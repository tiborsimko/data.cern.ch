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
"""Integration tests for searching records."""

from invenio_files_rest.models import ObjectVersion
from six import BytesIO

import json
import responses
from pytest import mark

from invenio_search import current_search
from invenio_files_rest.models import ObjectVersion

from cap.modules.repos.github_api import Github
from cap.modules.schemas.models import Schema


###########################################
# api/records/ [GET]
###########################################
def test_get_records_when_user_not_logged_in_returns_401(client, users, es):
    resp = client.get('/records/')

    assert resp.status_code == 401


def test_get_records_when_superuser_returns_all_records(
    client, users, auth_headers_for_user, auth_headers_for_superuser, create_deposit
):
    create_deposit(users['lhcb_user'], 'lhcb-v0.2.0')
    record = create_deposit(
        users['cms_user'], 'cms-analysis-v0.0.1', experiment='CMS', publish=True
    )

    resp = client.get('/records/', headers=auth_headers_for_superuser)

    found_pids = set(hit['id'] for hit in resp.json['hits']['hits'])

    assert resp.status_code == 200

    assert len(found_pids) == 1
    assert record['control_number'] in found_pids


def test_get_records_when_owner_can_see_his_record(
    client, db, users, auth_headers_for_user, auth_headers_for_superuser, create_deposit
):
    record = create_deposit(users['lhcb_user'], 'lhcb-v0.0.1', publish=True)

    resp = client.get('/records/', headers=auth_headers_for_user(users['lhcb_user']))

    found_pids = set(hit['id'] for hit in resp.json['hits']['hits'])

    assert resp.status_code == 200

    assert record['control_number'] in found_pids


def test_get_records_when_member_of_exp_can_see_all_experiments_records(
    client, db, users, auth_headers_for_user, auth_headers_for_superuser, create_deposit
):
    create_deposit(users['lhcb_user'], 'lhcb-v0.0.1', experiment='LHCb', publish=True)
    cms_records = [
        create_deposit(users['cms_user'], 'cms-v0.0.1', experiment='CMS', publish=True),
        create_deposit(
            users['cms_user2'], 'cms-v0.0.1', experiment='CMS', publish=True
        ),
    ]

    resp = client.get('/records/', headers=auth_headers_for_user(users['cms_user']))

    found_pids = set(hit['id'] for hit in resp.json['hits']['hits'])
    cms_deposits_pids = set(deposit['control_number'] for deposit in cms_records)

    assert resp.status_code == 200

    assert found_pids == cms_deposits_pids


def test_get_records_default_serializer(
    client, auth_headers_for_superuser, users, json_headers, create_deposit
):
    owner = users['cms_user2']
    deposit = create_deposit(
        owner,
        'cms-analysis',
        {
            '$schema': 'https://analysispreservation.cern.ch/schemas/deposits/records/cms-analysis-v1.0.0.json',
            'basic_info': {
                'analysis_number': 'dream_team',
            },
        },
        experiment='CMS',
        files={'file_1.txt': BytesIO(b'Hello world!')},
        publish=True,
    )
    recid = deposit['control_number']
    _, record = deposit.fetch_published()
    file = deposit.files['file_1.txt']
    metadata = record.get_record_metadata()

    resp = client.get('/records/', headers=auth_headers_for_superuser)

    assert resp.json['hits']['hits'][0] == {
        'id': record['control_number'],
        'type': 'record',
        'revision': 0,
        'experiment': 'CMS',
        'status': 'published',
        'schema': {'fullname': '', 'name': 'cms-analysis', 'version': '1.0.0'},
        'created_by': {'email': owner.email, 'profile': {}},
        'created': metadata.created.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'updated': metadata.updated.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'labels': [],
        'access': {
            'record-admin': {
                'roles': [],
                'users': [{'email': owner.email, 'profile': {}}],
            },
            'record-update': {
                'roles': [],
                'users': [{'email': owner.email, 'profile': {}}],
            },
            'record-read': {
                'roles': [],
                'users': [
                    {'email': owner.email, 'profile': {}},
                    {'email': users['cms_user2'].email, 'profile': {}},
                ],
            },
        },
        'metadata': {
            'basic_info': {
                'analysis_number': 'dream_team',
            }
        },
        # TOFIX shouldnt be deposit.files but record.files here!
        'files': [
            {
                'bucket': str(deposit.files.bucket),
                'checksum': file.file.checksum,
                'key': file.key,
                'size': file.file.size,
                'version_id': str(file.version_id),
                'file_id': str(file.file.id),
            }
        ],
        'is_owner': False,
        'links': {
            'bucket': 'http://analysispreservation.cern.ch/api/files/{}'.format(
                record.files.bucket
            ),
            'html': 'http://analysispreservation.cern.ch/published/{}'.format(recid),
            'self': 'http://analysispreservation.cern.ch/api/records/{}'.format(recid),
        },
        'draft_id': deposit.pid.pid_value,
    }


def test_get_records_with_correct_search_links(
    client, superuser, auth_headers_for_superuser, users, json_headers, create_deposit
):
    for i in range(11):
        deposit = create_deposit(
            superuser,
            'cms-analysis',
            {
                '$schema': 'https://analysispreservation.cern.ch/schemas/deposits/records/cms-analysis-v1.0.0.json',
                'basic_info': {
                    'analysis_number': 'dream_team',
                },
            },
            experiment='CMS',
            publish=True,
        )

    resp = client.get('/records/', headers=auth_headers_for_superuser)

    assert resp.status_code == 200
    assert resp.json['links'] == {
        'self': 'http://analysispreservation.cern.ch/api/records/?sort=mostrecent&size=10&page=1',
        'next': 'http://analysispreservation.cern.ch/api/records/?sort=mostrecent&size=10&page=2',
    }


@mark.skip
def test_get_records_with_correct_search_links_in_debug_mode(
    client,
    superuser,
    auth_headers_for_superuser,
    users,
    json_headers,
    create_deposit,
    app,
):
    app.config['DEBUG'] = True

    with app.test_client() as client:
        for i in range(11):
            create_deposit(
                superuser,
                'cms-analysis',
                {
                    '$schema': 'https://analysispreservation.cern.ch/schemas/deposits/records/cms-analysis-v1.0.0.json',
                    'basic_info': {
                        'analysis_number': 'dream_team',
                    },
                },
                experiment='CMS',
                publish=True,
            )

        resp = client.get('/records/', headers=auth_headers_for_superuser)

        assert resp.status_code == 200
        assert resp.json['links'] == {
            'self': 'http://analysispreservation.cern.ch/records/?page=1&sort=mostrecent&size=10',
            'next': 'http://analysispreservation.cern.ch/records/?page=2&sort=mostrecent&size=10',
        }


###########################################
# api/records/{pid} [GET]
###########################################
def test_get_record_when_user_not_logged_in_returns_401(client, users, create_deposit):
    deposit = create_deposit(users['lhcb_user'], 'lhcb-v0.0.1', publish=True)

    resp = client.get('/records/{}'.format(deposit['control_number']))

    assert resp.status_code == 401


def test_get_record_when_owner_returns_record(
    client, users, auth_headers_for_user, create_deposit
):
    owner = users['alice_user']
    record = create_deposit(
        owner, 'alice-analysis-v0.0.1', experiment='ALICE', publish=True
    )

    resp = client.get(
        '/records/{}'.format(record['control_number']),
        headers=auth_headers_for_user(owner),
    )

    assert resp.status_code == 200


def test_get_record_when_superuser_returns_record(
    client, db, users, auth_headers_for_user, auth_headers_for_superuser, create_deposit
):
    owner = users['cms_user']
    deposit = create_deposit(
        owner,
        'cms-analysis',
        {
            '$schema': 'https://analysispreservation.cern.ch/schemas/deposits/records/cms-analysis-v1.0.0.json',
            'basic_info': {
                'analysis_number': 'dream_team',
            },
        },
        experiment='CMS',
        files={'file_1.txt': BytesIO(b'Hello world!')},
        publish=True,
    )

    recid = deposit['control_number']
    _, record = deposit.fetch_published()
    file = record.files['file_1.txt']
    metadata = record.get_record_metadata()

    resp = client.get(
        '/records/{}'.format(deposit['control_number']),
        headers=[('Accept', 'application/json')] + auth_headers_for_user(owner),
    )

    assert resp.status_code == 200

    assert resp.json == {
        'id': recid,
        'type': 'record',
        'revision': 0,
        'experiment': 'CMS',
        'status': 'published',
        'schema': {'fullname': '', 'name': 'cms-analysis', 'version': '1.0.0'},
        'created_by': {'email': owner.email, 'profile': {}},
        'created': metadata.created.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'updated': metadata.updated.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'labels': [],
        'access': {
            'record-admin': {
                'roles': [],
                'users': [{'email': owner.email, 'profile': {}}],
            },
            'record-update': {
                'roles': [],
                'users': [{'email': owner.email, 'profile': {}}],
            },
            'record-read': {
                'roles': [],
                'users': [
                    {'email': users['cms_user'].email, 'profile': {}},
                    {'email': users['cms_user2'].email, 'profile': {}},
                ],
            },
        },
        'metadata': {'basic_info': {'analysis_number': 'dream_team'}},
        'files': [
            {
                'bucket': str(record.files.bucket),
                'checksum': file.file.checksum,
                'key': file.key,
                'size': file.file.size,
                'version_id': str(file.version_id),
                'mimetype': file.mimetype,
                'created': file.created.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
                'updated': file.updated.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
                'delete_marker': False,
                'is_head': True,
                'tags': {},
                'links': {
                    'self': f'http://analysispreservation.cern.ch/api/files/{str(file.bucket)}/file_1.txt',
                    'uploads': f'http://analysispreservation.cern.ch/api/files/{str(file.bucket)}/file_1.txt?uploads',
                    'version': f'http://analysispreservation.cern.ch/api/files/{str(file.bucket)}/file_1.txt?versionId={str(file.version_id)}',
                },
            }
        ],
        'is_owner': True,
        'links': {
            'bucket': 'http://analysispreservation.cern.ch/api/files/{}'.format(
                record.files.bucket
            ),
            'html': 'http://analysispreservation.cern.ch/published/{}'.format(recid),
            'self': 'http://analysispreservation.cern.ch/api/records/{}'.format(recid),
        },
        'draft_id': deposit.pid.pid_value,
    }


def test_get_record_when_other_member_of_collaboration_returns_record(
    client, users, auth_headers_for_user, create_deposit
):
    owner, other_user = users['alice_user'], users['alice_user2']
    deposit = create_deposit(
        owner, 'alice-analysis-v0.0.1', experiment='ALICE', publish=True
    )

    resp = client.get(
        '/records/{}'.format(deposit['control_number']),
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 200


def test_get_record_when_user_is_not_member_of_collaboration_returns_403(
    client, users, auth_headers_for_user, create_deposit
):
    deposit = create_deposit(
        users['alice_user'], 'alice-analysis-v0.0.1', experiment='ALICE', publish=True
    )

    resp = client.get(
        '/records/{}'.format(deposit['control_number']),
        headers=auth_headers_for_user(users['cms_user']),
    )

    assert resp.status_code == 403


def test_get_record_with_form_json_serializer(
    client, auth_headers_for_example_user, example_user, create_deposit, create_schema
):
    create_schema(
        'test-schema',
        experiment='CMS',
        fullname='Test Schema',
        deposit_schema={'title': 'deposit-test-schema'},
        deposit_options={'title': 'deposit-ui-test-schema'},
        record_schema={'title': 'record-test-schema'},
        record_options={'title': 'record-ui-test-schema'},
        use_deposit_as_record=False,
    )

    deposit = create_deposit(
        example_user,
        'test-schema',
        {'$ana_type': 'test-schema', 'my_field': 'mydata'},
        experiment='CMS',
        files={'readme': BytesIO(b'Hello!')},
        publish=True,
    )
    _, rec = deposit.fetch_published()
    file = rec.files['readme']

    pid = deposit['control_number']

    headers = auth_headers_for_example_user + [('Accept', 'application/form+json')]
    resp = client.get(f'/records/{pid}', headers=headers)

    assert resp.status_code == 200
    assert resp.json == {
        'access': {
            'record-admin': {
                'roles': [],
                'users': [{'email': example_user.email, 'profile': {}}],
            },
            'record-read': {
                'roles': [],
                'users': [
                    {'email': example_user.email, 'profile': {}},
                    {'email': 'cms_user2@cern.ch', 'profile': {}},
                ],
            },
            'record-update': {
                'roles': [],
                'users': [{'email': example_user.email, 'profile': {}}],
            },
        },
        'can_update': True,
        'is_owner': True,
        'can_review': False,
        'created': rec.created.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'updated': rec.updated.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
        'created_by': {'email': example_user.email, 'profile': {}},
        'experiment': rec['_experiment'],
        'draft_id': rec['_deposit']['id'],
        'id': pid,
        'files': [
            {
                'bucket': str(rec.files.bucket),
                'checksum': file.file.checksum,
                'key': file.key,
                'size': file.file.size,
                'version_id': str(file.version_id),
                'mimetype': file.mimetype,
                'created': file.created.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
                'updated': file.updated.strftime('%Y-%m-%dT%H:%M:%S.%f+00:00'),
                'delete_marker': False,
                'is_head': True,
                'tags': {},
                'links': {
                    'self': f'http://analysispreservation.cern.ch/api/files/{str(rec.files.bucket)}/readme',
                    'uploads': f'http://analysispreservation.cern.ch/api/files/{str(rec.files.bucket)}/readme?uploads',
                    'version': f'http://analysispreservation.cern.ch/api/files/{str(rec.files.bucket)}/readme?versionId={str(file.version_id)}',
                },
            }
        ],
        'links': {
            'bucket': f'http://analysispreservation.cern.ch/api/files/{str(rec.files.bucket)}',
            'html': f'http://analysispreservation.cern.ch/published/{pid}',
            'self': f'http://analysispreservation.cern.ch/api/records/{pid}',
        },
        'metadata': {'my_field': 'mydata'},
        'revision': 0,
        'status': 'published',
        'type': 'record',
        'labels': [],
        'schema': {
            'fullname': 'Test Schema',
            'name': 'test-schema',
            'version': '1.0.0',
        },
        'schemas': {
            'schema': {
                'title': 'record-test-schema',
            },
            'uiSchema': {
                'title': 'record-ui-test-schema',
            },
            'config_reviewable': False,
        },
    }


def test_get_record_with_form_json_serializer_check_other_user_can_update(
    client, users, auth_headers_for_user, create_deposit
):
    deposit = create_deposit(users['cms_user'], 'cms-analysis', experiment='CMS')

    other_user = users['cms_user2']
    permissions = [
        {
            'email': other_user.email,
            'type': 'user',
            'op': 'add',
            'action': 'deposit-read',
        },
        {
            'email': other_user.email,
            'type': 'user',
            'op': 'add',
            'action': 'deposit-update',
        },
    ]

    deposit.edit_permissions(permissions)
    deposit.publish()
    _, rec = deposit.fetch_published()

    pid = rec['control_number']
    headers = auth_headers_for_user(users['cms_user2']) + [
        ('Accept', 'application/form+json')
    ]
    resp = client.get(f'/records/{pid}', headers=headers)

    assert resp.status_code == 200
    assert resp.json['is_owner'] is False
    assert resp.json['can_update'] is True
    assert 'cms_user2@cern.ch' in [
        user['email'] for user in resp.json['access']['record-update']['users']
    ]


def test_get_record_with_form_json_serializer_check_other_user_can_admin(
    client, users, auth_headers_for_user, create_deposit
):
    deposit = create_deposit(users['cms_user'], 'cms-analysis', experiment='CMS')

    other_user = users['cms_user2']
    permissions = [
        {
            'email': other_user.email,
            'type': 'user',
            'op': 'add',
            'action': 'deposit-admin',
        }
    ]

    deposit.edit_permissions(permissions)
    deposit.publish()
    _, rec = deposit.fetch_published()

    pid = rec['control_number']
    headers = auth_headers_for_user(users['cms_user2']) + [
        ('Accept', 'application/form+json')
    ]
    resp = client.get(f'/records/{pid}', headers=headers)

    assert resp.status_code == 200
    assert resp.json['is_owner'] is False
    assert resp.json['can_update'] is True
    assert 'cms_user2@cern.ch' in [
        user['email'] for user in resp.json['access']['record-admin']['users']
    ]


def test_get_record_when_user_has_no_access_to_schema_can_still_see_record_that_got_access_to(
    client, users, auth_headers_for_user, deposit
):
    other_user = users['lhcb_user2']

    permissions = [
        {
            'email': other_user.email,
            'type': 'user',
            'op': 'add',
            'action': 'deposit-read',
        }
    ]
    deposit.edit_permissions(permissions)
    deposit.publish()
    pid = deposit['control_number']

    resp = client.get(
        f'/records/{pid}',
        headers=auth_headers_for_user(other_user)
        + [('Accept', 'application/form+json')],
    )

    assert resp.status_code == 200
