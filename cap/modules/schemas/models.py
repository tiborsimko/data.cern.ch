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
"""Models for schemas."""

import re
from datetime import datetime

from flask import current_app
from invenio_access.models import ActionRoles, ActionSystemRoles, ActionUsers
from invenio_access.permissions import authenticated_user
from invenio_accounts.models import Role
from invenio_cache import current_cache
from invenio_db import db
from invenio_jsonschemas.errors import JSONSchemaNotFound
from invenio_rest.errors import FieldError
from invenio_search import current_search
from invenio_search import current_search_client as es
from jsonschema import Draft7Validator
from six.moves.urllib.parse import urljoin
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import import_string

from cap.modules.records.errors import get_error_path
from cap.modules.user.errors import DoesNotExistInLDAP
from cap.modules.user.utils import (
    get_existing_or_register_role,
    get_existing_or_register_user,
    get_remote_account_by_id,
)
from cap.types import json_type

from .access import (
    _allow_role,
    _allow_user,
    _deny_role,
    _deny_user,
    _remove_role,
    _remove_user,
)
from .helpers import ValidationError
from .jsonschemas import SCHEMA_CONFIG_JSONSCHEMA_V1
from .permissions import SchemaAdminAction, SchemaReadAction
from .serializers import (
    config_resolved_schemas_serializer,
    patched_schema_serializer,
    resolved_schemas_serializer,
    schema_serializer,
)

ES_FORBIDDEN = r' ,"\<*>|?'

# map attributes when use_deposit_as_record flag on
SERVE_DEPOSIT_AS_RECORD_MAP = {
    'record_schema': 'deposit_schema',
    'record_mapping': 'deposit_mapping',
    'record_options': 'deposit_options',
}


class Schema(db.Model):
    """Model defining analysis JSON schemas."""

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(128), unique=False, nullable=False)
    fullname = db.Column(db.String(128), unique=False, nullable=True)

    # version
    major = db.Column(db.Integer, unique=False, nullable=False, default=1)
    minor = db.Column(db.Integer, unique=False, nullable=False, default=0)
    patch = db.Column(db.Integer, unique=False, nullable=False, default=0)

    experiment = db.Column(db.String(128), unique=False, nullable=True)
    config = db.Column(json_type, default=lambda: dict(), nullable=False)

    deposit_schema = db.Column(json_type, default=lambda: dict(), nullable=True)

    deposit_options = db.Column(
        json_type, default=lambda: dict(), nullable=True
    )

    deposit_mapping = db.Column(
        json_type, default=lambda: dict(), nullable=True
    )

    record_schema = db.Column(json_type, default=lambda: dict(), nullable=True)

    record_options = db.Column(json_type, default=lambda: dict(), nullable=True)

    record_mapping = db.Column(json_type, default=lambda: dict(), nullable=True)

    use_deposit_as_record = db.Column(
        db.Boolean(create_constraint=False), unique=False, default=False
    )
    is_indexed = db.Column(
        db.Boolean(create_constraint=False), unique=False, default=False
    )

    created = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)
    updated = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    __tablename__ = 'schema'
    __table_args__ = (
        UniqueConstraint(
            'name', 'major', 'minor', 'patch', name='unique_schema_version'
        ),
    )

    def __init__(self, *args, **kwargs):
        """Possible to set version from string."""
        version = kwargs.pop('version', None)
        if version:
            self.version = version

        # TODO: maybe add generator for dafault mapping if doesnt exist
        super(Schema, self).__init__(*args, **kwargs)

    def __getattribute__(self, attr):
        """Map record attribute to deposit one, if use_deposit_as_record is True."""  # noqa
        if (
            attr in SERVE_DEPOSIT_AS_RECORD_MAP.keys()
            and self.use_deposit_as_record
        ):
            attr = SERVE_DEPOSIT_AS_RECORD_MAP.get(attr)

        return object.__getattribute__(self, attr)

    def __str__(self):
        """Stringify schema object."""
        return '{name}-v{version}'.format(name=self.name, version=self.version)

    @property
    def version(self):
        """Return stringified version."""
        return "{0}.{1}.{2}".format(self.major, self.minor, self.patch)

    @version.setter
    def version(self, string):
        """Set version."""
        matched = re.match(r"(\d+)\.(\d+)\.(\d+)", string)
        if matched is None:
            raise ValueError(
                'Version has to be passed as string <major>.<minor>.<patch>'
            )

        self.major, self.minor, self.patch = matched.groups()

    @property
    def deposit_path(self):
        """Return deposit schema path."""
        prefix = current_app.config['SCHEMAS_DEPOSIT_PREFIX']
        path = urljoin(prefix, "{0}.json".format(self))
        return path

    @property
    def record_path(self):
        """Return record schema path."""
        prefix = current_app.config['SCHEMAS_RECORD_PREFIX']
        path = urljoin(prefix, "{0}.json".format(self))
        return path

    @property
    def deposit_index(self):
        """Get deposit index name."""
        path = urljoin(current_app.config['SCHEMAS_DEPOSIT_PREFIX'], str(self))
        return name_to_es_name(path)

    @property
    def record_index(self):
        """Get record index name."""
        path = urljoin(current_app.config['SCHEMAS_RECORD_PREFIX'], str(self))
        return name_to_es_name(path)

    @property
    def deposit_aliases(self):
        """Get ES deposits aliases."""
        name = name_to_es_name(self.name)
        return ['deposits', 'deposits-records', 'deposits-{}'.format(name)]

    @property
    def record_aliases(self):
        """Get ES records aliases."""
        name = name_to_es_name(self.name)
        return ['records', 'records-{}'.format(name)]

    @validates('name')
    def validate_name(self, key, name):
        """Validate if name is ES compatible."""
        if any(x in ES_FORBIDDEN for x in name):
            raise ValueError(
                'Name cannot contain the following characters'
                '[, ", *, \\, <, | , , , > , ?]'
            )
        return name

    @validates('config')
    def validate_config(self, key, value):
        """Validate the config."""
        if value:
            validator = Draft7Validator(SCHEMA_CONFIG_JSONSCHEMA_V1)
            errors = []

            for error in validator.iter_errors(value):
                errors.append(
                    FieldError(
                        get_error_path(error), str(error.message)
                    ).to_dict()
                )

            if errors:
                raise ValidationError(
                    errors=errors,
                    description="Schema configuration validation error",
                )
        return value

    def serialize(self, resolve=False):
        """Serialize schema model."""
        serializer = (
            resolved_schemas_serializer if resolve else schema_serializer
        )  # noqa
        return serializer.dump(self).data

    def config_serialize(self):
        """Serialize config schema model."""
        return config_resolved_schemas_serializer.dump(self).data

    def patch_serialize(self):
        """Serialize schema for patching schema."""
        return patched_schema_serializer.dump(self).data

    def update(self, **kwargs):
        """Update schema instance."""
        for key, value in kwargs.items():
            setattr(self, key, value)

        return self

    def add_read_access_for_all_users(self):
        """Give read access to all authenticated users."""
        assert self.id

        db.session.add(
            ActionSystemRoles.allow(
                SchemaReadAction(self.id), role=authenticated_user
            )
        )
        db.session.flush()

    def modify_record_permissions(
        self, permissions, record_type="deposit", schema_action="allow"
    ):
        allowed_actions = current_app.extensions['invenio-access'].actions
        # TODO add serializer for payload

        actions_roles = []
        actions_users = []
        for permission_type in permissions.keys():
            action_name = f"{record_type}-schema-{permission_type}"
            if action_name not in allowed_actions:
                continue
            for user in permissions[permission_type].get("users", []):
                actions_users.append([action_name, user])
            for role in permissions[permission_type].get("roles", []):
                actions_roles.append([action_name, role])

        permissions_roles_log = self.process_action_roles(
            schema_action, actions_roles
        )
        permissions_users_log = self.process_action_users(
            schema_action, actions_users
        )

        return permissions_roles_log + permissions_users_log

    def process_action_roles(self, schema_action, actions_roles):
        """Permission process action.

        The schema_argument can be either a schema name
        or a schema id.
        """
        allowed_actions = current_app.extensions["invenio-access"].actions
        schema_actions = {
            "allow": _allow_role,
            "deny": _deny_role,
            "remove": _remove_role,
        }
        processor = schema_actions[schema_action]
        # check for kind of action, in order to use the correct argument
        # schema actions need id, deposit/record actions need name
        permission_logs = []
        for _action, _role in actions_roles:
            try:
                with db.session.begin_nested():
                    role = get_existing_or_register_role(_role)
                    db.session.flush()
                    role_id = role.id
                    schema_argument = str(self.id)
                    processor(
                        allowed_actions[_action], schema_argument, role_id
                    )
                db.session.commit()
                permission_logs.append(
                    {
                        "action": _action,
                        "role": role.name,
                        "status": schema_action,
                    }
                )
            except (DoesNotExistInLDAP, IntegrityError) as err:
                message = ""
                if isinstance(err, DoesNotExistInLDAP):
                    message = "Doesn't exist in CERN database"
                elif isinstance(err, IntegrityError):
                    message = "Already exists"
                permission_logs.append(
                    {
                        "action": _action,
                        "role": _role,
                        "status": "error",
                        "message": message,
                    }
                )
                continue

        return permission_logs

    def process_action_users(self, schema_action, actions_users):
        """
        Permission process action.

        The schema_argument can be either a schema name
        or a schema id.
        """
        allowed_actions = current_app.extensions["invenio-access"].actions
        schema_actions = {
            "allow": _allow_user,
            "deny": _deny_user,
            "remove": _remove_user,
        }
        processor = schema_actions[schema_action]
        # check for kind of action, in order to use the correct argument
        # schema actions need id, deposit/record actions need name
        permission_logs = []
        for _action, _user in actions_users:
            try:
                with db.session.begin_nested():
                    user = get_existing_or_register_user(_user)
                    db.session.flush()
                    user_id = user.id
                    schema_argument = str(self.id)
                    processor(
                        allowed_actions[_action], schema_argument, user_id
                    )
                db.session.commit()
                permission_logs.append(
                    {
                        "action": _action,
                        "user": user.email,
                        "status": schema_action,
                    }
                )
            except (DoesNotExistInLDAP, IntegrityError) as err:
                message = ""
                if isinstance(err, DoesNotExistInLDAP):
                    message = "Doesn't exist in CERN database"
                elif isinstance(err, IntegrityError):
                    message = "Already exists"
                permission_logs.append(
                    {
                        "action": _action,
                        "role": _user,
                        "status": "error",
                        "message": message,
                    }
                )
                continue
        return permission_logs

    def give_admin_access_for_user(self, user):
        """Give admin access for users."""
        assert self.id

        db.session.add(ActionUsers.allow(SchemaAdminAction(self.id), user=user))
        db.session.flush()

    def get_schema_permissions(self):
        """Retrieve permissions from 'Schema.config'."""
        action_roles = ActionRoles.query.filter(
            ActionRoles.argument == str(self.id),
            ActionRoles.action.like("%-schema-%"),
        ).all()

        action_users = ActionUsers.query.filter(
            ActionUsers.argument == str(self.id),
            ActionUsers.action.like("%-schema-%"),
        ).all()

        permissions = {}
        for ar in action_roles:
            if ar.action not in permissions:
                permissions[ar.action] = {"roles": [], "users": []}
            permissions[ar.action]["roles"].append(ar.role.name)
        for au in action_users:
            if au.action not in permissions:
                permissions[au.action] = {"roles": [], "users": []}
            permissions[au.action]["users"].append(
                get_remote_account_by_id(au.user.id)
            )

        return permissions

    @classmethod
    def get_latest(cls, name):
        """Get the latest version of schema with given name."""
        latest = (
            cls.query.filter_by(name=name)
            .order_by(cls.major.desc(), cls.minor.desc(), cls.patch.desc())
            .first()
        )

        if latest:
            return latest
        else:
            raise JSONSchemaNotFound(schema=name)

    @classmethod
    def get_all_versions(cls, name):
        """Get all versions of schema with given name."""
        schemas = (
            cls.query.filter_by(name=name)
            .order_by(cls.major.desc(), cls.minor.desc(), cls.patch.desc())
            .all()
        )
        if schemas:
            return schemas
        else:
            raise JSONSchemaNotFound(schema=name)

    def get_versions(self):
        """Get the latest version of schema with given name."""
        schemas = self.query.filter_by(name=self.name).all()
        if schemas:
            return [s.version for s in schemas]
        else:
            raise JSONSchemaNotFound(schema=self.name)

    @classmethod
    def get(cls, name, version):
        """Get schema by name and version."""
        matched = re.match(r"(\d+).(\d+).(\d+)", version)
        if matched is None:
            raise ValueError(
                'Version has to be passed as string <major>.<minor>.<patch>'
            )

        major, minor, patch = matched.groups()

        try:
            schema = cls.query.filter_by(
                name=name, major=major, minor=minor, patch=patch
            ).one()

        except NoResultFound:
            raise JSONSchemaNotFound("{}-v{}".format(name, version))

        return schema


def name_to_es_name(name):
    r"""Translate name to ES compatible name.

    Replace '/' with '-'.
    [, ", *, \\, <, | , , , > , ?] are forbidden.
    """
    if any(x in ES_FORBIDDEN for x in name):
        raise AssertionError(
            'Name cannot contain the following characters'
            '[, ", *, \\, <, | , , , > , ?]'
        )

    return name.replace('/', '-')


def create_index(index_name, mapping_body, aliases):
    """Create index in opensearch, add under given aliases."""
    if not es.indices.exists(index_name):
        current_search.mappings[index_name] = {}  # invenio search needs it

        es.indices.create(index=index_name, body=mapping_body, ignore=False)

        for alias in aliases:
            es.indices.update_aliases(
                {'actions': [{'add': {'index': index_name, 'alias': alias}}]}
            )


def add_permissions_from_schema(permissions, name):
    """Add permissions found in the schema's config."""
    access_actions = current_app.extensions['invenio-access'].actions
    try:
        for action in permissions.keys():
            roles = permissions[action]

            for role in roles:
                _action = access_actions[action]
                _role = Role.query.filter_by(name=role).first()
                _permission = ActionRoles.allow(
                    _action, argument=name, role_id=_role.id
                )

                db.session.add(_permission)
    except IntegrityError:
        db.session.rollback()


@event.listens_for(Schema, 'after_insert')
def after_insert_schema(target, value, schema):
    """On schema insert, create corresponding indexes and aliases in ES."""
    if schema.is_indexed:
        create_index(
            schema.deposit_index, schema.deposit_mapping, schema.deposit_aliases
        )
        create_index(
            schema.record_index, schema.record_mapping, schema.record_aliases
        )

        # invenio search needs it
        mappings_imp = current_app.config.get('SEARCH_GET_MAPPINGS_IMP')
        current_cache.delete_memoized(import_string(mappings_imp))


@event.listens_for(Schema, 'after_delete')
def before_delete_schema(mapper, connect, schema):
    """On schema delete, delete corresponding indexes and aliases in ES."""
    if schema.is_indexed:
        for index in (schema.record_index, schema.deposit_index):
            if es.indices.exists(index):
                es.indices.delete(index)

            # invenio search needs it
            mappings_imp = current_app.config.get('SEARCH_GET_MAPPINGS_IMP')
            current_cache.delete_memoized(import_string(mappings_imp))


@db.event.listens_for(Schema, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Update `updated` property with current time on `before_update` event."""
    target.updated = datetime.utcnow()


def create_indices():
    schemas = Schema.query.all()
    for schema in schemas:
        if schema.is_indexed:
            create_index(
                schema.deposit_index,
                schema.deposit_mapping,
                schema.deposit_aliases,
            )
            create_index(
                schema.record_index,
                schema.record_mapping,
                schema.record_aliases,
            )

            # invenio search needs it
            mappings_imp = current_app.config.get('SEARCH_GET_MAPPINGS_IMP')
            current_cache.delete_memoized(import_string(mappings_imp))


# def recreate_index_schemas():
#     # 1. Get all indexed schemas
#     # 2. Delete index to update
#     # 3. Create index for update
#     schemas = (
#         Schema.query.filter_by(is_indexed=True)
#         .order_by(
#             Schema.name, Schema.major.desc(),
#             Schema.minor.desc(), Schema.patch.desc()
#         )
#         .all()
#     )
#     for schema in schemas:
#         if schema.is_indexed:
#             # for index in (schema.record_index, schema.deposit_index):
#             create_index(
#                 schema.deposit_index,
#                 generate_mapping(schema.deposit_index,
#                                  mapping=schema.deposit_mapping),
#                 schema.deposit_aliases,
#             )
#             create_index(
#                 schema.record_index,
#                 generate_mapping(schema.record_index,
#                                  mapping=schema.record_mapping),
#                 schema.record_aliases,
#             )

#             # invenio search needs it
#             mappings_imp = current_app.config.get("SEARCH_GET_MAPPINGS_IMP")
#             current_cache.delete_memoized(import_string(mappings_imp))


# def generate_mapping(name, mapping={}, settings={}):
#     if not name:
#         raise Exception("No name passed for mapping")

#     default_mapping = {
#         "settings": {
#             "analysis": {
#                 "analyzer": {
#                     "lowercase_whitespace_analyzer": {
#                         "type": "custom",
#                         "tokenizer": "whitespace",
#                         "filter": ["lowercase"],
#                     }
#                 }
#             }
#         },
#         "mappings": {
#             name: {
#                 "_all": {"enabled": True,
#                          "analyzer": "lowercase_whitespace_analyzer"},
#                 "properties": {
#                     "_deposit": {
#                         "type": "object",
#                         "properties": {
#                             "created_by": {
#                                   "type": "integer",
#                                   "copy_to": "created_by"},
#                             "status": {
#                                 "type": "text",
#                                 "fields": {"keyword": {"type": "keyword"}},
#                                 "copy_to": "status",
#                             },
#                         },
#                     },
#                     "_collection": {
#                         "type": "object",
#                         "properties": {
#                             "fullname": {"type": "keyword"},
#                             "name": {"type": "keyword"},
#                             "version": {"type": "keyword"},
#                         },
#                     },
#                     "_experiment": {"type": "text"},
#                     "_fetched_from": {
#                         "type": "text",
#                         "analyzer": "lowercase_whitespace_analyzer",
#                         "copy_to": "fetched_from",
#                     },
#                     "_user_edited": {"type": "boolean",
#                                      "copy_to": "user_edited"},
#                     "_created": {"type": "date", "copy_to": "created"},
#                     "_updated": {"type": "date", "copy_to": "updated"},
#                 },
#             }
#         },
#     }

#     try:
#         default_mapping["settings"] = {
#             **default_mapping["settings"],
#             **settings
#         }
#         default_mapping["mappings"][name]["properties"] = {
#             **default_mapping["mappings"][name]["properties"],
#             **mapping
#         }
#     except:
#         pass
#     return default_mapping
