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
"""Integration tests for atlas views."""
from __future__ import absolute_import, print_function

import responses
from flask import current_app
from unittest.mock import patch


@responses.activate
@patch('cap.modules.experiments.views.atlas.get_glance_token')
def test_get_glance_by_id(mock_get_token, client, auth_headers_for_superuser):
    access_token = 'some_token'
    glance_id = '111'
    glance_resp = {
        'count': 1,
        'links': [],
        'items': [{
            'status': 'phase0_closed',
            'gitlab_projects': [{
                'group_id': 00000,
                'link': 'https://gitlab.cern.ch/atlas/ANA-000'
            }],
            'phase0': [{
                'model_tested': 'Smart simulation',
                'main_physics_aim': 'Smart goal.',
                'dataset_used': 'Smart data',
                'methods': 'Very smart methods.'
            }],
            'pub_short_title': None,
            'short_title': 'Some smart analysis',
            'creation_date': '2018-02-15T13:14:44Z',
            'full_title': None,
            'refcode': 'ANA-00',
            'id': glance_id
        }],
        'hasMore': False,
        'offset': 0,
        'limit': 0
    }

    mock_get_token.return_value = access_token
    responses.add(
        responses.GET,
        current_app.config.get('GLANCE_GET_BY_ID_URL').format(id=glance_id),
        json=glance_resp,
        status=200)

    resp = client.get('/atlas/glance/{}'.format(glance_id),
                      headers=auth_headers_for_superuser)

    # check that requst to glance is called with correct url and access_token
    assert responses.calls[0].request.url == \
        'https://oraweb.cern.ch/ords/atlr/atlas_authdb/atlas/analysis/analysis/?client_name=cap&id={}'.format(
        glance_id)
    assert responses.calls[0].request.headers[
        'Authorization'] == 'Bearer {}'.format(access_token)

    # check the response
    assert resp.json == glance_resp['items'][0]


@responses.activate
@patch('cap.modules.experiments.views.atlas.get_glance_token')
def test_get_glance_by_id_when_glance_server_down_returns_503(
        mock_get_token, client, auth_headers_for_superuser):
    glance_id = '111'
    mock_get_token.return_value = 'some_token'
    responses.add(
        responses.GET,
        current_app.config.get('GLANCE_GET_BY_ID_URL').format(id=glance_id),
        json={'message': 'External server replied with an error.'},
        status=503)

    resp = client.get('/atlas/glance/{}'.format(glance_id),
                      headers=auth_headers_for_superuser)

    assert resp.status_code == 503
    assert resp.json['message'] == 'External server replied with an error.'


@patch('cap.modules.experiments.views.atlas.get_glance_token')
def test_get_glance_by_id_when_glance_server_doesnt_return_token_returns_503(
        mock_get_token, client, auth_headers_for_superuser):
    glance_id = '111'
    mock_get_token.return_value = None

    resp = client.get('/atlas/glance/{}'.format(glance_id),
                      headers=auth_headers_for_superuser)

    assert resp.status_code == 503
    assert resp.json['message'] == 'External server replied with an error.'
