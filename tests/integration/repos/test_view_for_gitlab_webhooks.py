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
"""Tests for endpoint for Gittlab webhooks."""

import json
import tarfile

import responses
from invenio_files_rest.models import ObjectVersion
from unittest.mock import Mock, patch
from pytest import mark

from cap.modules.repos.models import GitSnapshot

push_headers = {
    "Content-Type": "application/json",
    "X-Gitlab-Event": "Push Hook",
    "X-Gitlab-Token": "mysecretsecret"
}

# this is a shortened payload for testing purposes, check documentation to see more
push_payload_shortened = {
    "object_kind": "push",
    "event_name": "push",
    "before": "6111aac64d15bcda6215f6792f3eadf638309cd3",
    "after": "87735e015e2b4faf60415833478dacd3174b2d1c",
    "ref": "refs/heads/mybranch",
    "checkout_sha": "87735e015e2b4faf60415833478dacd3174b2d1c",
    "message": None,
    "user_id": 1,
    "user_name": "owner_name",
    "user_username": "owner_name",
    "user_email": "",
    "user_avatar": "https://secure.gravatar.com/avatar/72a7565394014378baffcbc503d75b12?s=80&d=identicon",
    "project_id": 12345,
    "project": {
        "id": 12345,
        "name": "myrepository",
        "description": "",
        "namespace": "owner_name",
        "visibility_level": 20,
        "path_with_namespace": "owner_name/myrepository",
        "default_branch": "master",
        "ci_config_path": None,
    },
    "commits": [{
        "id": "87735e015e2b4faf60415833478dacd3174b2d1c",
        "message": "Update README.md",
        "title": "Update README.md",
        "timestamp": "2020-02-26T18:54:15+00:00",
        "url": "https://gitlab.cern.ch/owner_name/myrepository/-/commit/87735e015e2b4faf60415833478dacd3174b2d1c",
        "author": {
            "name": "owner_name",
            "email": "owner_name@gmail.com"
        },
        "added": [],
        "modified": ["README.md"],
        "removed": []
    }, {
        "id": "52160efe9888c7825ae7b691481148eb4a422010",
        "message": "Update README.md",
        "title": "Update README.md",
        "timestamp": "2019-12-13T14:40:48+00:00",
        "url": "https://gitlab.cern.ch/owner_name/myrepository/-/commit/52160efe9888c7825ae7b691481148eb4a422010",
        "author": {
            "name": "owner_name",
            "email": "owner_name@gmail.com"
        },
        "added": [],
        "modified": ["README.md"],
        "removed": []
    }, {
        "id": "6111aac64d15bcda6215f6792f3eadf638309cd3",
        "message": "Add new directory",
        "title": "Add new directory",
        "timestamp": "2019-12-13T14:36:25+00:00",
        "url": "https://gitlab.cern.ch/owner_name/myrepository/-/commit/6111aac64d15bcda6215f6792f3eadf638309cd3",
        "author": {
            "name": "owner_name",
            "email": "owner_name@gmail.com"
        },
        "added": ["dir/.gitkeep"],
        "modified": [],
        "removed": []
    }],
    "total_commits_count": 3,
    "push_options": {},
    "repository": {
        "name": "myrepository",
        "description": "",
        "visibility_level": 20
    }
}

tag_push_headers = {
    "Content-Type": "application/json",
    "X-Gitlab-Event": "Tag Push Hook",
    "X-Gitlab-Token": "mysecretsecret"
}

# this is a shortened payload for testing purposes, check documentation to see more
tag_push_payload_shortened = {
    "object_kind": "tag_push",
    "event_name": "tag_push",
    "before": "0000000000000000000000000000000000000000",
    "after": "ec70b17d01ac909b7d4d254d88a283214d91b9ac",
    "ref": "refs/tags/v3.0.0",
    "checkout_sha": "ec70b17d01ac909b7d4d254d88a283214d91b9ac",
    "message": "My release",
    "user_id": 1,
    "user_name": "owner_name",
    "user_username": "owner_name",
    "user_email": "",
    "project_id": 12345,
    "project": {
        "id": 12345,
        "name": "myrepository",
        "description": "",
        "namespace": "owner_name",
        "visibility_level": 20,
        "path_with_namespace": "owner_name/myrepository",
        "default_branch": "mybranch",
        "ci_config_path": None,
        "homepage": "https://gitlab.com/owner_name/myrepository",
        "url": "git@gitlab.com:owner_name/myrepository.git",
    },
    "commits": [{
        "id": "ec70b17d01ac909b7d4d254d88a283214d91b9ac",
        "message": "Update README.md next",
        "title": "Update README.md next",
        "timestamp": "2020-02-25T13:18:15+00:00",
        "url": "https://gitlab.com/owner_name/myrepository/-/commit/ec70b17d01ac909b7d4d254d88a283214d91b9ac",
        "author": {
            "name": "owner_name",
            "email": "owner@gmail.com"
        },
        "added": [],
        "modified": ["README.md"],
        "removed": []
    }],
    "total_commits_count": 1,
    "push_options": {},
    "repository": {
        "name": "myrepository",
        "url": "git@gitlab.com:owner_name/myrepository.git",
        "description": "",
        "homepage": "https://gitlab.com/owner_name/myrepository",
        "git_http_url": "https://gitlab.com/owner_name/myrepository.git",
        "git_ssh_url": "git@gitlab.com:owner_name/myrepository.git",
        "visibility_level": 20
    }
}


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_get_webhook_event_view_when_push_event(m_gitlab, deposit, client,
                                                gitlab_push_webhook_sub, git_repo_tar):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='12345')

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    responses.add(responses.GET, (
        'https://gitlab.cern.ch/api/v4/projects/12345/repository/archive?sha=mybranchsha'
    ),
                  body=git_repo_tar,
                  content_type='application/octet_stream',
                  headers={
                      'Transfer-Encoding': 'binary',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post('/repos/event',
                       headers=push_headers,
                       data=json.dumps(push_payload_shortened))

    assert resp.status_code == 200
    assert resp.json == {'message': 'Snapshot of repository was saved.'}
    assert responses.calls[0].request.headers['Private-Token'] == 'some-token'

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/gitlab.cern.ch/owner_name/myrepository/mybranch.tar.gz')
    tar_obj = tarfile.open(obj.file.uri)
    repo_file_name = tar_obj.getmembers()[1]
    repo_content = tar_obj.extractfile(repo_file_name).read()

    assert repo_content == b'test repo for cap\n'

    snapshot = gitlab_push_webhook_sub.snapshots[0]
    assert obj.snapshot_id == snapshot.id
    assert GitSnapshot.query.count() == 1
    assert snapshot.payload == {
        'branch': 'mybranch',
        'link': 'https://gitlab.cern.ch/owner_name/myrepository/-/commit/87735e015e2b4faf60415833478dacd3174b2d1c',
        'event_type': 'push',
        'commit': [{
            'id': '87735e015e2b4faf60415833478dacd3174b2d1c',
            'message': 'Update README.md',
            'added': [],
            'removed': [],
            'modified': ['README.md']
        }, {
            'id': '52160efe9888c7825ae7b691481148eb4a422010',
            'message': 'Update README.md',
            'added': [],
            'removed': [],
            'modified': ['README.md']
        }, {
            'id': '6111aac64d15bcda6215f6792f3eadf638309cd3',
            'message': 'Add new directory',
            'added': ['dir/.gitkeep'],
            'removed': [],
            'modified': []
        }],
        'author': {
            'name': 'owner_name',
            'id': 1
        }
    }


@responses.activate
@patch('cap.modules.repos.gitlab_api.Gitlab')
def test_get_webhook_event_view_when_release_event(m_gitlab, deposit, client,
                                                   gitlab_release_webhook_sub,
                                                   git_repo_tar):
    class MockBranchManager:
        def get(self, name):
            m = Mock(commit=dict(id='mybranchsha'))
            m.name = 'mybranch'
            return m

    class MockProjectManager:
        def get(self, name, lazy):
            return Mock(branches=MockBranchManager(), id='12345')

    m_gitlab.return_value = Mock(projects=MockProjectManager())
    responses.add(responses.GET, (
        'https://gitlab.cern.ch/api/v4/projects/12345/repository/archive?sha=mybranchsha'
    ),
                  body=git_repo_tar,
                  content_type='application/octet_stream',
                  headers={
                      'Transfer-Encoding': 'binary',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post('/repos/event',
                       headers=tag_push_headers,
                       data=json.dumps(tag_push_payload_shortened))

    assert resp.status_code == 200
    assert resp.json == {'message': 'Snapshot of repository was saved.'}
    assert responses.calls[0].request.headers['Private-Token'] == 'some-token'

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/gitlab.cern.ch/owner_name/myrepository/v3.0.0.tar.gz')
    tar_obj = tarfile.open(obj.file.uri)
    repo_file_name = tar_obj.getmembers()[1]
    repo_content = tar_obj.extractfile(repo_file_name).read()

    assert repo_content == b'test repo for cap\n'

    snapshot = gitlab_release_webhook_sub.snapshots[0]
    assert obj.snapshot_id == snapshot.id
    assert GitSnapshot.query.count() == 1
    assert snapshot.payload == {
        'event_type': 'release',
        'author': {
            'name': 'owner_name',
            'id': 1
        },
        'link': 'https://gitlab.com/owner_name/myrepository/tags/v3.0.0',
        'release': {
            'tag': 'v3.0.0',
            'name': 'My release'
        }
    }
