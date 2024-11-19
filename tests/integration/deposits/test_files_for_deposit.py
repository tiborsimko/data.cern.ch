# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2007 CERN.
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
"""Integration tests for files methods for deposits."""

import json

from flask import current_app
from pytest import mark
from six import BytesIO

from cap.modules.deposit.api import CAPDeposit

#########################################
# api/deposits/{pid}/files [GET]
#########################################
def test_deposit_files_when_owner_can_see_files_list(client, users,
                                                     auth_headers_for_user,
                                                     create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']

    resp = client.get('/deposits/{}/files'.format(pid),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 200


def test_deposit_files_when_superuser_can_see_files_list(
        client, users, auth_headers_for_superuser, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']

    resp = client.get('/deposits/{}/files'.format(pid),
                      headers=auth_headers_for_superuser)

    assert resp.status_code == 200


def test_deposit_files_when_other_user_returns_403(client, users,
                                                   auth_headers_for_user,
                                                   create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']

    resp = client.get('/deposits/{}/files'.format(pid),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 403


@mark.parametrize("action", [
    ("deposit-read"),
    ("deposit-admin"),
])
def test_deposit_files_when_user_has_read_or_admin_permission_can_see_files_list(
        action, client, users, auth_headers_for_user, json_headers,
        create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': action
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.get('/deposits/{}/files'.format(pid),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 200


def test_deposit_files_when_no_files_returns_empty_list(
        client, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']

    resp = client.get('/deposits/{}/files'.format(pid),
                      headers=auth_headers_for_user(owner))
    assert json.loads(resp.data) == []


def test_deposit_files_returns_list_with_files_info(client, users,
                                                    auth_headers_for_user,
                                                    create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    deposit.files['file_2.txt'] = BytesIO(b'Hello brave new world!')
    pid = deposit['_deposit']['id']

    resp = client.get('/deposits/{}/files'.format(pid),
                      headers=auth_headers_for_user(owner))

    files = resp.json

    assert files[0]["filename"] == 'file_1.txt'
    assert files[0]["filesize"] == 12

    assert files[1]["filename"] == 'file_2.txt'
    assert files[1]["filesize"] == 22


#########################################
# api/files/{bucket_id} [GET]
#########################################
def test_bucket_read_when_nonexisting_bucket_returns_404(
        client, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')

    resp = client.get('/files/nonexistingbucketid',
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 404


def test_bucket_read_when_owner_of_deposit_can_access(client, users,
                                                      auth_headers_for_user,
                                                      create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}'.format(bucket),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 200


def test_bucket_read_when_superuser_can_access(client, users,
                                               auth_headers_for_superuser,
                                               create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}'.format(bucket),
                      headers=auth_headers_for_superuser)

    assert resp.status_code == 200


def test_bucket_read_when_other_user_returns_404(client, users,
                                                 auth_headers_for_user,
                                                 create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}'.format(bucket),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 404


@mark.parametrize("action", [
    ("deposit-read"),
    ("deposit-update"),
    ("deposit-admin"),
])
def test_bucket_read_when_user_has_read_update_or_admin_access_can_access(
        action, client, users, auth_headers_for_user, create_deposit,
        json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': action
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.get('/files/{}'.format(bucket),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 200


#########################################
# api/files/{bucket_id}/{filekey} [GET]
#########################################
def test_file_read_when_given_nonexisting_filekey_returns_404(
        client, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}/non-existing.txt'.format(bucket),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 404


def test_file_read_when_owner_of_deposit_can_access_file(
        client, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}/file_1.txt'.format(bucket),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 200


def test_file_read_when_superuser_can_access_file(client, users,
                                                  auth_headers_for_superuser,
                                                  create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}/file_1.txt'.format(bucket),
                      headers=auth_headers_for_superuser)

    assert resp.status_code == 200


def test_file_read_when_other_user_returns_404(client, users,
                                               auth_headers_for_user,
                                               create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.get('/files/{}/file_1.txt'.format(bucket),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 404


@mark.parametrize("action", [
    ("deposit-read"),
    ("deposit-update"),
    ("deposit-admin"),
])
def test_file_read_when_user_has_read_update_or_admin_access_can_access(
        action, client, users, auth_headers_for_user, create_deposit,
        json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': action
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.get('/files/{}/file_1.txt'.format(bucket),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 200


def test_bucket_links(client, users, auth_headers_for_superuser, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.get(f'/files/{bucket}', headers=auth_headers_for_superuser)

    assert resp.status_code == 200
    assert resp.json['links'] == {
        'self': f'http://analysispreservation.cern.ch/api/files/{bucket}',
        'uploads': f'http://analysispreservation.cern.ch/api/files/{bucket}?uploads',
        'versions': f'http://analysispreservation.cern.ch/api/files/{bucket}?versions'
    }


def test_bucket_links_with_files(client, users, auth_headers_for_superuser, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket
    version = deposit['_files'][0]['version_id']

    resp = client.get(f'/files/{bucket}', headers=auth_headers_for_superuser)

    assert resp.status_code == 200
    assert 'contents' in resp.json
    assert resp.json['contents'][0]['links'] == {
        'self': f'http://analysispreservation.cern.ch/api/files/{bucket}/file_1.txt',
        'uploads': f'http://analysispreservation.cern.ch/api/files/{bucket}/file_1.txt?uploads',
        'version': f'http://analysispreservation.cern.ch/api/files/{bucket}/file_1.txt?versionId={version}'
    }


def test_bucket_links_with_versioned_files(client, users, auth_headers_for_superuser, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world! Second time!')
    bucket = deposit.files.bucket

    resp = client.get(f'/files/{bucket}?versions', headers=auth_headers_for_superuser)

    assert resp.status_code == 200
    assert 'contents' in resp.json
    assert len(resp.json['contents']) == 2
    assert resp.json['contents'][0]['key'] == resp.json['contents'][1]['key']


def test_bucket_links_with_versioned_files_get_versions_separately(
        client, users, auth_headers_for_superuser, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world! Second time!')
    bucket = deposit.files.bucket

    resp = client.get(f'/files/{bucket}?versions', headers=auth_headers_for_superuser)
    assert resp.status_code == 200
    assert 'contents' in resp.json
    assert len(resp.json['contents']) == 2

    version_id_first = resp.json['contents'][1]['version_id']
    version_id_second = resp.json['contents'][0]['version_id']

    # get contents of 1st version
    resp = client.get(f'/files/{bucket}/file_1.txt?versionId={version_id_first}',
                      headers=auth_headers_for_superuser)
    assert resp.data == b'Hello world!'

    # get contents of 1st version
    resp = client.get(f'/files/{bucket}/file_1.txt?versionId={version_id_second}',
                      headers=auth_headers_for_superuser)
    assert resp.data == b'Hello world! Second time!'


#########################################
# api/files/{bucket_id}/{filekey} [PUT]
#########################################
@mark.skip('This should be possible? or we solve problem from UI/client side')
def test_file_upload_when_key_already_exists_returns_400(
        client, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.put('/files/{}/file_1.txt'.format(bucket),
                      input_stream=BytesIO(b'Hello world!'),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 400


def test_file_upload_when_owner_of_deposit_can_upload(client, users,
                                                      auth_headers_for_user,
                                                      create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.put('/files/{}/file_1.txt'.format(bucket),
                      input_stream=BytesIO(b'Hello world!'),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 200


def test_file_upload_when_superuser_can_upload(client, users,
                                               auth_headers_for_superuser,
                                               create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.put('/files/{}/file_1.txt'.format(bucket),
                      input_stream=BytesIO(b'Hello world!'),
                      headers=auth_headers_for_superuser)

    assert resp.status_code == 200


def test_file_upload_when_other_user_returns_404(client, users,
                                                 auth_headers_for_user,
                                                 create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.put('/files/{}/file_1.txt'.format(bucket),
                      input_stream=BytesIO(b'Hello world!'),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 404


@mark.parametrize("action", [
    ("deposit-update"),
    ("deposit-admin"),
])
def test_file_upload_when_user_has_update_or_admin_access_can_upload(
        action, client, users, auth_headers_for_user, create_deposit,
        json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': action
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.put('/files/{}/file_1.txt'.format(bucket),
                      input_stream=BytesIO(b'Hello world!'),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 200


def test_file_upload_when_user_has_only_read_access_returns_404(
        client, users, auth_headers_for_user, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': 'deposit-read'
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.put('/files/{}/file_1.txt'.format(bucket),
                      input_stream=BytesIO(b'Hello world!'),
                      headers=auth_headers_for_user(other_user))

    assert resp.status_code == 404


def test_file_upload_uploads_successfully(client, users, auth_headers_for_user,
                                          create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    client.put('/files/{}/file_1.txt'.format(bucket),
               input_stream=BytesIO(b'Hello world!'),
               headers=auth_headers_for_user(owner))

    resp = client.get('/files/{}/file_1.txt'.format(bucket),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 200
    assert resp.data == b'Hello world!'


def test_put_header_tags(client, users, auth_headers_for_user, create_deposit):
    """Test upload of an object with tags in the headers."""
    key = 'test.txt'
    headers = [
        (current_app.config['FILES_REST_FILE_TAGS_HEADER'],
         'key1=val1&key2=val2&key3=val3'),
    ]

    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.put(
        '/files/{}/{}'.format(bucket, key),
        input_stream=BytesIO(b'updated_content'),
        headers=headers + auth_headers_for_user(owner),
    )

    assert resp.status_code == 200

    resp = client.get(
        '/files/{}'.format(bucket),
        headers=auth_headers_for_user(owner),
    )

    tags = resp.json.get('contents', [{}])[0].get('tags', {})

    assert tags['key1'] == 'val1'
    assert tags['key2'] == 'val2'
    assert tags['key3'] == 'val3'


def test_put_header_invalid_tags(client, users, auth_headers_for_user,
                                 create_deposit):
    """Test upload of an object with tags in the headers."""
    key = 'test.txt'
    header_name = current_app.config['FILES_REST_FILE_TAGS_HEADER']
    invalid = [
        # We don't test zero-length values/keys, because they are filtered out
        # from parse_qsl
        ('a' * 256, 'valid'),
        ('valid', 'b' * 256),
    ]

    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    # Invalid key or values
    for k, v in invalid:
        resp = client.put('/files/{}/{}'.format(bucket, key),
                          input_stream=BytesIO(b'updated_content'),
                          headers=[(header_name, '{}={}'.format(k, v))] +
                          auth_headers_for_user(owner))

        assert resp.status_code == 400

    # Duplicate key
    resp = client.put('/files/{}/{}'.format(bucket, key),
                      input_stream=BytesIO(b'updated_content'),
                      headers=[(header_name, 'a=1&a=2')] +
                      auth_headers_for_user(owner))

    assert resp.status_code == 400


def test_bucket_locked_status(client, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    headers = auth_headers_for_user(owner)
    deposit = create_deposit(owner, 'test', experiment='CMS')
    depid = deposit['_deposit']['id']
    deposit_bucket = deposit.files.bucket
    assert deposit_bucket.locked is False

    # Upload file
    client.put('/files/{}/file_1.txt'.format(deposit_bucket),
                input_stream=BytesIO(b'Hello world!'),
                headers=headers)

    client.post('/deposits/{}/actions/publish'.format(depid), headers=headers)
    assert deposit_bucket.locked is True

    deposit = CAPDeposit.get_record(deposit.id)
    assert deposit.files.bucket.locked == True

    _, record = deposit.fetch_published()
    record_bucket = record.files.bucket
    assert record_bucket.locked == True
    resp_put = client.put('/files/{}/file_2.txt'.format(record_bucket),
                      input_stream=BytesIO(b'Hello brave new world!'),
                      headers=headers)
    assert resp_put.status_code == 403

    # check the record contains different bucket
    assert deposit_bucket != record_bucket

    # check the content of record_bucket matched the get record `files` response
    resp = client.get('/records/{}'.format(record['control_number']),
                      headers=auth_headers_for_user(owner))

    rec_files = resp.json.get('files')
    assert len(rec_files) == len(record_bucket.objects)

    # Check the response object has same metadata as the bucket
    assert rec_files[0].get('key') == record_bucket.objects[0].key
    assert rec_files[0].get('version_id') == str(record_bucket.objects[0].version_id)
    assert rec_files[0].get('mimetype') == record_bucket.objects[0].mimetype
    assert rec_files[0].get('size') == record_bucket.objects[0].file.size
    assert rec_files[0].get('checksum') == record_bucket.objects[0].file.checksum


#########################################
# api/files/{bucket_id}/{filekey} [DELETE]
#########################################
def test_file_delete_when_key_doesnt_exist_returns_404(client, users,
                                                       auth_headers_for_user,
                                                       create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    bucket = deposit.files.bucket

    resp = client.delete('/files/{}/nonexisting.txt'.format(bucket),
                         headers=auth_headers_for_user(owner))

    assert resp.status_code == 404


def test_file_delete_when_owner_of_deposit_can_delete(client, users,
                                                      auth_headers_for_user,
                                                      create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.delete('/files/{}/file_1.txt'.format(bucket),
                         headers=auth_headers_for_user(owner))

    assert resp.status_code == 204


def test_file_delete_when_superuser_can_delete(client, users,
                                               auth_headers_for_superuser,
                                               create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.delete('/files/{}/file_1.txt'.format(bucket),
                         headers=auth_headers_for_superuser)

    assert resp.status_code == 204


def test_file_delete_when_other_user_returns_404(client, users,
                                                 auth_headers_for_user,
                                                 json_headers, create_deposit):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    resp = client.delete('/files/{}/file_1.txt'.format(bucket),
                         headers=auth_headers_for_user(other_user))

    assert resp.status_code == 404


@mark.parametrize("action", [
    ("deposit-update"),
    ("deposit-admin"),
])
def test_file_delete_when_user_has_update_or_admin_access_can_delete(
        action, client, users, auth_headers_for_user, create_deposit,
        json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': action
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.delete('/files/{}/file_1.txt'.format(bucket),
                         headers=auth_headers_for_user(other_user))

    assert resp.status_code == 204


def test_file_delete_when_user_has_only_read_access_returns_403(
        client, users, auth_headers_for_user, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    permissions = [{
        'email': other_user.email,
        'type': 'user',
        'op': 'add',
        'action': 'deposit-read'
    }]

    client.post('/deposits/{}/actions/permissions'.format(pid),
                headers=auth_headers_for_user(owner) + json_headers,
                data=json.dumps(permissions))

    resp = client.delete('/files/{}/file_1.txt'.format(bucket),
                         headers=auth_headers_for_user(other_user))

    assert resp.status_code == 403


def test_file_delete_delets_successfully(client, users, auth_headers_for_user,
                                         create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    deposit.files['file_1.txt'] = BytesIO(b'Hello world!')
    bucket = deposit.files.bucket

    client.delete('/files/{}/file_1.txt'.format(bucket),
                  headers=auth_headers_for_user(owner))

    resp = client.get('/files/{}/file_1.txt'.format(bucket),
                      headers=auth_headers_for_user(owner))

    assert resp.status_code == 404
