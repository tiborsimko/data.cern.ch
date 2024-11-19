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

from flask import current_app
from werkzeug.local import LocalProxy

from conftest import add_role_to_user
from invenio_accounts.models import Role, User
from unittest.mock import MagicMock, patch
from pytest import mark

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

########################################
# api/deposits/{pid}/actions/permissions [POST]
########################################


@mark.parametrize("action", [("deposit-read"), ("deposit-update")])
def test_change_permissions_when_user_has_only_read_update_access_to_deposit_returns_403(
    action, client, users, auth_headers_for_user, create_deposit,
    json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': action
            },
        ]),
    )

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(other_user) + json_headers,
        data=json.dumps([]),
    )

    assert resp.status_code == 403


def test_change_permissions_when_user_has_admin_access_to_deposit_can_update_permissions(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-admin'
            },
        ]),
    )

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(other_user) + json_headers,
        data=json.dumps([]),
    )

    assert resp.status_code == 201


def test_change_permissions_when_superuser_can_update_others_deposits_permissions(
    client, users, auth_headers_for_superuser, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_superuser + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-update'
            },
        ]),
    )

    assert resp.status_code == 201


@patch('cap.modules.user.utils.does_user_exist_in_ldap',
       MagicMock(return_value=True))
def test_add_permissions_for_non_registered_user_registers_him_and_adds_permissions(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'cern.user@cern.ch',
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 201

    # now other user can see the deposit
    other_user = User.query.filter_by(email='cern.user@cern.ch').one()

    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 200


@patch('cap.modules.user.utils.does_user_exist_in_ldap',
       MagicMock(return_value=False))
def test_add_permissions_for_user_that_doesnt_exist_in_ldap_returns_400(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'non.cern.user@cern.ch',
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 400
    assert resp.json[
        'message'] == 'User with this mail does not exist in LDAP.'


def test_add_permissions_when_data_not_present_in_request(
    client, users, auth_headers_for_superuser, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_superuser + json_headers
    )

    assert resp.status_code == 400


def test_add_permissions_when_permission_already_exist_returns_400(
    client, users, auth_headers_for_superuser, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_superuser + json_headers,
        data=json.dumps([
            {
                'email': owner.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 400
    assert resp.json['message'] == 'Permission already exist.'


def test_add_permissions_when_permission_doesnt_exist_returns_400(
    client, users, auth_headers_for_superuser, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_superuser + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'remove',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 400
    assert resp.json['message'] == 'Permission does not exist.'


@mark.skip('to discuss if this should be done this way')
def test_add_permissions_when_add_admin_permissions_add_all_the_others_as_well(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': owner.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-admin'
            },
        ]),
    )


def test_add_ermissions_gives_permissions_for_user(client, users,
                                                   auth_headers_for_user,
                                                   create_deposit,
                                                   json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    # owner can see the deposit
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(owner),
    )

    assert resp.status_code == 200

    # other user cant see the deposit                          ,
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 403

    client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    # now other user can see the deposit
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 200

    # but other user still can't update the deposit
    resp = client.put(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user) + json_headers,
        data=json.dumps({}),
    )

    assert resp.status_code == 403

    client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-update'
            },
        ]),
    )

    # now user can update the deposit
    resp = client.put(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user) + json_headers,
        data=json.dumps({}),
    )

    assert resp.status_code == 200


def test_remove_permissions_for_user(client, users, auth_headers_for_user,
                                     create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-update'
            },
        ]),
    )

    # user can read/write the deposit
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user) + json_headers,
    )

    assert resp.status_code == 200

    # remove read/write permissions
    client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'remove',
                'action': 'deposit-read'
            },
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'remove',
                'action': 'deposit-update'
            },
        ]),
    )

    # user cant read/write the deposit anymore
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user) + json_headers,
    )

    assert resp.status_code == 403


@patch('cap.modules.user.utils.does_egroup_exist_in_ldap',
       MagicMock(return_value=True))
def test_add_permissions_for_non_registered_egroup_registers_it_and_adds_permissions(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['lhcb_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    # user can't see the deposit
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 403

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'cern.egroup@cern.ch',
                'type': 'egroup',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 201

    role = Role.query.filter_by(name='cern.egroup@cern.ch').one()
    _datastore.add_role_to_user(other_user, role)

    # now other user can see the deposit
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 200


@patch('cap.modules.user.utils.does_egroup_exist_in_ldap',
       MagicMock(return_value=False))
def test_add_permissions_for_egroup_that_doesnt_exist_in_ldap_returns_400(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'non.cern.egroup@cern.ch',
                'type': 'egroup',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 400
    assert resp.json[
        'message'] == 'Egroup with this mail does not exist in LDAP.'


@patch('cap.modules.user.utils.does_egroup_exist_in_ldap',
       MagicMock(return_value=True))
def test_change_permissions_for_egroup_is_not_case_sensitive(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner = users['cms_user']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'my-egroup@cern.ch',
                'type': 'egroup',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 201

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'My-EgrouP@cern.ch',
                'type': 'egroup',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 400
    assert resp.json['message'] == 'Permission already exist.'

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'My-EgrouP@cern.ch',
                'type': 'egroup',
                'op': 'remove',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 201


@patch('cap.modules.user.utils.does_user_exist_in_ldap',
       MagicMock(return_value=True))
def test_change_permissions_for_user_is_not_case_sensitive(
    client, users, auth_headers_for_user, create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email,
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 201

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email.upper(),
                'type': 'user',
                'op': 'add',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 400
    assert resp.json['message'] == 'Permission already exist.'

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': other_user.email.upper(),
                'type': 'user',
                'op': 'remove',
                'action': 'deposit-read'
            },
        ]),
    )

    assert resp.status_code == 201


def test_change_permissions_for_egroup(client, users, auth_headers_for_user,
                                       create_deposit, json_headers):
    owner, other_user = users['cms_user'], users['cms_user2']
    add_role_to_user(other_user, 'some-egroup@cern.ch')
    pid = create_deposit(owner, 'test-v1.0.0')['_deposit']['id']

    resp = client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'some-egroup@cern.ch',
                'type': 'egroup',
                'op': 'add',
                'action': 'deposit-read'
            },
            {
                'email': 'some-egroup@cern.ch',
                'type': 'egroup',
                'op': 'add',
                'action': 'deposit-update'
            },
        ]),
    )

    # user can read/write the deposit
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 200

    resp = client.put(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user) + json_headers,
        data=json.dumps({}),
    )

    assert resp.status_code == 200

    # remove read/write permissions
    client.post(
        f'/deposits/{pid}/actions/permissions',
        headers=auth_headers_for_user(owner) + json_headers,
        data=json.dumps([
            {
                'email': 'some-egroup@cern.ch',
                'type': 'egroup',
                'op': 'remove',
                'action': 'deposit-read'
            },
            {
                'email': 'some-egroup@cern.ch',
                'type': 'egroup',
                'op': 'remove',
                'action': 'deposit-update'
            },
        ]),
    )

    # user cant read/write the deposit anymore
    resp = client.get(
        f'/deposits/{pid}',
        headers=auth_headers_for_user(other_user),
    )

    assert resp.status_code == 403

    resp = client.put(
        f'/deposits/{pid}',
        data=json.dumps({}),
        headers=json_headers + auth_headers_for_user(other_user),
    )

    assert resp.status_code == 403
