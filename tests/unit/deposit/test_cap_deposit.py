# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2017 CERN.
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
# or submit itself to any jurisdiction.
"""Unit tests for Cap Deposit class."""

from uuid import uuid4

from flask_security import login_user
from invenio_access.models import ActionRoles, ActionUsers
from unittest.mock import patch
from pytest import mark, raises
from sqlalchemy.exc import IntegrityError

from cap.modules.deposit.api import CAPDeposit as Deposit
from cap.modules.deposit.errors import DepositValidationError
from cap.modules.deposit.serializers.schemas.json import DepositFormSchema
from conftest import _datastore


def test_create_deposit_with_empty_data_raises_DepositValidationError(
    app, users, location):
    metadata = {}

    with app.test_request_context():
        login_user(users['superuser'])
        id_ = uuid4()

        with raises(DepositValidationError):
            Deposit.create(metadata, id_=id_)


def test_create_deposit_with_empty_schema_raises_DepositValidationError(
    app, users, location):
    metadata = {'$schema': ''}

    with app.test_request_context():
        login_user(users['superuser'])
        id_ = uuid4()

        with raises(DepositValidationError):
            Deposit.create(metadata, id_=id_)


def test_create_deposit_with_wrong_schema_raises_DepositValidationError(
    app, users, location):
    metadata = {
        '$schema': 'https://analysispreservation.cern.ch/schemas/deposits/records/non-existing-schema.json'  # noqa
    }

    with app.test_request_context():
        login_user(users['superuser'])
        id_ = uuid4()

        with raises(DepositValidationError):
            Deposit.create(metadata, id_=id_)


def test_add_and_remove_user_permissions_set_access_object_properly_and_updates_actions_in_the_db(
    app, db, users, create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'alice-analysis-v0.0.1')

    assert deposit['_access'] == {
        'deposit-read': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-update': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-admin': {
            'users': [owner.id],
            'roles': []
        }
    }
    assert not ActionUsers.query.filter_by(
        action='deposit-read',
        argument=str(deposit.id),
        user_id=other_user.id,
    ).all()

    deposit._add_user_permissions(
        other_user,
        ['deposit-read', 'deposit-update'],
        db.session,
    )

    assert deposit['_access'] == {
        'deposit-read': {
            'users': [owner.id, other_user.id],
            'roles': []
        },
        'deposit-update': {
            'users': [owner.id, other_user.id],
            'roles': []
        },
        'deposit-admin': {
            'users': [owner.id],
            'roles': []
        }
    }
    assert ActionUsers.query.filter_by(
        action='deposit-read',
        argument=str(deposit.id),
        user_id=other_user.id,
    ).one()

    deposit._remove_user_permissions(
        other_user,
        ['deposit-read', 'deposit-update'],
        db.session,
    )
    assert deposit['_access'] == {
        'deposit-read': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-update': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-admin': {
            'users': [owner.id],
            'roles': []
        }
    }
    assert not ActionUsers.query.filter_by(
        action='deposit-read',
        argument=str(deposit.id),
        user_id=other_user.id,
    ).all()


def test_add_and_remove_egroup_permissions_set_access_object_properly_and_updates_actions_in_the_db(
    app, db, users, create_deposit):
    owner = users['cms_user']
    egroup = _datastore.find_or_create_role('my-egroup@cern.ch')
    deposit = create_deposit(owner, 'alice-analysis-v0.0.1')

    assert deposit['_access'] == {
        'deposit-read': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-update': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-admin': {
            'users': [owner.id],
            'roles': []
        }
    }
    assert not ActionRoles.query.filter_by(
        action='deposit-read',
        argument=str(deposit.id),
        role_id=egroup.id,
    ).all()

    deposit._add_egroup_permissions(
        egroup,
        ['deposit-read', 'deposit-update'],
        db.session,
    )

    assert deposit['_access'] == {
        'deposit-read': {
            'users': [owner.id],
            'roles': [egroup.id]
        },
        'deposit-update': {
            'users': [owner.id],
            'roles': [egroup.id]
        },
        'deposit-admin': {
            'users': [owner.id],
            'roles': []
        }
    }
    assert ActionRoles.query.filter_by(
        action='deposit-read',
        argument=str(deposit.id),
        role_id=egroup.id,
    ).one()

    deposit._remove_egroup_permissions(
        egroup,
        ['deposit-read', 'deposit-update'],
        db.session,
    )

    assert deposit['_access'] == {
        'deposit-read': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-update': {
            'users': [owner.id],
            'roles': []
        },
        'deposit-admin': {
            'users': [owner.id],
            'roles': []
        }
    }
    assert not ActionRoles.query.filter_by(
        action='deposit-read',
        argument=str(deposit.id),
        role_id=egroup.id,
    ).all()


def test_create_deposit_check_if_reviewable(users, create_schema, create_deposit):
    owner = users['cms_user']
    schema_reviewable = create_schema(
        'review-schema',
        experiment='CMS',
        config={
          'reviewable': True
        })

    schema_not_reviewable = create_schema('non-review-schema', experiment='CMS')

    deposit_reviewable = create_deposit(owner, 'review-schema', experiment='CMS')
    deposit_not_reviewable = create_deposit(owner, 'non-review-schema', experiment='CMS')

    assert deposit_reviewable.schema_is_reviewable()
    assert not deposit_not_reviewable.schema_is_reviewable()


@mark.parametrize(
    "permission_info, schema, expected",
    [
        (
            [
                {"path": ["properties", "title"], "value": {"users": ["test@test.com"]}},
                {"path": ["properties", "date"], "value": {"users": ["test_user@test.com"]}},
                {
                    "path": ["properties", "test", "items", "properties", "title"],
                    "value": {"users": ["test@test.com"]},
                },
                {
                    "path": ["properties", "test", "items", "properties", "date"],
                    "value": {"users": ["test_user@test.com"]},
                },
            ],
            {
                "title": "deposit-test-schema",
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "x-cap-permission": {"users": ["test@test.com"]},
                    },
                    "date": {
                        "type": "string",
                        "x-cap-permission": {"users": ["test_user@test.com"]},
                    },
                    "test": {
                        "type": "array",
                        "items": {
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "x-cap-permission": {"users": ["test@test.com"]},
                                },
                                "date": {
                                    "type": "string",
                                    "x-cap-permission": {
                                        "users": ["test_user@test.com"]
                                    },
                                },
                            },
                            "type": "object",
                        },
                    },
                },
            },
            {
                "title": "deposit-test-schema",
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "x-cap-permission": {"users": ["test@test.com"]},
                        "readOnly": True,
                    },
                    "date": {
                        "type": "string",
                        "x-cap-permission": {"users": ["test_user@test.com"]},
                        "readOnly": True,
                    },
                    "test": {
                        "type": "array",
                        "items": {
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "x-cap-permission": {"users": ["test@test.com"]},
                                    "readOnly": True,
                                },
                                "date": {
                                    "type": "string",
                                    "x-cap-permission": {
                                        "users": ["test_user@test.com"]
                                    },
                                    "readOnly": True,
                                },
                            },
                            "type": "object",
                        },
                    },
                },
            },
        ),
        (
            [{'path': [], 'value': {'users': ['test@test.com']}}],
            {
                "title": "deposit-test-schema",
                "type": "object",
                "x-cap-permission": {"users": ["test@test.com"]},
            },
            {
                "title": "deposit-test-schema",
                "type": "object",
                "x-cap-permission": {"users": ["test@test.com"]},
                "readOnly": True,
            },
        ),
        (
            [
                {"path": ["items", "properties", "title"], "value": {"users": ["test@test.com"]}},
                {
                    "path": ["items", "properties", "date"],
                    "value": {"users": ["test_user@test.com"]},
                },
            ],
            {
                "title": "deposit-test-schema-one",
                "type": "array",
                "items": {
                    "properties": {
                        "title": {
                            "type": "string",
                            "x-cap-permission": {"users": ["test@test.com"]},
                        },
                        "date": {
                            "type": "string",
                            "x-cap-permission": {"users": ["test_user@test.com"]},
                        },
                    },
                    "type": "object",
                },
            },
            {
                "title": "deposit-test-schema-one",
                "type": "array",
                "items": {
                    "properties": {
                        "title": {
                            "type": "string",
                            "x-cap-permission": {"users": ["test@test.com"]},
                            "readOnly": True,
                        },
                        "date": {
                            "type": "string",
                            "x-cap-permission": {"users": ["test_user@test.com"]},
                            "readOnly": True,
                        },
                    },
                    "type": "object",
                },
            },
        ),
        (
            [{'path': ['items'], 'value': {'users': ['test@test.com']}}],
            {
                "title": "deposit-test-schema-one",
                "type": "array",
                "items": {
                    "type": "string",
                    "x-cap-permission": {"users": ["test@test.com"]},
                },
            },
            {
                "title": "deposit-test-schema-one",
                "type": "array",
                "items": {
                    "type": "string",
                    "x-cap-permission": {"users": ["test@test.com"]},
                    "readOnly": True,
                },
            },
        ),
        (
            [{'path': [], 'value': {'users': ['test_user@test.com']}}],
            {
                "title": "deposit-test-schema-two",
                "type": "string",
                "x-cap-permission": {"users": ["test_user@test.com"]},
            },
            {
                "title": "deposit-test-schema-two",
                "type": "string",
                "x-cap-permission": {"users": ["test_user@test.com"]},
                "readOnly": True,
            },
        ),
        (
            [
                {
                    "path": [
                        "properties",
                        "basic_info",
                        "properties",
                        "status",
                        "properties",
                        "main_status",
                    ],
                    "value": {"users": ["test_user@test.com"]},
                },
                {
                    "path": ["properties", "basic_info", "properties", "analysis_people"],
                    "value": {"users": ["test_user@test.com"]},
                },
                {"path": [], "value": {"users": ["test_user@test.com"]}},
            ],
            {
                "title": "deposit-test-schema-two",
                "type": "object",
                "properties": {
                    "basic_info": {
                        "properties": {
                            "status": {
                                "properties": {
                                    "main_status": {
                                        "type": "string",
                                        "x-cap-permission": {
                                            "users": ["test_user@test.com"]
                                        },
                                    }
                                }
                            },
                            "analysis_people": {
                                "x-cap-permission": {"users": ["test_user@test.com"]},
                                "items": {"type": "string"},
                            },
                        }
                    }
                },
                "x-cap-permission": {"users": ["test_user@test.com"]},
            },
            {
                "title": "deposit-test-schema-two",
                "type": "object",
                "x-cap-permission": {"users": ["test_user@test.com"]},
                "properties": {
                    "basic_info": {
                        "properties": {
                            "status": {
                                "properties": {
                                    "main_status": {
                                        "type": "string",
                                        "x-cap-permission": {
                                            "users": ["test_user@test.com"]
                                        },
                                        "readOnly": True,
                                    }
                                }
                            },
                            "analysis_people": {
                                "x-cap-permission": {"users": ["test_user@test.com"]},
                                "items": {"type": "string"},
                                "readOnly": True,
                            },
                        }
                    }
                },
                "readOnly": True,
            },
        ),
        (
            [
                {
                    "path": ["dependencies", "object", "oneOf", 0, "properties", "object"],
                    "value": {"users": ["test_user@test.com"]},
                },
                {
                    "path": ["dependencies", "object", "oneOf", 0, "properties", "electron_type"],
                    "value": {"users": ["test_user@test.com"]},
                },
                {
                    "path": ["dependencies", "object", "oneOf", 1, "properties", "muon_type"],
                    "value": {"users": ["test_user@test.com"]},
                },
                {
                    "path": [
                        "properties",
                        "basic_info",
                        "properties",
                        "status",
                        "properties",
                        "main_status",
                    ],
                    "value": {"users": ["test_user@test.com"]},
                },
                {
                    "path": ["properties", "basic_info", "properties", "analysis_people"],
                    "value": {"users": ["test_user@test.com"]},
                },
                {"path": [], "value": {"users": ["test_user@test.com"]}},
            ],
            {
                "title": "deposit-test-schema-fs",
                "additionalProperties": True,
                "type": "object",
                "dependencies": {
                    "object": {
                        "oneOf": [
                            {
                                "properties": {
                                    "object": {
                                        "enum": ["electron"],
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                    },
                                    "electron_type": {
                                        "enum": ["GsfElectron"],
                                        "type": "string",
                                        "title": "Electron type",
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                    },
                                }
                            },
                            {
                                "properties": {
                                    "object": {"enum": ["muon"]},
                                    "muon_type": {
                                        "enum": ["PFMuon", "GlobalMuon", "TrackerMuon"],
                                        "type": "string",
                                        "title": "Muon type",
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                    },
                                }
                            },
                        ]
                    }
                },
                "properties": {
                    "basic_info": {
                        "properties": {
                            "status": {
                                "properties": {
                                    "main_status": {
                                        "type": "string",
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                    }
                                }
                            },
                            "analysis_people": {
                                "x-cap-permission": {"users": ["test_user@test.com"]},
                                "items": {"type": "string"},
                            },
                        }
                    }
                },
                "x-cap-permission": {"users": ["test_user@test.com"]},
            },
            {
                "title": "deposit-test-schema-fs",
                "additionalProperties": True,
                "type": "object",
                "dependencies": {
                    "object": {
                        "oneOf": [
                            {
                                "properties": {
                                    "object": {
                                        "enum": ["electron"],
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                        "readOnly": True,
                                    },
                                    "electron_type": {
                                        "enum": ["GsfElectron"],
                                        "type": "string",
                                        "title": "Electron type",
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                        "readOnly": True,
                                    },
                                }
                            },
                            {
                                "properties": {
                                    "object": {"enum": ["muon"]},
                                    "muon_type": {
                                        "enum": ["PFMuon", "GlobalMuon", "TrackerMuon"],
                                        "type": "string",
                                        "title": "Muon type",
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                        "readOnly": True,
                                    },
                                }
                            },
                        ]
                    }
                },
                "properties": {
                    "basic_info": {
                        "properties": {
                            "status": {
                                "properties": {
                                    "main_status": {
                                        "type": "string",
                                        "x-cap-permission": {"users": ["test_user@test.com"]},
                                        "readOnly": True,
                                    }
                                }
                            },
                            "analysis_people": {
                                "x-cap-permission": {"users": ["test_user@test.com"]},
                                "items": {"type": "string"},
                                "readOnly": True,
                            },
                        }
                    }
                },
                "x-cap-permission": {"users": ["test_user@test.com"]},
                "readOnly": True,
            }

        )
    ],
)
@patch(
    "cap.modules.deposit.serializers.schemas.json.DepositFormSchema.can_user_edit_field",
    return_value=True,
)
def test_get_read_only_status(
    mock_can_user_edit_field, permission_info, schema, expected
):
    test_class = DepositFormSchema()
    result = test_class.get_read_only_status(permission_info, schema)
    assert result == expected
