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
"""Tests for endpoint for GitHub webhooks."""

import json
import tarfile

from invenio_files_rest.models import ObjectVersion

import responses
from unittest.mock import Mock, patch

from cap.modules.repos.github_api import Github
from cap.modules.repos.models import GitSnapshot

ping_headers = {
    "Content-Type": "application/json",
    "User-Agent": "GitHub-Hookshot/49beeff",
    "X-GitHub-Delivery": "23181600-55a4-11ea-95f3-651867586ba0",
    "X-GitHub-Event": "ping",
    "X-Hub-Signature": "sha1=da57911117c1d33def8b22dac41e64bd950a0829"
}

ping_payload_without_urls = {
    "zen": "Favor focus over features.",
    "hook_id": 666,
    "hook": {
        "type": "Repository",
        "id": 666,
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "content_type": "json",
            "secret": "********",
            "url": "https://analysispreservation.cern.ch/api/repos/event",
            "insecure_ssl": "0"
        },
        "updated_at": "2020-02-22T18:50:04Z",
        "created_at": "2020-02-22T18:50:04Z",
    },
    "repository": {
        "id": 12345,
        "node_id": "id",
        "name": "repo",
        "full_name": "owner/repo",
        "private": False,
        "html_url": "https://github.com/owner/repo",
        "owner": {
            "login": "owner",
            "id": 1,
            "node_id": "id",
            "gravatar_id": "",
            "type": "User",
            "site_admin": False
        }
    },
    "sender": {
        "login": "owner",
        "id": 1,
        "node_id": "id",
        "gravatar_id": "",
        "type": "User",
        "site_admin": False
    }
}

push_headers = {
    "Content-Type": "application/json",
    "User-Agent": "GitHub-Hookshot/49beeff",
    "X-GitHub-Delivery": "23181600-55a4-11ea-95f3-651867586ba0",
    "X-GitHub-Event": "push",
    "X-Hub-Signature": "sha1=e422d9a5a3d93d96ca50edc7aa3d2f14d28715e2"
}

push_payload_without_urls = {
    "ref": "refs/heads/mybranch",
    "before": "0000000000000000000000000000000000000000",
    "after": "91fa363a384d5b4ac14b469847fdcb119112f139",
    "repository": {
        "id": 12345,
        "node_id": "MDEwOlJlcG9zaXRvcnkyMjY3Mjg3OTE=",
        "name": "repo",
        "full_name": "owner/repo",
        "private": False,
        "owner": {
            "name": "owner",
            "email": "trzcinska.ania@gmail.com",
            "login": "owner",
            "id": 1,
            "node_id": "MDQ6VXNlcjIxODIwNzg4",
            "avatar_url": "https://avatars3.githubusercontent.com/u/21820788?v=4",
            "gravatar_id": "",
            "type": "User",
            "site_admin": False
        },
        "description": None,
        "fork": False,
        "created_at": 1575837774,
        "updated_at": "2020-02-22T18:29:23Z",
        "pushed_at": 1582402785,
        "homepage": None,
        "size": 6,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": None,
        "has_issues": True,
        "has_projects": True,
        "has_downloads": True,
        "has_wiki": True,
        "has_pages": False,
        "forks_count": 0,
        "mirror_url": None,
        "archived": False,
        "disabled": False,
        "open_issues_count": 0,
        "license": None,
        "forks": 0,
        "open_issues": 0,
        "watchers": 0,
        "default_branch": "mybranch",
        "stargazers": 0,
        "master_branch": "mybranch"
    },
    "pusher": {
        "name": "owner",
        "email": "trzcinska.ania@gmail.com"
    },
    "sender": {
        "login": "owner",
        "id": 1,
        "node_id": "MDQ6VXNlcjIxODIwNzg4",
        "gravatar_id": "",
        "type": "User",
        "site_admin": False
    },
    "created": True,
    "deleted": False,
    "forced": False,
    "base_ref": None,
    "compare": "https://github.com/owner/repo/commit/91fa363a384d",
    "commits": [{
        "id": "91fa363a384d5b4ac14b469847fdcb119112f139",
        "tree_id": "ffd5a74459dee5294b9ff72d21fe4d6f163a9e3a",
        "distinct": True,
        "message": "Update a.txt",
        "timestamp": "2020-02-22T21:19:45+01:00",
        "url": "https://github.com/owner/repo/commit/91fa363a384d5b4ac14b469847fdcb119112f139",
        "author": {
            "name": "owner",
            "email": "trzcinska.ania@gmail.com",
            "username": "owner"
        },
        "committer": {
            "name": "GitHub",
            "email": "noreply@github.com",
            "username": "web-flow"
        },
        "added": [],
        "removed": [],
        "modified": ["dir/a.txt"]
    }],
    "head_commit": {
        "id": "91fa363a384d5b4ac14b469847fdcb119112f139",
        "tree_id": "ffd5a74459dee5294b9ff72d21fe4d6f163a9e3a",
        "distinct": True,
        "message": "Update a.txt",
        "timestamp": "2020-02-22T21:19:45+01:00",
        "author": {
            "name": "owner",
            "email": "owner@gmail.com",
            "username": "owner"
        },
        "committer": {
            "name": "GitHub",
            "email": "noreply@github.com",
            "username": "web-flow"
        },
        "added": [],
        "removed": [],
        "modified": ["dir/a.txt"]
    }
}

release_headers = {
    "Content-Type": "application/json",
    "User-Agent": "GitHub-Hookshot/49beeff",
    "X-GitHub-Delivery": "23181600-55a4-11ea-95f3-651867586ba0",
    "X-GitHub-Event": "release",
    "X-Hub-Signature": "sha1=68e6c578a6221a11abbc0656310f9438cd58cc06"
}

release_payload_without_urls = {
    "action": "released",
    "release": {
        "url": "https://api.github.com/repos/owner/test/releases/24037340",
        "assets_url": "https://api.github.com/repos/owner/test/releases/24037340/assets",
        "upload_url": "https://uploads.github.com/repos/owner/test/releases/24037340/assets{?name,label}",
        "html_url": "https://github.com/owner/test/releases/tag/v1.0.0",
        "id": 24037340,
        "node_id": "MDc6UmVsZWFzZTI0MDM3MzQw",
        "tag_name": "v1.0.0",
        "target_commitish": "mybranch",
        "name": "test release 1",
        "draft": False,
        "author": {
            "login": "owner",
            "id": 1,
            "node_id": "MDQ6VXNlcjIxODIwNzg4",
            "gravatar_id": "",
            "type": "User",
            "site_admin": False
        },
        "prerelease": False,
        "created_at": "2020-02-17T23:51:38Z",
        "published_at": "2020-02-27T12:46:39Z",
        "assets": [],
        "tarball_url": "https://api.github.com/repos/owner/test/tarball/v1.0.0",
        "zipball_url": "https://api.github.com/repos/owner/test/zipball/v1.0.0",
        "body": ""
    },
    "repository": {
        "id": 12345,
        "node_id": "MDEwOlJlcG9zaXRvcnkyMjY3MTYwMDE=",
        "name": "test",
        "full_name": "owner/test",
        "private": True,
        "owner": {
            "login": "owner",
            "id": 1,
            "node_id": "MDQ6VXNlcjIxODIwNzg4",
            "avatar_url": "https://avatars3.githubusercontent.com/u/21820788?v=4",
            "gravatar_id": "",
            "type": "User",
            "site_admin": False
        },
        "html_url": "https://github.com/owner/test",
        "description": None,
        "fork": False,
        "created_at": "2019-12-08T18:56:58Z",
        "updated_at": "2020-02-17T23:51:41Z",
        "pushed_at": "2020-02-27T12:46:39Z",
        "homepage": None,
        "size": 6,
        "stargazers_count": 0,
        "watchers_count": 0,
        "language": None,
        "has_issues": True,
        "has_projects": True,
        "has_downloads": True,
        "has_wiki": True,
        "has_pages": False,
        "forks_count": 0,
        "mirror_url": None,
        "archived": False,
        "disabled": False,
        "open_issues_count": 0,
        "license": None,
        "forks": 0,
        "open_issues": 0,
        "watchers": 0,
        "default_branch": "master"
    },
    "sender": {
        "login": "owner",
        "id": 1,
        "node_id": "MDQ6VXNlcjIxODIwNzg4",
        "gravatar_id": "",
        "type": "User",
        "site_admin": False
    }
}


def test_get_webhook_event_view_when_ping(client):
    resp = client.post('/repos/event',
                       headers=ping_headers,
                       data=json.dumps(ping_payload_without_urls))

    assert resp.status_code == 200
    assert resp.json == {'message': 'Got it.'}


@responses.activate
@patch.object(Github, 'get_repo')
def test_get_webhook_event_view_when_push_event(
        m_get_repo, deposit, client, github_push_webhook_sub, git_repo_tar):
    class MockProject(object):
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

        def get_archive_link(self, format, ref):
            assert format == 'tarball'
            assert ref == 'mybranchsha'
            return ('https://codeload.github.com/owner/repository/'
                    'legacy.tar.gz/mybranchsha')

    m_get_repo.return_value = MockProject()
    responses.add(responses.GET,
                  ('https://codeload.github.com/owner/repository/'
                   'legacy.tar.gz/mybranchsha'),
                  body=git_repo_tar,
                  content_type='application/x-gzip',
                  headers={
                      'Transfer-Encoding': 'chunked',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post('/repos/event',
                       headers=push_headers,
                       data=json.dumps(push_payload_without_urls))

    assert resp.status_code == 200
    assert resp.json == {'message': 'Snapshot of repository was saved.'}
    assert responses.calls[0].request.headers[
        'Authorization'] == 'token some-token'

    obj = ObjectVersion.get(
        deposit.files.bucket.id,
        'repositories/github.com/owner/repository/mybranch.tar.gz')

    tar_obj = tarfile.open(obj.file.uri)
    repo_file_name = tar_obj.getmembers()[1]
    repo_content = tar_obj.extractfile(repo_file_name).read()
    assert repo_content == b'test repo for cap\n'

    snapshot = github_push_webhook_sub.snapshots[0]
    assert obj.snapshot_id == snapshot.id
    assert GitSnapshot.query.count() == 1
    assert snapshot.payload == {
        'link': 'https://github.com/owner/repo/commit/91fa363a384d5b4ac14b469847fdcb119112f139',
        'event_type': 'push',
        'commit': [{
            'id': '91fa363a384d5b4ac14b469847fdcb119112f139',
            'message': 'Update a.txt',
            'added': [],
            'removed': [],
            'modified': ['dir/a.txt']
        }],
        'branch': 'mybranch',
        'author': {'name': 'owner', 'id': 1}
    }


@responses.activate
@patch.object(Github, 'get_repo')
def test_get_webhook_event_view_when_release_event(m_get_repo, deposit, client,
                                                   github_release_webhook_sub,
                                                   git_repo_tar):
    class MockProject(object):
        @property
        def default_branch(self):
            return 'def-branch'

        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

        def get_archive_link(self, format, ref):
            assert format == 'tarball'
            assert ref == 'mybranchsha'
            return ('https://codeload.github.com/owner/repository/'
                    'legacy.tar.gz/mybranchsha')

    m_get_repo.return_value = MockProject()
    responses.add(responses.GET,
                  ('https://codeload.github.com/owner/repository/'
                   'legacy.tar.gz/mybranchsha'),
                  body=git_repo_tar,
                  content_type='application/x-gzip',
                  headers={
                      'Transfer-Encoding': 'chunked',
                      'Content-Length': '287'
                  },
                  stream=True,
                  status=200)

    resp = client.post('/repos/event',
                       headers=release_headers,
                       data=json.dumps(release_payload_without_urls))

    assert resp.status_code == 200
    assert resp.json == {'message': 'Snapshot of repository was saved.'}
    assert responses.calls[0].request.headers[
        'Authorization'] == 'token some-token'

    obj = ObjectVersion.get(deposit.files.bucket.id,
                            'repositories/github.com/owner/repository/v1.0.0.tar.gz')

    tar_obj = tarfile.open(obj.file.uri)
    repo_file_name = tar_obj.getmembers()[1]
    repo_content = tar_obj.extractfile(repo_file_name).read()
    assert repo_content == b'test repo for cap\n'

    snapshot = github_release_webhook_sub.snapshots[0]
    assert obj.snapshot_id == snapshot.id
    assert GitSnapshot.query.count() == 1
    assert snapshot.payload == {
        'event_type': 'release',
        'author': {
            'name': 'owner',
            'id': 1
        },
        'link': 'https://github.com/owner/test/releases/tag/v1.0.0',
        'release': {
            'tag': 'v1.0.0',
            'name': 'test release 1'
        }
    }


def test_get_webhook_event_view_when_push_event_has_no_commits_throws_400(
        deposit, client, github_push_webhook_sub, git_repo_tar):

    push_payload_without_urls['commits'] = []
    resp = client.post('/repos/event',
                       headers=push_headers,
                       data=json.dumps(push_payload_without_urls))

    assert resp.status_code == 400
    assert resp.json == {
        'message': 'Server was unable to serialize this request',
        'status': 400
    }
