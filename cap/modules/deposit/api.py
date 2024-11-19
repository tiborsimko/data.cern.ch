# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016 CERN.
#
# CERN Analysis Preservation Framework is free software; you can redistribute
# it and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CERN Analysis Preservation Framework is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CERN Analysis Preservation Framework; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""Deposit API."""

import copy
import uuid
from functools import wraps

from flask import current_app, request
from flask_login import current_user
from invenio_access.models import ActionRoles, ActionUsers
from invenio_db import db
from invenio_deposit.api import Deposit, has_status, index, preserve
from invenio_deposit.utils import mark_as_action
from invenio_files_rest.errors import MultipartMissingParts
from invenio_files_rest.models import (
    Bucket,
    FileInstance,
    ObjectVersion,
    ObjectVersionTag,
)
from invenio_jsonschemas.errors import JSONSchemaNotFound
from invenio_jsonschemas.proxies import current_jsonschemas
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest.errors import InvalidDataRESTError
from invenio_rest.errors import FieldError
from jsonpatch import apply_patch
from jsonschema.exceptions import RefResolutionError, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.local import LocalProxy

from cap.modules.deposit.egroups import CERNEgroupMixin
from cap.modules.deposit.errors import (
    DepositValidationError,
    DisconnectWebhookError,
    FileUploadError,
    ReviewError,
    UniqueRequiredValidationError,
    UpdateDepositPermissionsError,
)
from cap.modules.deposit.fetchers import cap_deposit_fetcher
from cap.modules.deposit.loaders import get_val_from_path
from cap.modules.deposit.minters import cap_deposit_minter
from cap.modules.deposit.permissions import (
    AdminDepositPermission,
    CloneDepositPermission,
    DepositAdminActionNeed,
    DepositReadActionNeed,
    DepositUpdateActionNeed,
    ReviewDepositPermission,
    UpdateDepositPermission,
)
from cap.modules.deposit.review import Reviewable
from cap.modules.deposit.utils import perform_copying_fields
from cap.modules.deposit.validators import (
    NoRequiredValidator,
    get_custom_validator,
)
from cap.modules.experiments.permissions import exp_need_factory
from cap.modules.records.api import CAPRecord
from cap.modules.records.errors import get_error_path
from cap.modules.repos.errors import GitError, GitHostNotSupported
from cap.modules.repos.integrator import (
    attach_repo_to_deposit,
    create_repo_as_user_and_attach,
    create_schema_default_repo_and_attach,
)
from cap.modules.repos.utils import disconnect_subscriber
from cap.modules.schemas.resolvers import (
    resolve_schema_by_url,
    schema_name_to_url,
)
from cap.modules.user.errors import DoesNotExistInLDAP
from cap.modules.user.utils import (
    get_existing_or_register_role,
    get_existing_or_register_user,
)

_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)

PRESERVE_FIELDS = (
    "_deposit",
    "_buckets",
    "_files",
    "_review",
    "_egroups",
    "_experiment",
    "_access",
    "_user_edited",
    "_fetched_from",
    "control_number",
    "general_title",
    "$schema",
)

DEPOSIT_ACTIONS = (
    "deposit-read",
    "deposit-update",
    "deposit-admin",
)


def DEPOSIT_ACTIONS_NEEDS(id):
    """Method to construct action needs."""
    return {
        "deposit-read": DepositReadActionNeed(str(id)),
        "deposit-update": DepositUpdateActionNeed(str(id)),
        "deposit-admin": DepositAdminActionNeed(str(id)),
    }


EMPTY_ACCESS_OBJECT = {
    action: {"users": [], "roles": []} for action in DEPOSIT_ACTIONS
}


class CAPDeposit(Deposit, Reviewable, CERNEgroupMixin):
    """Define API for changing deposit state."""

    deposit_fetcher = staticmethod(cap_deposit_fetcher)

    deposit_minter = staticmethod(cap_deposit_minter)

    published_record_class = CAPRecord

    @property
    def schema(self):
        """Schema property."""
        return resolve_schema_by_url(self["$schema"])

    @property
    def record_schema(self):
        """Get corresponding schema path for record."""
        return current_jsonschemas.path_to_url(self.schema.record_path)

    def build_deposit_schema(self, record):
        """Get schema path for deposit."""
        return current_jsonschemas.path_to_url(self.schema.deposit_path)

    def pop_from_data(method, fields=None):
        """Remove fields from deposit data.

        :param fields: List of fields to remove (default: ``('_deposit',)``).
        """
        fields = fields or (
            "_deposit",
            "_access",
            "_experiment",
            "_fetched_from",
            "_user_edited",
            "general_title",
            "$schema",
        )

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            """Check current deposit status."""
            for field in fields:
                if field in args[0]:
                    args[0].pop(field)

            return method(self, *args, **kwargs)

        return wrapper

    def pop_from_data_patch(method, fields=None):
        """Remove fields from deposit data.

        :param fields: List of fields to remove (default: ``('_deposit',)``).
        """
        fields = fields or (
            "/_deposit",
            "/_access",
            "/_files",
            "/_experiment",
            "/_fetched_from",
            "/_user_edited",
            "/$schema",
        )

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            """Check current deposit status."""
            for field in fields:
                for k, patch in enumerate(args[0]):
                    if field == patch.get("path", None):
                        del args[0][k]

            return method(self, *args, **kwargs)

        return wrapper

    @mark_as_action
    def permissions(self, pid=None):
        """Permissions action.

        We expect an array of objects:
        [{
        "email": "",
        "type": "user|egroup",
        "op": "add|remove",
        "action": "deposit-read|deposit-update|deposit-admin"
        }]
        """
        with AdminDepositPermission(self).require(403):
            data = request.get_json()
            if data is None:
                raise InvalidDataRESTError()

            return self.edit_permissions(data)

    def _publish_edited(self):
        record = super(CAPDeposit, self)._publish_edited()
        record._add_deposit_permissions(record, record.id)

        if record["_experiment"]:
            record._add_experiment_permissions(record, record.id)

        return record

    @mark_as_action
    def publish(self, *args, **kwargs):
        """Simple file check before publishing."""
        with AdminDepositPermission(self).require(403):
            # check if all deposit files has been uploaded
            for file_ in self.files:
                if file_.data["checksum"] is None:
                    raise MultipartMissingParts()

            try:
                return super(CAPDeposit, self).publish(*args, **kwargs)
            except ValidationError as e:
                raise DepositValidationError(e.message)

    @has_status
    @mark_as_action
    def upload(self, pid, *args, **kwargs):
        """Upload action for repositories.

        Can upload a repository or its single file and/or create a webhook.
        Expects json with params:
        * `url`: the git url, can point to repo or specific file
        * `webhook`: the webhook type to be applied, can be null to just `attach` the repo  # noqa
        """
        with UpdateDepositPermission(self).require(403):
            try:
                _, rec = request.view_args.get("pid_value").data
                data = request.get_json()
                if data is None:
                    raise InvalidDataRESTError()

                record_uuid = str(rec.id)

                # For backward compatibility
                # if no 'type' passed, pass 'repo_download_attach' as default
                action_type = data.get("type", "repo_download_attach")
            except Exception:
                raise FileUploadError("Invalid arguments. Please try again.")

            actions = {
                "repo_create": create_repo_as_user_and_attach,
                "repo_download_attach": attach_repo_to_deposit,
                "repo_create_default": create_schema_default_repo_and_attach,
            }

            try:
                actions[action_type](record_uuid, data)
            except KeyError:
                raise FileUploadError(
                    "Unsupported repository action. "
                    "Try create, attach or collab."
                )
            except GitHostNotSupported:
                raise FileUploadError("Host isn't provided or not supported")
            except GitError as err:
                raise FileUploadError(err.message)

        return self

    @has_status
    @mark_as_action
    def disconnect_webhook(self, pid, *args, **kwargs):
        """Disconnect webhook for repostiories.

        Expects json with subscriber id as a param:
        """
        with UpdateDepositPermission(self).require(403):
            data = request.get_json()
            sub_id = data.get("subscriber_id")
            if sub_id is None:
                raise DisconnectWebhookError("Missing subscriber_id parameter")

            try:
                disconnect_subscriber(sub_id)
            except NoResultFound:
                raise DisconnectWebhookError(
                    "This webhook was not registered with analysis."
                )

            return self

    @index
    @mark_as_action
    def clone(self, pid=None, id_=None):
        """Clone a deposit.

        Adds snapshot of the files when deposit is cloned.
        """
        with CloneDepositPermission(self).require(403):
            data = copy.deepcopy(self.dumps())
            # control number exist only in case of a published draft(record)
            if data:
                data.pop("_deposit", None)
                data.pop("control_number", None)
            deposit = super(CAPDeposit, self).create(data, id_=id_)
            deposit["_deposit"]["cloned_from"] = {
                "type": pid.pid_type,
                "value": pid.pid_value,
                "revision_id": self.revision_id,
            }
            bucket = self.files.bucket.snapshot()
            RecordsBuckets.create(record=deposit.model, bucket=bucket)
            # optionally we might need to do: deposit.files.flush()
            deposit.commit()
            return deposit

    @index
    @mark_as_action
    def review(self, pid, *args, **kwargs):
        """Review actions for a deposit.

        Adds review and comments for a deposit.
        """
        with ReviewDepositPermission(self).require(403):
            if self.schema_is_reviewable():
                data = request.get_json()
                if data is None:
                    raise InvalidDataRESTError()

                if data.get("id"):
                    self.update_review(data)
                else:
                    self.create_review(data)
            else:
                raise ReviewError(None)

            self.commit()

            return self

    def _prepare_edit(self, record):
        """Update selected keys for edit method.

        Override method from `invenio_deposit.api:Deposit` class.
        Copy deposit metadata instead of record metadata.

        :param record: The published record.
        """
        data = self.dumps()

        # Keep current record revision for merging.
        data["_deposit"]["pid"]["revision_id"] = record.revision_id
        data["_deposit"]["status"] = "draft"

        return data

    @mark_as_action
    def edit(self, *args, **kwargs):
        """Edit deposit."""
        with UpdateDepositPermission(self).require(403):
            self = super(CAPDeposit, self).edit(*args, **kwargs)

            # unlock the bucket, so files can be added/updated/deleted
            # when user tries to edit file required by published record
            # new version will be created
            self.files.bucket.locked = False
            db.session.commit()

            return self

    @pop_from_data
    def update(self, data, *args, **kwargs):
        """Update deposit."""
        with UpdateDepositPermission(self).require(403):
            schema = {"$ref": self["$schema"]}
            validated_data = None

            # 1. Maybe check if should continue with action
            # 2. Maybe merge for more customized
            validated_data = self.validation(schema, data)
            data = validated_data if validated_data else data

            super(CAPDeposit, self).update(data, *args, **kwargs)

    @pop_from_data_patch
    def patch(self, *args, **kwargs):
        """Patch deposit."""
        with UpdateDepositPermission(self).require(403):
            schema = {"$ref": self["$schema"]}

            patch = copy.deepcopy(request.get_json(force=True))

            patched_data = apply_patch(self.model.json, patch)

            self.validation(schema, patched_data)
            return super(CAPDeposit, self).patch(*args, **kwargs)

    def validation(self_or_cls, schema, data_to_validate, **kwargs):
        """Validation function to validate the data.

        Validates the data in order provided in schema configuration.
        """
        current_data = None
        if hasattr(self_or_cls, 'model'):
            current_data = self_or_cls.model.json
        data_to_validate = self_or_cls.check_data(
            schema=schema,
            current_data=current_data,
            submitted_data=data_to_validate,
        )

        return data_to_validate

    def edit_permissions(self, data):
        """Edit deposit permissions.

        We expect an array of objects:
        [{
        "email": "",
        "type": "user|egroup",
        "op": "add|remove",
        "action": "deposit-read|deposit-update|deposit-admin"
        }]

        """
        with db.session.begin_nested():
            for obj in data:
                if obj["type"] == "user":
                    try:
                        user = get_existing_or_register_user(obj["email"])
                    except DoesNotExistInLDAP:
                        raise UpdateDepositPermissionsError(
                            "User with this mail does not exist in LDAP."
                        )

                    if obj["op"] == "add":
                        try:
                            self._add_user_permissions(
                                user, [obj["action"]], db.session
                            )
                        except IntegrityError:
                            raise UpdateDepositPermissionsError(
                                "Permission already exist."
                            )

                    elif obj["op"] == "remove":
                        try:
                            self._remove_user_permissions(
                                user, [obj["action"]], db.session
                            )
                        except NoResultFound:
                            raise UpdateDepositPermissionsError(
                                "Permission does not exist."
                            )

                elif obj["type"] == "egroup":
                    try:
                        role = get_existing_or_register_role(obj["email"])
                    except DoesNotExistInLDAP:
                        raise UpdateDepositPermissionsError(
                            "Egroup with this mail does not exist in LDAP."
                        )

                    if obj["op"] == "add":
                        try:
                            self._add_egroup_permissions(
                                role, [obj["action"]], db.session
                            )
                        except IntegrityError:
                            raise UpdateDepositPermissionsError(
                                "Permission already exist."
                            )
                    elif obj["op"] == "remove":
                        try:
                            self._remove_egroup_permissions(
                                role, [obj["action"]], db.session
                            )
                        except NoResultFound:
                            raise UpdateDepositPermissionsError(
                                "Permission does not exist."
                            )

        self.commit()

        return self

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def clear(self, *args, **kwargs):
        """Clear only drafts."""
        super(CAPDeposit, self).clear(*args, **kwargs)

    def is_published(self):
        """Check if deposit is published."""
        return self["_deposit"].get("pid") is not None

    def get_record_metadata(self):
        """Get Record Metadata instance for deposit."""
        return RecordMetadata.query.filter_by(id=self.id).one_or_none()

    def commit(self, *args, **kwargs):
        """Synchronize files before commit."""
        self.files.flush()

        # mark as manually edited
        if current_user:
            self["_user_edited"] = True

        return super(CAPDeposit, self).commit(*args, **kwargs)

    def _add_user_permissions(self, user, permissions, session):
        """Adds permissions for user for this deposit."""
        for permission in permissions:
            session.add(
                ActionUsers.allow(
                    DEPOSIT_ACTIONS_NEEDS(self.id)[permission], user=user
                )
            )

            session.flush()

            self["_access"][permission]["users"].append(user.id)

    def _remove_user_permissions(self, user, permissions, session):
        """Remove permissions for user for this deposit."""
        for permission in permissions:
            session.delete(
                ActionUsers.query.filter(
                    ActionUsers.action == permission,
                    ActionUsers.argument == str(self.id),
                    ActionUsers.user_id == user.id,
                ).one()
            )
            session.flush()

            self["_access"][permission]["users"].remove(user.id)

    def _add_egroup_permissions(self, egroup, permissions, session):
        for permission in permissions:
            session.add(
                ActionRoles.allow(
                    DEPOSIT_ACTIONS_NEEDS(self.id)[permission], role=egroup
                )
            )
            session.flush()

            if egroup.id not in self["_access"][permission]["roles"]:
                self["_access"][permission]["roles"].append(egroup.id)

    def _remove_egroup_permissions(self, egroup, permissions, session):
        for permission in permissions:
            session.delete(
                ActionRoles.query.filter(
                    ActionRoles.action == permission,
                    ActionRoles.argument == str(self.id),
                    ActionRoles.role_id == egroup.id,
                ).one()
            )
            session.flush()

            self["_access"][permission]["roles"].remove(egroup.id)

    def _add_experiment_permissions(self, experiment, permissions):
        """Add read permissions to everybody assigned to experiment."""
        exp_need = exp_need_factory(experiment)

        # give read access to members of collaboration
        with db.session.begin_nested():
            for au in ActionUsers.query_by_action(exp_need).all():
                self._add_user_permissions(au.user, permissions, db.session)
            for ar in ActionRoles.query_by_action(exp_need).all():
                self._add_egroup_permissions(ar.role, permissions, db.session)

    def _set_experiment(self):
        schema = resolve_schema_by_url(self["$schema"])
        self["_experiment"] = schema.experiment

    def _create_buckets(self):
        bucket = Bucket.create()
        RecordsBuckets.create(record=self.model, bucket=bucket)

    def validate(self, **kwargs):
        """Validate data using schema with ``JSONResolver``."""
        if "$schema" in self and self["$schema"]:
            try:
                schema = self["$schema"]
                if not isinstance(schema, dict):
                    schema = {"$ref": schema}
                resolver = current_app.extensions[
                    "invenio-records"
                ].ref_resolver_cls.from_schema(schema)

                validator = NoRequiredValidator(schema, resolver=resolver)

                errors = []
                for err in validator.iter_errors(self):
                    if (
                        err.__class__ is UniqueRequiredValidationError
                        and self["_deposit"]["id"] in err.uuids
                    ):
                        pass
                    else:
                        errors.append(
                            FieldError(get_error_path(err), str(err.message))
                        )

                if errors:
                    raise DepositValidationError(None, errors=errors)
            except RefResolutionError:
                raise DepositValidationError(
                    "Schema {} not found.".format(self["$schema"])
                )
        else:
            raise DepositValidationError("You need to provide a valid schema.")

    def save_file(self, content, filename, size, failed=False):
        """Save file with given content in deposit bucket.

        If downloading a content failed, file will be still created,
        with tag `failed`.

        :param content: stream
        :param filename: name that file will be saved with
        :param size: size of content
        :param failed: if failed during downloading the content
        """
        obj = ObjectVersion.create(bucket=self.files.bucket, key=filename)
        obj.file = FileInstance.create()
        self.files.flush()

        if not failed:
            self.files[filename].file.set_contents(
                content,
                default_location=self.files.bucket.location.uri,
                size=size,
            )

            print("File {} saved ({}b).\n".format(filename, size))
        else:
            ObjectVersionTag.create(
                object_version=obj, key="status", value="failed"
            )
            print("File {} not saved.\n".format(filename))

        self.files.flush()
        db.session.commit()

        return obj

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Get record instance."""
        deposit = super(CAPDeposit, cls).get_record(
            id_=id_, with_deleted=with_deleted
        )
        deposit["_files"] = deposit.files.dumps()
        return deposit

    @classmethod
    @index
    def create(cls, data, id_=None, owner=current_user):
        """Create a new deposit.

        :param data: metadata, need to contain $schema|$ana_type field
        :type data: dict
        :param id_: specify a UUID to use for the new record, instead of
                    automatically generated
        :type id_: `uuid.UUID`
        :param owner: owner of a new deposit (will get all permissions)
        :type owner: `invenio_accounts.models.User`

        :warn: if user session owner will be automatically current_user

        :return: newly created deposit
        :rtype: `CAPDeposit`

        Process:
        * fill deposit metadata based on given data
        * initialize the follow internal fields (underscore prefixed):
            _experiment: 'experiment_of_given_schema'
            _deposit: {
                'id': pid_value,
                'status': 'draft',
                'owners': [owner_id],
                'created_by': owner_id
            }
            _access: {
                'deposit-admin': {
                    'roles': [],
                    'users': [owner.id]
                },
                'deposit-update': {
                    'roles': [],
                    'users': [owner.id]
                },
                'deposit-read': {
                    'roles': [],
                    'users': [owner.id]
                }
            }
        * validate metadata against given schema (defined by $schema|$ana_type)
        * create RecordMetadata instance
        * create bucket for storing deposit files
        * set owner permissions in the db
        * index deposit in opensearch
        """
        if current_user and current_user.is_authenticated:
            owner = current_user

        with db.session.begin_nested():
            uuid_ = id_ or uuid.uuid4()

            data = cls._preprocess_create_data(data, uuid_, owner)

            # create RecordMetadata instance
            deposit = Record.create(
                data, id_=uuid_, validator=NoRequiredValidator
            )
            deposit.__class__ = cls

            # create files bucket
            bucket = Bucket.create()
            RecordsBuckets.create(record=deposit.model, bucket=bucket)
            # give owner permissions to the deposit
            if owner:
                for permission in DEPOSIT_ACTIONS:
                    db.session.add(
                        ActionUsers.allow(
                            DEPOSIT_ACTIONS_NEEDS(deposit.id)[permission],
                            user=owner,
                        )
                    )

                    db.session.flush()

            return deposit

    @classmethod
    def _preprocess_create_data(cls, data, uuid_, owner):
        """Preprocess metadata for new deposit.

        :param data: metadata, need to contain $schema|$ana_type field
        :type data: dict
        :param id_: specify a UUID to use for the new record, instead of
                    automatically generated
        :type id_: `uuid.UUID`
        :param owner: owner of a new deposit (will get all permissions)
        :type owner: `invenio_accounts.models.User`

        :returns: processed metadata dictionary
        :rtype: dict
        """
        if not isinstance(data, dict) or data == {}:
            raise DepositValidationError("Empty deposit data.")

        if "$ana_type" in data:
            try:
                ana_type = data.pop("$ana_type")
                data["$schema"] = schema_name_to_url(ana_type)
            except JSONSchemaNotFound:
                raise DepositValidationError(
                    f"Schema {ana_type} is not a valid deposit schema."
                )
        elif "$schema" not in data:
            raise DepositValidationError("Schema not specified.")

        try:
            schema = resolve_schema_by_url(data["$schema"])
            data["_experiment"] = schema.experiment
        except JSONSchemaNotFound:
            raise DepositValidationError(
                f'Schema {data["$schema"]} is not a valid deposit schema.'
            )
        _schema = {"$ref": data["$schema"]}

        cls.validation(cls, _schema, data)

        # minting is done by invenio on POST action preprocessing,
        # if method called programatically mint PID here
        if "_deposit" not in data:
            cls.deposit_minter(uuid_, data, schema=schema)

        if owner:
            data["_deposit"]["owners"] = [owner.id]
            data["_deposit"]["created_by"] = owner.id
            data["_access"] = {
                permission: {"users": [owner.id], "roles": []}
                for permission in DEPOSIT_ACTIONS
            }
        else:
            data["_deposit"]["owners"] = []
            data["_access"] = copy.deepcopy(EMPTY_ACCESS_OBJECT)

        return data

    @classmethod
    def check_data(
        cls, schema=None, current_data=None, submitted_data=None, **kwargs
    ):
        if not any([schema, submitted_data]):
            return

        validator = get_custom_validator(schema, **kwargs)
        errors = []
        data = submitted_data
        ordered_list = []

        error_list = [e for e in validator.iter_errors(submitted_data)]
        for err in error_list:
            _validator = err.validator
            if _validator in CUSTOM_POST_VALIDATORS:
                _validator_value = err.validator_value
                _order = (
                    _validator_value["x-cap-order"]
                    if "x-cap-order" in _validator_value
                    else 9999
                )
                ordered_list.append((_order, err))

        ordered_list.sort(key=lambda x: x[0])
        for field in ordered_list:
            err = field[1]
            _method = CUSTOM_POST_VALIDATORS[err.validator]
            _error, data = _method(err, current_data, data)
            if _error:
                errors.append(FieldError(get_error_path(err), str(err.message)))

        if errors:
            raise DepositValidationError(
                "You cannot edit this field.", errors=errors
            )

        return data


def has_changed(error, current, new):
    error_path = get_error_path(error)
    current_version = get_val_from_path(current, error_path) or None
    new_version = get_val_from_path(new, error_path)

    if not new_version:
        new_version = current_version
    if current_version != new_version:

        return True, current
    else:
        return False, new


def copy_to_fields(error, current, new):
    data = error.instance
    paths = error.validator_value.get("path")
    perform_copying_fields(new, data, paths)
    return False, new


CUSTOM_POST_VALIDATORS = {
    "x-cap-copy": copy_to_fields,
    "x-cap-copyto": copy_to_fields,
    "x-cap-permission": has_changed,
}
