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

"""Models for Git repositories and snapshots."""

from __future__ import absolute_import, print_function

from invenio_db import db
from invenio_accounts.models import User
from invenio_records.models import RecordMetadata

from sqlalchemy_utils.types import UUIDType

from cap.types import json_type
from cap.modules.auth.ext import _fetch_token


class GitRepository(db.Model):
    """Information about a GitHub repository."""

    __tablename__ = 'git_connected_repositories'
    __table_args__ = (db.UniqueConstraint('record_uuid', 'repo_id', 'branch',
                                          name='unique_ids_constraint'),)

    id = db.Column(db.Integer, primary_key=True)
    repo_id = db.Column(db.Integer, unique=False, index=True)

    # CAP relations
    record_uuid = db.Column(UUIDType, db.ForeignKey(RecordMetadata.id))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    # git specific attributes
    url = db.Column(db.String(255), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(255), nullable=False, default='master')

    # enable/disable the hook through this field (hook id)
    hook = db.Column(db.String(255), nullable=True)
    hook_secret = db.Column(db.String(32), nullable=True)

    # check if the repo should be downloaded every time an event occurs
    # do not remove create_constraint, sqlalchemy bug workaround
    download = db.Column(db.Boolean(create_constraint=False),
                         nullable=False, default=False)

    user = db.relationship(User)
    record = db.relationship(
        RecordMetadata,
        backref=db.backref("repositories", cascade="all, delete-orphan")
    )

    @classmethod
    def create_or_get(cls, user_id, record_id, data_url,        # generic attrs
                      repo_id, host, owner, repo_name, branch,  # git attrs
                      download=False):
        """Create a new repository instance, using the API information."""
        repo = cls.get_by(repo_id, branch=branch)

        if not repo:
            # avoid celery trouble with serializing
            user = User.query.filter_by(id=user_id).one()
            repo = cls(repo_id=repo_id,
                       host=host, owner=owner,
                       name=repo_name, branch=branch,
                       url=data_url,
                       record_uuid=record_id,
                       user=user,
                       download=download)
        return repo

    @classmethod
    def get_by(cls, repo_id, branch='master'):
        """Get a repo by its ID and branch if available."""
        return cls.query.filter(cls.repo_id == repo_id,
                                cls.branch == branch).first()

    def __repr__(self):
        """Get repository representation."""
        return '<Repository {self.name}: {self.repo_id}>'.format(self=self)


class GitRepositorySnapshots(db.Model):
    """Snapshot information for a Git repo."""

    __tablename__ = 'git_repository_snapshots'

    id = db.Column(db.Integer, primary_key=True)

    # webhook payload / event
    event_payload = db.Column(json_type, default={}, nullable=True)
    event_type = db.Column(db.String(255), nullable=False)

    # git specifics
    tag = db.Column(db.String(255), nullable=True)
    ref = db.Column(db.String(255), nullable=True)

    # foreign keys (connecting to repo and events)
    repo_id = db.Column(db.Integer, db.ForeignKey(GitRepository.id))
    repo = db.relationship(
        GitRepository,
        backref=db.backref("snapshots", cascade="all, delete-orphan")
    )

    @staticmethod
    def create(event, data, repo, ref=None):
        snapshot = GitRepositorySnapshots(event_type=event, event_payload=data,
                                          tag=data['commit'].get('tag'),
                                          ref=ref, repo=repo)
        db.session.add(snapshot)
        db.session.commit()

    @property
    def download_url(self):
        if 'github' in self.repo.host:
            return 'https://codeload.github.com/{self.repo.owner}/' \
                   '{self.repo.name}/legacy.tar.gz/{self.ref}'\
                .format(self=self)
        else:
            token = _fetch_token('gitlab', self.repo.user_id)
            return 'https://gitlab.cern.ch/api/v4/projects/' \
                   '{self.repo.repo_id}/repository/archive?' \
                   'sha={self.ref}&access_token={token}' \
                .format(self=self, token=token)

    def __repr__(self):
        """Get repository representation."""
        return """
        <Repository {self.repo.name}: {self.repo.repo_id}
         event:\t{self.event_type}
         tags:\t{self.tag}
         url:\t{self.url}
        """.format(self=self)
