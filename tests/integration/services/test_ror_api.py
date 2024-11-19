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

from invenio_rest.errors import RESTException
from unittest.mock import patch

from cap.modules.experiments.errors import ExternalAPIException

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


@patch('cap.modules.services.views.ror._ror')
def test_ror_by_query(mock_ror, app, auth_headers_for_superuser, json_headers):
    query_arg = 'tilburg'
    mock_ror.return_value = {
        'items': [{
            'acronyms': ['TiU'],
            'aliases': [],
            'id': 'https://ror.org/04b8v1s79',
            'country': {
                'country_code': 'NL',
                'country_name': 'Netherlands'
            },
            'external_ids': {
                'FundRef': {
                    'all': ['501100007659'],
                    'preferred': None
                },
                'GRID': {
                    'all': 'grid.12295.3d',
                    'preferred': 'grid.12295.3d'
                },
                'ISNI': {
                    'all': ['0000 0001 0943 3265'],
                    'preferred': None
                },
                'OrgRef': {
                    'all': ['1070237'],
                    'preferred': None
                },
                'Wikidata': {
                    'all': ['Q595668'],
                    'preferred': None
                }
            },
            'labels': [{
                'iso639': 'nl',
                'label': 'Universiteit van Tilburg'
            }],
            'links': ['https://www.tilburguniversity.edu/'],
            'name': 'Tilburg University',
            'types': ['Education'],
            'wikipedia_url': 'http://en.wikipedia.org/wiki/Tilburg_University'
        }],
        'meta': {
            'countries': [{
                'count': 1,
                'id': 'nl',
                'title': 'Kingdom of the Netherlands'
            }],
            'types': [{
                'count': 1,
                'id': 'education',
                'title': 'Education'
            }]
        },
        'number_of_results': 1,
        'time_taken': 4
    }, 200

    with app.test_client() as client:
        resp = client.get('services/ror?query={}'.format(query_arg),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.json == [{
            "acronyms": ["TiU"],
            "ror_org_id": "04b8v1s79",
            "name": "Tilburg University"
        }]


@patch('cap.modules.services.views.ror._ror')
def test_ror_by_query_returns_empty_list(mock_ror, app, auth_headers_for_superuser, json_headers):
    query_arg = 'bleh'
    mock_ror.return_value = {'items': [],
                             'time_taken': 4,
                             'number_of_results': 0,
                             'meta': {'types': [], 'countries': []}}, 200

    with app.test_client() as client:
        resp = client.get('services/ror?query={}'.format(query_arg),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 200
        assert resp.json == []


@patch('cap.modules.services.views.ror._ror', side_effect=ExternalAPIException())
def test_ror_by_query_returns_exception(mock_ror, app, auth_headers_for_superuser, json_headers):
    query_arg = '111'

    with app.test_client() as client:
        resp = client.get('services/ror?query={}'.format(query_arg),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 503
        assert resp.json['message'] == 'External API replied with an error.'


@patch('cap.modules.services.views.ror._ror',
       side_effect=RESTException(description='ROR Query not found.'))
def test_ror_by_query_empty_query(mock_ror, app, auth_headers_for_superuser,
                                  json_headers):

    with app.test_client() as client:
        resp = client.get('services/ror',
                          data=json.dumps({}),
                          headers=auth_headers_for_superuser + json_headers)
        assert resp.status_code == 200
        assert resp.json['message'] == 'ROR Query not found.'


@patch('cap.modules.services.views.ror._ror')
def test_ror_by_org(mock_ror, app, auth_headers_for_superuser, json_headers):
    mock_ror_id = '04b8v1s79'
    mock_ror.return_value = {
        'acronyms': ['TiU'],
        'aliases': [],
        'country': {
            'country_code': 'NL',
            'country_name': 'Netherlands'
        },
        'external_ids': {
            'FundRef': {
                'all': ['501100007659'],
                'preferred': None
            },
            'GRID': {
                'all': 'grid.12295.3d',
                'preferred': None
            },
            'ISNI': {
                'all': ['0000 0001 0943 3265'],
                'preferred': None
            },
            'OrgRef': {
                'all': ['1070237'],
                'preferred': None
            },
            'Wikidata': {
                'all': ['Q595668'],
                'preferred': None
            }
        },
        'id': 'https://ror.org/04b8v1s79',
        'name': 'Tilburg University',
        'labels': [{
            'iso639': 'nl',
            'label': 'Universiteit van Tilburg'
        }],
        'links': ['https://www.tilburguniversity.edu/'],
        'types': ['Education'],
        'wikipedia_url': 'http://en.wikipedia.org/wiki/Tilburg_University'
    }, 200

    with app.test_client() as client:
        resp = client.get('services/ror/{}'.format(mock_ror_id),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 200
        assert resp.json == {
            "acronyms": ["TiU"],
            "aliases": [],
            "types": ["Education"],
            "country": {
                "country_code": "NL",
                "country_name": "Netherlands"
            },
            "external_ids": {
                "FundRef": "501100007659",
                "GRID": "grid.12295.3d",
                "ISNI": "0000 0001 0943 3265",
                "OrgRef": "1070237",
                "Wikidata": "Q595668"
            },
            "labels": [{
                "iso639": "nl",
                "label": "Universiteit van Tilburg"
            }],
            "ror_org_id": "04b8v1s79",
            "name": "Tilburg University",
            "links": ["https://www.tilburguniversity.edu/"],
            "wikipedia_url": "http://en.wikipedia.org/wiki/Tilburg_University"
        }


@patch('cap.modules.services.views.ror._ror',
       side_effect=ExternalAPIException())
def test_ror_by_query_exception(mock_ror, app, auth_headers_for_superuser,
                                json_headers):
    mock_ror_id = '04b8v1s79'

    with app.test_client() as client:
        resp = client.get('services/ror/{}'.format(mock_ror_id),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 503
        assert resp.json['message'] == 'External API replied with an error.'


@patch('cap.modules.services.views.ror._ror', side_effect=ValueError())
def test_ror_by_query_empty_list_exception(mock_ror, app,
                                           auth_headers_for_superuser,
                                           json_headers):
    mock_ror_id = '11111'

    with app.test_client() as client:
        resp = client.get('services/ror/{}'.format(mock_ror_id),
                          headers=auth_headers_for_superuser + json_headers)

        assert resp.status_code == 404
        assert resp.json == {'message': 'Organization not found.'}
