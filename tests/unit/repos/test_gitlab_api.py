# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2018 CERN.
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
"""Tests for Gitlab API class."""

import responses
from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError
from unittest.mock import Mock, patch
from pytest import raises

from cap.modules.repos.errors import (GitIntegrationError, GitObjectNotFound,
                                      GitRequestWithInvalidSignature,
                                      GitUnauthorizedRequest)
from cap.modules.repos.gitlab_api import GitlabAPI


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_when_user_unauthorized_raises_GitUnauthorizedRequest(
    m_gitlab):
    class MockProjectManager:
        def get(self, name, lazy):
            raise GitlabAuthenticationError('Unauthorized', 401)

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    with raises(GitUnauthorizedRequest):
        GitlabAPI('gitlab.cern.ch', 'owner_name', 'non-existing-repo')


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_when_repository_doesnt_exist_or_no_access_raises_GitObjectNotFound(
    m_gitlab):
    class MockProjectManager:
        def get(self, name, lazy):
            raise GitlabGetError('Project Not Found', 404)

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    with raises(GitObjectNotFound):
        GitlabAPI('gitlab.cern.ch', 'owner_name', 'non-existing-repo')


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_with_branch(m_gitlab, gitlab_token, example_user):
    class MockBranchManager:
        def get(self, name):
            assert name == 'mybranch'
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            assert name == 'owner_name/myrepository'
            assert lazy is False
            return Mock(branches=MockBranchManager())

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.cern.ch',
                    'owner_name',
                    'myrepository',
                    'mybranch',
                    user_id=example_user.id)

    assert api.host == 'gitlab.cern.ch'
    assert api.owner == 'owner_name'
    assert api.repo == 'myrepository'
    assert api.branch == 'mybranch'
    assert api.sha == 'mybranchsha'
    assert api.token == gitlab_token.access_token

    assert str(
        api) == 'API for gitlab.cern.ch/owner_name/myrepository/mybranch'


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_with_default_branch_when_no_branch_nor_sha_given(m_gitlab):
    class MockBranchManager:
        def get(self, name):
            assert name == 'defaultbranch'
            m = Mock(commit=dict(id='defaultbranchsha'))
            m.name = 'defaultbranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(
                default_branch='defaultbranch',
                branches=MockBranchManager(),
            )

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository')

    assert api.host == 'gitlab.cern.ch'
    assert api.owner == 'owner_name'
    assert api.repo == 'myrepository'
    assert api.branch == 'defaultbranch'
    assert api.sha == 'defaultbranchsha'
    assert api.token is None

    assert str(
        api) == 'API for gitlab.cern.ch/owner_name/myrepository/defaultbranch'


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_when_just_created_repo_without_branches(m_gitlab):
    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(default_branch=None)

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    with raises(GitObjectNotFound):
        GitlabAPI('gitlab.cern.ch', 'owner_name', 'repo')


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_with_sha(m_gitlab):
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

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository',
                    'mycommitsha')

    assert api.host == 'gitlab.cern.ch'
    assert api.owner == 'owner_name'
    assert api.repo == 'myrepository'
    assert api.branch is None
    assert api.sha == 'mycommitsha'
    assert api.token is None

    assert str(
        api) == 'API for gitlab.cern.ch/owner_name/myrepository/mycommitsha'


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_when_commit_with_sha_or_branch_doesnt_exist(m_gitlab):
    class MockCommitManager:
        def get(self, sha):
            assert sha == 'nonexistingsha'
            raise GitlabGetError('Commit Not Found', 404)

    class MockBranchManager:
        def get(self, name):
            assert name == 'nonexistingsha'
            raise GitlabGetError('Branch Not Found', 404)

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(
                branches=MockBranchManager(),
                commits=MockCommitManager(),
            )

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    with raises(GitObjectNotFound):
        GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository',
                  'nonexistingsha')


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_get_repo_download(m_gitlab, example_user, gitlab_token):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch',
                    example_user.id)

    assert api.get_repo_download() == \
        'https://gitlab.cern.ch/api/v4/projects/123/repository/archive?sha=mybranchsha'


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_get_file_download(m_gitlab, example_user, gitlab_token):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    responses.add(
        responses.HEAD,
        ('https://gitlab.cern.ch/api/v4/projects/123/repository/files/'
         'README.md/raw?ref=mybranchsha'),
        content_type='application/json',
        status=200)

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch',
                    example_user.id)

    assert api.get_file_download('README.md') == (
        'https://gitlab.cern.ch/api/v4/projects/123/repository/files/'
        'README.md/raw?ref=mybranchsha', None)

    assert responses.calls[0].request.headers['Private-Token'] == 'some-token'


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_get_file_download_when_file_does_not_exist_or_directory_raises_GitObjectNotFound(
        m_gitlab, example_user, gitlab_token):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    responses.add(
        responses.HEAD,
        ('https://gitlab.cern.ch/api/v4/projects/123/repository/files/'
         'README.md/raw?ref=mybranchsha'),
        content_type='application/json',
        status=404)

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch',
                    example_user.id)

    with raises(GitObjectNotFound):
        api.get_file_download('README.md')

    assert responses.calls[0].request.headers['Private-Token'] == 'some-token'


@patch('cap.modules.repos.gitlab_api.generate_secret',
       Mock(return_value='mysecret'))
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_create_push_webhook(m_gitlab, app):
    app.config['DEBUG'] = False

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

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch')

    assert api.create_webhook('push') == (12345, 'mysecret')


@patch('cap.modules.repos.gitlab_api.generate_secret',
       Mock(return_value='mysecret'))
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_create_release_webhook(m_gitlab, app):
    app.config['DEBUG'] = False

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
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(),
                        hooks=MockHooksManager(),
                        id='123')

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch')

    assert api.create_webhook() == (12345, 'mysecret')


@patch('cap.modules.repos.gitlab_api.generate_secret',
       Mock(return_value='mysecret'))
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_create_webhook_when_no_permissions_to_create_a_webhook_raises_GitIntegrationError(
        m_gitlab, app):
    class MockHooksManager:
        def create(self, data):
            raise GitlabAuthenticationError('Unauthorized', 401)

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

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch')

    with raises(GitIntegrationError):
        api.create_webhook() == (12345, 'mysecret')


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_delete_webhook(m_gitlab, app):
    class MockHooksManager:
        def delete(self, hook_id):
            assert hook_id == 12345

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

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch')

    api.delete_webhook(12345)


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_delete_webhook_when_webhook_does_not_exist_raises_GitObjectNotFound(
        m_gitlab, app):
    class MockHooksManager:
        def delete(self, hook_id):
            raise GitlabGetError('Not Found', 404)

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

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch')

    with raises(GitObjectNotFound):
        api.delete_webhook(1245)


@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_gitlab_api_delete_webhook_when_no_permission_to_webhook_raises_GitObjectNotFound(
        m_gitlab, app):
    class MockHooksManager:
        def delete(self, hook_id):
            raise GitlabAuthenticationError('Unauthorized', 401)

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

    api = GitlabAPI('gitlab.cern.ch', 'owner_name', 'myrepository', 'mybranch')

    with raises(GitObjectNotFound):
        api.delete_webhook(1245)


@patch('cap.modules.repos.gitlab_api.Gitlab', Mock())
@patch.object(GitlabAPI, '_get_branch_and_sha', return_value=(None, None))
def test_gitlab_api_verify_request_when_sha_and_secret_match(
    m_get_branch_and_sha, app):
    with app.test_request_context('/',
                                  headers={'X-Gitlab-Token': 'mysecretsecret'
                                           }):
        api = GitlabAPI('gitlab.com', 'owner', 'repository')
        api.verify_request('mysecretsecret')


@patch('cap.modules.repos.gitlab_api.Gitlab', Mock())
@patch.object(GitlabAPI, '_get_branch_and_sha', return_value=(None, None))
def test_gitlab_api_verify_request_when_sha_and_secret_dont_match_raises_GitRequestWithInvalidSignature(
    m_get_branch_and_sha, app):
    with app.test_request_context('/',
                                  headers={'X-Gitlab-Token': 'notmysecret'}):
        api = GitlabAPI('gitlab.com', 'owner', 'repository')

        with raises(GitRequestWithInvalidSignature):
            api.verify_request('mysecretsecret')


@patch('cap.modules.repos.gitlab_api.Gitlab')
@patch.object(GitlabAPI, '_get_branch_and_sha', return_value=(None, None))
def test_gitlab_api_ping_webhook(m_get_branch_and_sha, m_gitlab):
    class MockHooksManager:
        def get(self, id):
            assert id == 123
            return Mock(id=123)

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(hooks=MockHooksManager())

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.com', 'owner', 'repository', 'my-branch')

    api.ping_webhook(123)


@patch('cap.modules.repos.gitlab_api.Gitlab')
@patch.object(GitlabAPI, '_get_branch_and_sha', return_value=(None, None))
def test_gitlab_api_ping_webhook_when_hook_doesnt_exist_raises_GitObjectNotFound(
    m_get_branch_and_sha, m_gitlab):
    class MockHooksManager:
        def get(self, id):
            raise GitlabGetError('Not Found', 404)

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(hooks=MockHooksManager())

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.com', 'owner', 'repository')

    with raises(GitObjectNotFound):
        api.ping_webhook(123)


@patch('cap.modules.repos.gitlab_api.Gitlab')
@patch.object(GitlabAPI, '_get_branch_and_sha', return_value=(None, None))
def test_gitlab_api_ping_webhook_when_user_have_no_permission_raises_GitObjectNotFound(
    m_get_branch_and_sha, m_gitlab):
    class MockHooksManager:
        def get(self, id):
            raise GitlabAuthenticationError('Unauthorized', 401)

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(hooks=MockHooksManager())

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.com', 'owner', 'repository')

    with raises(GitObjectNotFound):
        api.ping_webhook(123)


@patch('cap.modules.repos.gitlab_api.Gitlab')
@patch.object(GitlabAPI, '_get_branch_and_sha', return_value=(None, None))
def test_gitlab_api_repo_id(m_get_branch_and_sha, m_gitlab):
    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(id=123)

    m_gitlab.return_value = Mock(projects=MockProjectManager())

    api = GitlabAPI('gitlab.com', 'owner', 'repository', 'my-branch')

    assert api.repo_id == 123
