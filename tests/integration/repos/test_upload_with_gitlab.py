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

from __future__ import absolute_import, print_function

import json
import tarfile
import responses
from unittest.mock import Mock, patch
from pytest import mark

from gitlab.exceptions import GitlabGetError
from invenio_files_rest.models import ObjectVersion

from cap.modules.repos.models import GitWebhookSubscriber, GitWebhook


def test_upload_when_wrong_url(client, deposit, auth_headers_for_example_user,
                               json_headers):
    pid = deposit['_deposit']['id']

    resp = client.post(f'/deposits/{pid}/actions/upload',
                       headers=auth_headers_for_example_user + json_headers,
                       data=json.dumps({
                           'type': 'repo_download_attach',
                           'url': 'http://gitlab.cern.ch/verywrongurl'
                       }))

    assert resp.status_code == 400
    assert resp.json == {'status': 400, 'message': 'Invalid git URL.'}


@mark.skip
@patch('cap.modules.repos.gitlab_api.Gitlab')
@patch('cap.modules.deposit.api.create_git_api')
def test_upload_when_user_gave_url_with_sha_and_tries_to_create_a_push_webhook_raises_an_error(
    m_api, m_gitlab, client, deposit, auth_headers_for_example_user, json_headers,
    git_repo_tar):
    class MockCommitManager:
        def get(self, sha):
            assert sha == 'mycommitsha'
            return Mock(id='mycommitsha')

    class MockBranchManager:
        def get(self, name):
            raise GitlabGetError('Branch Not Found', 404)

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(
                branches=MockBranchManager(),
                commits=MockCommitManager(),
            )

    def create_webhook(type_):
        return 'id', 'secret'

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    m_api.return_value = Mock(repo_id='id', host='gitlab.cern.ch', repo='repo',
                              owner='owner', branch='mycommitsha',
                              create_webhook=create_webhook)
    pid = deposit['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/upload',
        headers=auth_headers_for_example_user + json_headers,
        data=json.dumps({
            'type': 'attach',
            'url': 'http://gitlab.cern.ch/owner/repository/mycommitsha',
            'webhook': 'push'
        }))

    assert resp.status_code == 400
    assert resp.json == {
        'status': 400,
        'message': 'You cannot create a push webhook for a specific sha.'
    }


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_upload_when_repo(m_gitlab, client, deposit,
                          auth_headers_for_example_user, json_headers,
                          git_repo_tar):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    pid = deposit['_deposit']['id']
    responses.add(responses.GET, (
        'https://gitlab.cern.ch/api/v4/projects/123/repository/archive?sha=mybranchsha'
    ),
                  body=git_repo_tar,
                  content_type='application/octet_stream',
                  headers={
                      'Transfer-Encoding': 'binary',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post(
        f'/deposits/{pid}/actions/upload',
        headers=auth_headers_for_example_user + json_headers,
        data=json.dumps({
            'type': 'repo_download_attach',
            'url': 'http://gitlab.cern.ch/owner/repository/mybranch',
            'download': True
        }))

    assert resp.status_code == 201

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/gitlab.cern.ch/owner/repository/mybranch.tar.gz')
    tar_obj = tarfile.open(obj.file.uri)
    repo_file_name = tar_obj.getmembers()[1]
    repo_content = tar_obj.extractfile(repo_file_name).read()

    assert repo_content == b'test repo for cap\n'


@responses.activate
def test_upload_for_record_so_bucket_is_locked_returns_403(
    client, record, auth_headers_for_example_user, json_headers, git_repo_tar):
    pid = record['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/upload',
        headers=auth_headers_for_example_user + json_headers,
        data=json.dumps(
            {'url': 'http://gitlab.cern.ch/owner/repository/mybranch'}))

    assert resp.status_code == 403


@responses.activate
@patch('cap.modules.repos.gitlab_api.generate_secret',
       Mock(return_value='mysecret'))
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_upload_when_repo_and_creating_push_webhook(
    m_gitlab, client, deposit, auth_headers_for_example_user, json_headers,
    git_repo_tar):
    class MockHooksManager:
        def create(self, data):
            assert data == {
                'url': 'http://analysispreservation.cern.ch/api/repos/event',
                'token': 'mysecret',
                'push_events': True,
                'tag_push_events': False
            }
            return Mock(id=12345)

    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(),
                        hooks=MockHooksManager(),
                        id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    pid = deposit['_deposit']['id']

    responses.add(responses.GET, (
        'https://gitlab.cern.ch/api/v4/projects/123/repository/archive?sha=mybranchsha'
    ),
                  body=git_repo_tar,
                  content_type='application/octet_stream',
                  headers={
                      'Transfer-Encoding': 'binary',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post(
        f'/deposits/{pid}/actions/upload',
        headers=auth_headers_for_example_user + json_headers,
        data=json.dumps({
            'type': 'repo_download_attach',
            'url': 'http://gitlab.cern.ch/owner/repository/mybranch',
            'webhook': 'push'
        }))

    assert resp.status_code == 201

    # no file was saved
    assert not deposit.files

    # webhook was created
    webhook = GitWebhook.query.filter_by(event_type='push').one()
    sub = GitWebhookSubscriber.query.filter_by(record_id=deposit.id, webhook_id=webhook.id).one()
    repo = sub.webhook.repo

    assert sub.webhook.branch == 'mybranch'
    assert (repo.host, repo.owner, repo.name) == ('gitlab.cern.ch', 'owner',
                                                  'repository')


@responses.activate
@patch('cap.modules.repos.gitlab_api.generate_secret',
       Mock(return_value='mysecret'))
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_upload_when_repo_and_creating_release_webhook(
    m_gitlab, client, deposit, auth_headers_for_example_user, json_headers,
    git_repo_tar):
    class MockHooksManager:
        def create(self, data):
            assert data == {
                'url': 'http://analysispreservation.cern.ch/api/repos/event',
                'token': 'mysecret',
                'push_events': False,
                'tag_push_events': True
            }
            return Mock(id=12345)

    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='defaultbranchsha'))
            m.name = 'defaultbranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(),
                        default_branch='defaultbranch',
                        hooks=MockHooksManager(),
                        id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    pid = deposit['_deposit']['id']

    responses.add(responses.GET, (
        'https://gitlab.cern.ch/api/v4/projects/123/repository/archive?sha=defaultbranchsha'
    ),
                  body=git_repo_tar,
                  content_type='application/octet_stream',
                  headers={
                      'Transfer-Encoding': 'binary',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post(f'/deposits/{pid}/actions/upload',
                       headers=auth_headers_for_example_user + json_headers,
                       data=json.dumps({
                           'type': 'repo_download_attach',
                           'url': 'http://gitlab.cern.ch/owner/repository',
                           'webhook': 'release'
                       }))

    assert resp.status_code == 201

    # no file was saved
    assert not deposit.files


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_upload_when_repo_file(m_gitlab, client, deposit,
                               auth_headers_for_example_user, json_headers):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    pid = deposit['_deposit']['id']
    responses.add(
        responses.HEAD,
        ('https://gitlab.cern.ch/api/v4/projects/123/repository/files/'
         'README.md/raw?ref=mybranchsha'),
        content_type='application/json',
        status=200)
    responses.add(
        responses.GET,
        ('https://gitlab.cern.ch/api/v4/projects/123/repository/files/'
         'README.md/raw?ref=mybranchsha'),
        content_type='text/plain; charset=utf-8',
        body=b'readme',
        stream=True,
        headers={'Content-Length': '6'},
        status=200)

    resp = client.post(
        f'/deposits/{pid}/actions/upload',
        headers=auth_headers_for_example_user + json_headers,
        data=json.dumps({
            'type': 'repo_download_attach',
            'url': 'http://gitlab.cern.ch/owner/repository/blob/mybranch/README.md'
        }))

    assert resp.status_code == 201

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/gitlab.cern.ch/owner/repository/mybranch/README.md')
    open_file = open(obj.file.uri)
    repo_content = open_file.read()

    assert repo_content == 'readme'


@patch('cap.modules.repos.integrator.host_to_git_api')
@patch('cap.modules.repos.integrator.create_git_api')
def test_create_repo_as_user_and_attach(m_create_api, m_api, client, deposit,
                                        auth_headers_for_example_user, json_headers):
    
    class MockRepo(object):
        attributes = {
            'web_url': 'https://gitlab.cern.ch/attach-deposit/repository-create-test/'
        }

    class MockAPI(object):
        branch = None
        repo_id = 321
        host = 'gitlab.cern.ch'
        owner = 'attach-deposit'
        repo = 'repository-create-test'

        def create_webhook(type_):
            return 'id', 'secret'

    class MockProject(object):
        def create_repo_as_user(cls, user_id, repo_name, description='',
                                private=False, license=None, org_name=None, host=None):
            return MockRepo()

    m_api.return_value = MockProject()
    m_create_api.return_value = MockAPI()
    mock_pid = deposit['_deposit']['id']
    resp = client.post(f'/deposits/{mock_pid}/actions/upload'.format(mock_pid),
                       headers=auth_headers_for_example_user + json_headers,
                       data=json.dumps({
                           'type': 'repo_create',
                           'name': 'repository-create-test',
                           'host': 'gitlab.cern.ch',
                           'org_name': 'attach-deposit'
                       }))

    assert resp.status_code == 201

    webhook = GitWebhook.query.filter_by(event_type=None).one()
    sub = GitWebhookSubscriber.query.filter_by(record_id=deposit.id, webhook_id=webhook.id).one()
    repo = sub.webhook.repo

    assert repo.name == 'repository-create-test'
    assert repo.owner == 'attach-deposit'


@patch('cap.modules.repos.integrator.create_git_api')
def test_attach_repo_to_deposit(m_create_api, client, deposit,
                                auth_headers_for_example_user, json_headers):

    class MockAPI(object):
        branch = 'master'
        repo_id = 123
        host = 'gitlab.cern.ch'
        owner = 'attach-deposit'
        repo = 'repository-attach-test'

        def create_webhook(record_uuid, api, type_=None):
            return 123, 'secret'

    m_create_api.return_value = MockAPI()
    mock_pid = deposit['_deposit']['id']

    resp = client.post(f'/deposits/{mock_pid}/actions/upload'.format(mock_pid),
                       headers=auth_headers_for_example_user + json_headers,
                       data=json.dumps({
                           'type': 'repo_download_attach',
                           'url': 'https://gitlab.cern.ch/attach-deposit/repository-attach-test',
                           'download': False,
                           'webhook': 'push'
                       }))

    assert resp.status_code == 201

    webhook = GitWebhook.query.filter_by(event_type=None).one()
    sub = GitWebhookSubscriber.query.filter_by(record_id=deposit.id, webhook_id=webhook.id).one()
    repo = sub.webhook.repo

    assert repo.name == 'repository-attach-test'
    assert repo.owner == 'attach-deposit'

    webhook_push = GitWebhook.query.filter_by(event_type='push').one()

    assert webhook_push.branch == 'master'
    assert repo.id == webhook_push.repo_id


@patch('cap.modules.repos.integrator.populate_template_from_ctx')
@patch('cap.modules.repos.integrator.host_to_git_api')
@patch('cap.modules.repos.integrator.create_git_api')
def test_create_schema_default_repo_and_attach(m_create_api, m_api, m_populate, client, deposit,
                                                app, users, create_deposit, create_schema,
                                                auth_headers_for_superuser, json_headers):
    # Use the config
    SAMPLE_CONFIG = {
        "repositories": {
            "gitlab_test": {
                "host": "gitlab.cern.ch",
                "authentication": {
                    "type": "cap"
                },
                "host": "gitlab.cern.ch",
                "org_id": "1234",
                "org_name": "attach-deposit",
                "repo_name": {
                    "template": "test_info.html",
                    "ctx": {
                        "glance_id": {
                            "type": "path",
                            "path": "record.id"
                        }
                    }
                },
                "private": False,
                "license": "",
                "repo_description": {
                    "template": "test_info.html",
                    "ctx": {
                            "glance_id": {
                                "method": "draft_url"
                        }
                    }
                }
            }
        }
    }
    class MockRepo(object):
        attributes = {
            'web_url': 'https://gitlab.cern.ch/attach-deposit/test-collab'
        }

    class MockAPI(object):
        branch = 'master'
        repo_id = 123
        host = 'gitlab.cern.ch'
        owner = 'attach-deposit'
        repo = 'test-collab'

        def create_webhook(record_uuid, api, type_=None):
            return 'id', 'secret'

    class MockProject(object):
        def create_repo(cls, token, repo_name, description,
                        private, license, org_name):
            return MockRepo()

        def create_repo_as_collaborator(cls, token, organization, name, description,
                                        private, license, host):
            return MockRepo(), ""

    m_api.return_value = MockProject()
    m_create_api.return_value = MockAPI()

    user = users['superuser']
    create_schema('test', config=SAMPLE_CONFIG)
    deposit = create_deposit(user, 'test', experiment='CMS')
    mock_pid = deposit['_deposit']['id']
    m_populate.return_value = 'test-collab'

    resp = resp = client.post(f'/deposits/{mock_pid}/actions/upload'.format(mock_pid),
                       headers=auth_headers_for_superuser + json_headers,
                       data=json.dumps({ 
                           'type': 'repo_create_default',
                           'name': 'gitlab_test'
                       }))

    assert resp.status_code == 201

    webhook = GitWebhook.query.filter_by(event_type=None).one()
    sub = GitWebhookSubscriber.query.filter_by(record_id=deposit.id, webhook_id=webhook.id).one()
    repo = sub.webhook.repo

    assert repo.name == 'test-collab'
    assert repo.owner == 'attach-deposit'
