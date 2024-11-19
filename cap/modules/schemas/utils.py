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
"""Utils for Schemas module."""

import re
from functools import wraps

from flask import abort, jsonify
from invenio_jsonschemas.errors import JSONSchemaNotFound
from jsonpatch import JsonPatchConflict

from .models import Schema
from .permissions import AdminSchemaPermission, ReadSchemaPermission


def is_later_version(version1, version2):
    matched1 = re.match(r"(\d+)\.(\d+)\.(\d+)", version1)
    matched2 = re.match(r"(\d+)\.(\d+)\.(\d+)", version2)

    if not matched1 or not matched2:
        raise ValueError(
            'Version has to be passed as string <major>.<minor>.<patch>'
        )

    major1, minor1, patch1 = matched1.groups()
    major2, minor2, patch2 = matched2.groups()

    if major1 > major2:
        return True
    elif major1 < major2:
        return False
    elif major1 == major2:
        if minor1 > minor2:
            return True
        elif minor1 < minor2:
            return False
        elif minor1 == minor2:
            if patch1 > patch2:
                return True
            elif patch1 < patch2:
                return False
            elif patch1 == patch2:
                return False


def check_allowed_patch_operation(data):
    """Return patch data after filtering in allowed operations."""
    ALLOWED_OPERATIONS = ['add', 'remove', 'replace']
    if not data or not isinstance(data, list):
        return None
    try:
        data = [
            operation
            for operation in data
            if operation.get('op', '') in ALLOWED_OPERATIONS
        ]
        return data
    except AttributeError:
        return None


def check_allowed_patch_path(data):
    """Raise JsonPatchConflict for patching non-editable fields."""
    EDITABLE_FIELDS = [
        'fullname',
        'use_deposit_as_record',
        'deposit_mapping',
        'record_mapping',
        'deposit_options',
        'record_options',
        'config',
    ]

    if not data:
        return data

    for operation in data:
        _field = operation.get('path', '')
        if re.match(r'^/', _field):
            _field = _field.split('/')
        else:
            raise JsonPatchConflict
        try:
            if _field[1] not in EDITABLE_FIELDS:
                raise JsonPatchConflict
        except IndexError:
            raise JsonPatchConflict
    return data


def actions_from_type(_type, perms):
    """
    Get user-made action names depending on the type.

    When the type is record or deposit, the user should also
    get schema-read access.
    """
    if _type == "record":
        return [f"record-schema-{perm}" for perm in perms]
    elif _type == "deposit":
        return [f"deposit-schema-{perm}" for perm in perms]
    elif _type == "schema":
        return [f"schema-object-{perm}" for perm in perms]


def get_default_mapping(name, version):
    default_mapping = {"mappings": {}}
    collection_mapping = {
        "properties": {
            "_collection": {
                "type": "object",
                "properties": {
                    "fullname": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "version": {"type": "keyword"},
                },
            }
        }
    }
    default_mapping["mappings"] = collection_mapping
    return default_mapping


def pass_schema(f):
    """Decorator to check if schema exists by name and/or version."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        name = kwargs.get('name')
        version = kwargs.get('version')

        if name:
            try:
                if version:
                    schema = Schema.get(name, version)
                else:
                    schema = Schema.get_latest(name)

                kwargs['schema'] = schema
            except JSONSchemaNotFound:
                return (
                    jsonify(
                        {
                            'message': 'Schema not found. Please try '
                            'again with existing schemas.'
                        }
                    ),
                    404,
                )
        return f(*args, **kwargs)

    return wrapper


def pass_schema_versions(f):
    """Decorator to return all schema by name."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        name = kwargs.get('name')

        if name:
            try:
                schemas = Schema.get_all_versions(name)
                kwargs['schemas'] = schemas
            except (JSONSchemaNotFound, IndexError):
                return (
                    jsonify(
                        {
                            'message': 'Schema not found. Please try '
                            'again with existing schemas.'
                        }
                    ),
                    404,
                )
        return f(*args, **kwargs)

    return wrapper


def schema_admin_permission(f):
    """Decorator to check if user has admin permission."""

    @wraps(f)
    def wrapper(
        self=None, name=None, version=None, schema=None, *args, **kwargs
    ):
        if not AdminSchemaPermission(schema).can():
            abort(403)
        return f(
            self=self,
            name=name,
            version=version,
            schema=schema,
            *args,
            **kwargs,
        )

    return wrapper


def schema_read_permission(f):
    """Decorator to check if user has read permission."""

    @wraps(f)
    def wrapper(
        self=None, name=None, version=None, schema=None, *args, **kwargs
    ):
        if not ReadSchemaPermission(schema).can():
            abort(403)
        return f(
            self=self,
            name=name,
            version=version,
            schema=schema,
            *args,
            **kwargs,
        )

    return wrapper
