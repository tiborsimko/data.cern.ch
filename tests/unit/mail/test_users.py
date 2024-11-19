# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2020 CERN.
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
"""Tests for mail."""
from unittest.mock import patch
from cap.modules.mail.users import get_all_users, get_users_by_record, \
    get_users_by_experiment
from cap.modules.mail.custom.recipients import get_owner, get_submitter


def test_get_all_user_mails(users):
    users = get_all_users()

    assert len(users) == 12


def test_get_users_by_record(app, db, users, create_deposit):
    user1 = users['alice_user']
    user2 = users['alice_user2']

    deposit = create_deposit(user1, 'alice-analysis-v0.0.1')
    deposit._add_user_permissions(
        user2,
        ['deposit-read'],
        db.session
    )
    depid = deposit['_deposit']['id']

    users_all = get_users_by_record(depid)
    assert len(users_all) == 2

    users_admin = get_users_by_record(depid, role='admin')
    assert len(users_admin) == 1

    users_read = get_users_by_record(depid, role='read')
    assert len(users_read) == 2


def test_get_user_by_experiment(remote_accounts):
    cms_users = get_users_by_experiment('cms')
    assert len(cms_users) == 2

    lhcb_users = get_users_by_experiment('lhcb')
    assert len(lhcb_users) == 1

    atlas_users = get_users_by_experiment('atlas')
    assert len(atlas_users) == 1

    alice_users = get_users_by_experiment('alice')
    assert len(alice_users) == 1


def test_get_current_user(app, db, users):
    user1 = users['alice_user']
    assert get_submitter(None,
        default_ctx={'submitter_id': user1.id}) == ['alice_user@cern.ch']


def test_get_record_owner(users, location, create_schema, create_deposit):
    user = users['cms_user']
    create_schema('test', experiment='CMS')
    deposit = create_deposit(
        user, 'test',
        experiment='CMS',
    )
    assert get_owner(deposit) == ['cms_user@cern.ch']
