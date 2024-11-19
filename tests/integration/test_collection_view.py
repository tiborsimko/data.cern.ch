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
"""Integration tests for collection views."""
from __future__ import absolute_import, print_function

import json

from invenio_search import current_search
from pytest import mark


def test_collection_view_returns_user_drafts(location, client, users, create_deposit,
                                            auth_headers_for_user):
    my_deposit = create_deposit(users['lhcb_user'], 'lhcb', version="0.2.0")
    user_published_deposit = create_deposit(users['lhcb_user'],
                                            'lhcb',version='0.2.0',
                                            publish=True)
    other_user_deposit = create_deposit(users['lhcb_user2'], 'lhcb', version="0.1.2")

    resp = client.get('/collection/lhcb/0.2.0',
                      headers=auth_headers_for_user(users['lhcb_user']))
    user_drafts = [x['id'] for x in resp.json['user_drafts']['data']]

    assert len(user_drafts) == 1
    assert my_deposit['_deposit']['id'] in user_drafts
    assert user_published_deposit['_deposit']['id'] not in user_drafts
    assert other_user_deposit['_deposit']['id'] not in user_drafts


def test_collection_view_returns_user_published_analysis(
        client, users, create_deposit, auth_headers_for_user):
    my_deposit = create_deposit(users['lhcb_user'],
                                'lhcb',
                                experiment='LHCb',
                                version="0.2.0"
                                )
    user_published_deposit = create_deposit(users['lhcb_user'],
                                            'lhcb',
                                            experiment='LHCb',
                                            publish=True,
                                            version="0.2.0"
                                            )
    other_user_deposit = create_deposit(users['lhcb_user2'],
                                        'lhcb',
                                        experiment='LHCb',
                                        version="1.2.0"
                                        )
    other_user_published_deposit = create_deposit(users['lhcb_user2'],
                                                  'lhcb',
                                                  experiment='LHCb',
                                                  publish=True, version="1.2.1")

    resp = client.get('/collection/lhcb/0.2.0',
                      headers=auth_headers_for_user(users['lhcb_user']))
    user_published = [x['id'] for x in resp.json['user_published']['data']]

    assert len(user_published) == 1
    assert user_published_deposit['control_number'] in user_published
    assert my_deposit['_deposit']['id'] not in user_published
    assert other_user_deposit['_deposit']['id'] not in user_published
    assert other_user_published_deposit['control_number'] not in user_published


def test_collection_view_returns_publishedoration(
        client, users, create_deposit, auth_headers_for_user):
    my_deposit = create_deposit(users['lhcb_user'],
                                'lhcb',
                                experiment='LHCb',
                                version="0.2.0"
                                )
    user_published_deposit = create_deposit(users['lhcb_user'],
                                            'lhcb',
                                            publish=True,
                                            experiment='LHCb',
                                            version="0.2.0"
                                            )
    published_by_member_of_collab = create_deposit(users['lhcb_user2'],
                                                   'lhcb',
                                                   publish=True,
                                                   experiment='LHCb',
                                                   version="1.2.0"
                                                   )
    published_by_another_collab = create_deposit(users['cms_user'],
                                                 'cms',
                                                 publish=True,
                                                 experiment='CMS',
                                                 version="1.2.0")

    resp = client.get('/collection/lhcb/0.2.0',
                      headers=auth_headers_for_user(users['lhcb_user']))
    published = [
        x['id'] for x in resp.json['published']['data']
    ]

    assert len(published) == 2
    assert my_deposit['_deposit']['id'] not in published
    assert user_published_deposit['control_number'] in published
    assert published_by_member_of_collab[
        'control_number'] in published
    assert published_by_another_collab[
        'control_number'] not in published


def test_collection_view_returns_publishedoration(
        client, users, create_deposit, auth_headers_for_user):
    my_deposit = create_deposit(users['lhcb_user'],
                                'lhcb',
                                experiment='LHCb',
                                version="0.2.0"
                                )
    user_published_deposit = create_deposit(users['lhcb_user'],
                                            'lhcb',
                                            publish=True, version="0.2.0")
    published_by_member_of_collab = create_deposit(users['lhcb_user2'],
                                                   'lhcb',
                                                   publish=True, version="0.2.0")
    published_by_another_collab = create_deposit(users['cms_user'],
                                                 'cms',
                                                 experiment='CMS',
                                                 publish=True, version="0.2.0")

    resp = client.get('/collection/lhcb/0.2.0',
                      headers=auth_headers_for_user(users['lhcb_user']))
    published = [
        x['id'] for x in resp.json['published']['data']
    ]

    assert len(published) == 2
    assert my_deposit['_deposit']['id'] not in published
    assert user_published_deposit['control_number'] in published
    assert published_by_member_of_collab[
        'control_number'] in published
    assert published_by_another_collab[
        'control_number'] not in published


@mark.parametrize("action", [("deposit-read"), ("deposit-admin")])
def test_collection_view_returns_drafts(action, client, users,
                                                 create_deposit, json_headers,
                                                 auth_headers_for_user):
    user, other_user = users['lhcb_user'], users['lhcb_user2']
    my_deposit = create_deposit(user, 'lhcb', experiment='LHCb', version="1.0.0")
    user_published_deposit = create_deposit(user, 'lhcb', publish=True, version="1.0.0")
    other_user_deposit = create_deposit(other_user, 'lhcb', version="1.0.0")
    permissions = [{
        'email': user.email,
        'type': 'user',
        'op': 'add',
        'action': action
    }]

    client.post('/deposits/{}/actions/permissions'.format(
        other_user_deposit['_deposit']['id']),
                headers=auth_headers_for_user(other_user) + json_headers,
                data=json.dumps(permissions))
    current_search.flush_and_refresh('deposits')

    resp = client.get('/collection/lhcb/1.0.0', headers=auth_headers_for_user(user))
    drafts = [x['id'] for x in resp.json['drafts']['data']]

    assert len(drafts) == 2
    assert my_deposit['_deposit']['id'] in drafts
    assert user_published_deposit['control_number'] not in drafts
    assert other_user_deposit['_deposit']['id'] in drafts

def test_collection_view_error_handling(client, users,create_deposit,auth_headers_for_user):
    # provide a collection group that does not exists
    # this covers also the case for a typo when manually provided the url
    resp = client.get('/collection/cms-stats',
                      headers=auth_headers_for_user(users['cms_user']))
    assert resp.status_code == 404
    # check that someone from the lhcb experiment will not have access to the cms analysis
    create_deposit(users['lhcb_user'], 'lhcb',experiment='LHCb', version="0.2.0")
    resp = client.get('/collection/lhcb',
                      headers=auth_headers_for_user(users['cms_user']))
    assert resp.status_code == 403



def test_collection_view_fetching_properly_results(client, users,create_deposit,auth_headers_for_user):
    # create 2 drafts for cms
    cms_v1_deposit_1 = create_deposit(users['cms_user'], 'cms-stats-questionnaire', version="0.2.0")
    cms_v1_deposit_2 = create_deposit(users['cms_user'], 'cms-stats-questionnaire', version="0.2.0")

    # create 1 draft/published for cms
    cms_v2_deposit_2 = create_deposit(users['cms_user'], 'cms-stats-questionnaire', version="0.2.1")
    cms_v3_deposit_1 = create_deposit(users['cms_user'], 'cms-analysis', version="0.2.1")

    resp = client.get('/collection/cms-stats-questionnaire',
                      headers=auth_headers_for_user(users['cms_user']))
    cms_drafts = [x['id'] for x in resp.json['user_drafts']['data']]

    assert len(cms_drafts) == 3
    assert cms_v1_deposit_1['_deposit']['id'] in cms_drafts
    assert cms_v1_deposit_2['_deposit']['id'] in cms_drafts
    assert cms_v2_deposit_2['_deposit']['id'] in cms_drafts
    assert cms_v3_deposit_1['_deposit']['id'] not in cms_drafts

    resp = client.get('/collection/cms-stats-questionnaire/0.2.0',
                      headers=auth_headers_for_user(users['cms_user']))
    cms_drafts = [x['id'] for x in resp.json['user_drafts']['data']]

    assert len(cms_drafts) == 2
    assert cms_v1_deposit_1['_deposit']['id'] in cms_drafts
    assert cms_v1_deposit_2['_deposit']['id'] in cms_drafts
    assert cms_v2_deposit_2['_deposit']['id'] not in cms_drafts


def test_collections_view_for_schema_read_permission(app, db, client, users, create_deposit,
                                                    auth_headers_for_user, cli_runner, json_headers):
    superuser = users['superuser']
    lhcb_user = users['lhcb_user']

    superuser_headers = auth_headers_for_user(superuser) + json_headers
    test_headers = auth_headers_for_user(lhcb_user)

    # create schema
    schema_data = json.dumps(
        dict(name='test-schema', version='1.0.0',)
    )
    schema_resp = client.post('/jsonschemas/', data=schema_data, headers=superuser_headers)
    assert schema_resp.status_code == 200

    resp = client.get('/collection/test-schema',
                      headers=test_headers)
    assert resp.status_code == 403

    cli_runner(
        'fixtures permissions -p read -u lhcb_user@cern.ch --allow --deposit test-schema')

    resp = client.get('/collection/test-schema',
                      headers=test_headers)
    assert resp.status_code == 200
