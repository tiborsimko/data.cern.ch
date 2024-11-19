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

"""Integration tests for CAP api."""
from __future__ import absolute_import, print_function

import json
from unittest.mock import patch
from pytest import mark

from reana_client.errors import FileDeletionError

@mark.skip
@patch('cap.modules.workflows.views.ping', return_value='not ok!')
def test_reana_ping_not_ok(mock_ping, app, auth_headers_for_superuser, json_headers):
    with app.test_client() as client:
        resp = client.get('workflows/reana/ping', headers=auth_headers_for_superuser + json_headers)
        assert resp.status_code == 400
        assert resp.json['message'] == 'not ok!'


@mark.skip
@patch('cap.modules.workflows.views.ping', side_effect=Exception())
def test_reana_ping_exception(mock_ping, app, auth_headers_for_superuser, json_headers):
    with app.test_client() as client:
        resp = client.get('workflows/reana/ping',
                          headers=auth_headers_for_superuser + json_headers)
        assert resp.status_code == 400


@mark.skip
@patch('cap.modules.workflows.views.create_workflow_from_json')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_create_reana_workflow(mock_token, mock_created, app, get_record_pid_uuid,
                               auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_created.return_value = {
        'message': 'Workflow workspace created',
        'workflow_id': 'a5140d92-65e3-4fb0-a246-dc1f06cc2e13',
        'workflow_name': 'demo.1'
    }

    mock_data = {
        "pid": pid,
        "workflow_name": "demo",
        "workflow_engine": "serial",
        "workflow_json": {"steps": [{"environment": "python:2.7-slim",
                                     "commands": ["python \"${helloworld}\""]}]},
        "parameters": {"files": ["code/helloworld.py"],
                       "parameters": {"helloworld": "code/helloworld.py"}},
        "outputs": {"files": ["results/results.txt"]}
    }

    with app.test_client() as client:
        resp = client.post('workflows/reana/create', data=json.dumps(mock_data),
                           headers=auth_headers_for_superuser + json_headers)
        assert resp.status_code == 200
        assert resp.json == {
            "engine": "serial", "rec_uuid": uuid,
            "status": "created", "workflow_name": "demo.1",
            "workflow_id": "a5140d92-65e3-4fb0-a246-dc1f06cc2e13"
        }


@mark.skip
@patch('cap.modules.workflows.views.create_workflow_from_json', side_effect=Exception())
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_create_reana_workflow_exception(mock_token, mock_created, app, get_record_pid_uuid,
                                         auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_data = {
        "pid": pid, "workflow_name": "demo", "workflow_engine": "yadage",
        "workflow_json": {}, "parameters": {}, "outputs": {}
    }

    with app.test_client() as client:
        resp = client.post('workflows/reana/create', data=json.dumps(mock_data),
                           headers=auth_headers_for_superuser + json_headers)
        assert resp.status_code == 400
        assert resp.json == {'message': 'An exception has occured while creating the workflow.'}


@mark.skip
@patch('cap.modules.workflows.views.get_workflows')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_get_all_workflows(mock_token, mock_get_all, app, get_record_pid_uuid,
                           auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_get_all.return_value = [{
        u'created': u'2019-09-12T14:56:35',
        u'id': u'26db86dc-4f32-428e-b1cf-c84bbe190db9',
        u'name': u'demo.2', u'size': u'512', u'status': u'created',
        u'user': u'9ee3a516-7e97-4e50-852f-636c0b881f3a'
    }, {
        u'id': u'8cc0dfa5-473b-49cf-8636-4bd48a59b847',
        u'name': u'demo.1', u'size': u'31K', u'status': u'deleted',
        u'user': u'9ee3a516-7e97-4e50-852f-636c0b881f3a'
    }]

    with app.test_client() as client:
        resp = client.get('workflows/reana/all/record/{}'.format(pid),
                          headers=auth_headers_for_superuser + json_headers)
        assert resp.status_code == 200
        assert resp.json == {
            "current_workflows": [{
                "id": "26db86dc-4f32-428e-b1cf-c84bbe190db9",
                "name": "demo.2", "status": "created"
            }],
            "deleted_workflows": [{
                "id": "8cc0dfa5-473b-49cf-8636-4bd48a59b847",
                "name": "demo.1", "status": "deleted"
            }],
            "rec_uuid": uuid
        }


@mark.skip
@patch('cap.modules.workflows.views.get_workflow_logs')
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_reana_workflow_logs(mock_token, mock_uuid, mock_logs, app, get_record_pid_uuid,
                             auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_workflow_id = 'b46e27ac-a40e-4e4e-97ee-30703e6f1406'
    mock_uuid.return_value = uuid
    mock_logs.return_value = {
        'logs': '{"workflow_logs": "this is a tracking log at 2019-09-12T12:34:18.074285", '
                '"job_logs": {}, "engine_specific": null}',
        'user': '9ee3a516-7e97-4e50-852f-636c0b881f3a',
        'workflow_id': mock_workflow_id, 'workflow_name': 'demo.3'
    }

    with app.test_client() as client:
        resp = client.get('workflows/reana/{}/logs'.format(mock_workflow_id),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 200
        assert resp.json == {
            "logs": {
                "engine_specific": None,
                "job_logs": {},
                "workflow_logs": "this is a tracking log at 2019-09-12T12:34:18.074285"
              },
            "rec_uuid": uuid, "workflow_id": mock_workflow_id, "workflow_name": "demo.3"
        }


@mark.skip
@patch('cap.modules.workflows.views.start_workflow', side_effect=Exception())
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_start_exception(mock_token, mock_uuid, mock_start, app, get_record_pid_uuid,
                                  auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'

    with app.test_client() as client:
        resp = client.post('workflows/reana/{}/start'.format(mock_workflow_id),
                           headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 400
        assert resp.json == {'message': 'An exception has occured, most probably '
                                        'the workflow cannot restart.'}


@mark.skip
@patch('cap.modules.workflows.views.stop_workflow', side_effect=Exception())
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_stop_exception(mock_token, mock_uuid, mock_stop, app, get_record_pid_uuid,
                                 auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'

    with app.test_client() as client:
        resp = client.post('workflows/reana/{}/stop'.format(mock_workflow_id),
                           headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 400
        assert resp.json == {'message': 'An exception has occured, most probably '
                                        'the workflow is not running.'}


@mark.skip
@patch('cap.modules.workflows.views.delete_workflow', side_effect=Exception())
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_delete_exception(mock_token, mock_uuid, mock_start, app, get_record_pid_uuid,
                                   auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'

    with app.test_client() as client:
        resp = client.delete('workflows/reana/{}/delete'.format(mock_workflow_id),
                             headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 400
        assert resp.json == {'message': 'Workflow {} does not exist. '
                                        'Aborting deletion.'.format(mock_workflow_id)}


@mark.skip
@patch('cap.modules.workflows.views.list_files')
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_list_files(mock_token, mock_uuid, mock_ls, app, get_record_pid_uuid,
                             auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'
    mock_uuid.return_value = uuid
    mock_ls.return_value = [{
        'last-modified': '2019-09-12T11:25:30',
        'name': '_yadage/yadage_snapshot_backend.json', 'size': 2
    }, {
        'last-modified': '2019-09-12T11:25:30',
        'name': '_yadage/yadage_snapshot_workflow.json', 'size': 1943
    }, {
        'last-modified': '2019-09-12T11:25:30',
        'name': '_yadage/yadage_template.json', 'size': 1104
    }]

    with app.test_client() as client:
        resp = client.get('workflows/reana/{}/ls'.format(mock_workflow_id),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 200
        assert resp.json == {
            "files": [{
                "last-modified": "2019-09-12T11:25:30",
                "name": "_yadage/yadage_snapshot_backend.json", "size": 2
            }, {
                "last-modified": "2019-09-12T11:25:30",
                "name": "_yadage/yadage_snapshot_workflow.json", "size": 1943
            }, {
                "last-modified": "2019-09-12T11:25:30",
                "name": "_yadage/yadage_template.json", "size": 1104
            }],
            "rec_uuid": uuid, "workflow_id": mock_workflow_id
        }


@mark.skip
@patch('cap.modules.workflows.views.list_files', side_effect=Exception())
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_list_files_exception(mock_token, mock_uuid, mock_ls, app, get_record_pid_uuid,
                                       auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'

    with app.test_client() as client:
        resp = client.get('workflows/reana/{}/ls'.format(mock_workflow_id),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 400
        assert resp.json == {'message': 'File list from workflow {} could not be '
                                        'retrieved. Aborting listing.'.format(mock_workflow_id)}


@mark.skip
@patch('cap.modules.workflows.views.delete_file', side_effect=FileDeletionError())
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_delete_files_exception(mock_token, mock_uuid, mock_rm, app, get_record_pid_uuid,
                                         auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'
    mock_path = 'code/code.py'

    with app.test_client() as client:
        resp = client.delete('workflows/reana/{}/rm?file_path={}'.format(mock_workflow_id, mock_path),
                             headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 400
        assert resp.json == {'message': '{} did not match any existing file. '
                                        'Aborting deletion.'.format(mock_path)}


@mark.skip
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_upload_files_with_errors(mock_token, mock_uuid, app, get_record_pid_uuid,
                                           auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'
    mock_data = {
        'files_to_upload': [
            {'path': 'tmp/example1.txt', 'new_path': 'data/example1.txt'}
        ]
    }

    with app.test_client() as client:
        resp = client.post('workflows/reana/{}/upload'.format(mock_workflow_id),
                           data=json.dumps(mock_data),
                           headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 200
        assert resp.json == {'workflow_id': mock_workflow_id,
                             'successful': [],
                             'errors': ['tmp/example1.txt']}


@mark.skip
@patch('cap.modules.workflows.views.download_file', side_effect=Exception())
@patch('cap.modules.workflows.views.resolve_uuid')
@patch('cap.modules.workflows.views.get_reana_token', return_value='test-token')
def test_workflow_download_files_exception(mock_token, mock_uuid, mock_download, app, get_record_pid_uuid,
                                           auth_headers_for_superuser, json_headers):
    pid, uuid = get_record_pid_uuid
    mock_uuid.return_value = uuid
    mock_workflow_id = '7393815e-e3ef-4f7c-a0fe-a3a30a10ac2f'
    mock_path = 'code/code.py'

    with app.test_client() as client:
        resp = client.get('workflows/reana/{}/download?file_path={}'.format(mock_workflow_id, mock_path),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 400
        assert resp.json == {'message': '{} did not match any existing file. '
                                        'Aborting download.'.format(mock_path)}
