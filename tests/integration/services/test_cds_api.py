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

"""Integration tests for CDS api."""

from __future__ import absolute_import, print_function
from unittest.mock import patch
import responses

from cap.modules.experiments.errors import ExternalAPIException


@patch('cap.modules.services.views.cds._cds')
def test_cds(mock_cds, app, auth_headers_for_superuser):
    mock_record = '11111'
    mock_cds.return_value = {
        '001': '2708468',
        '0247_': {'2': 'DOI', '9': 'SISSA', 'a': '10.22323/1.350.0103'},
        '035__': ({'9': 'http://inspirehep.net/oai2d',
                   'a': 'oai:inspirehep.net:1769926',
                   'h': '2020-02-04T07:05:15Z'},
                  {'9': 'Inspire', 'a': '1769926'}),
        '100__': {'a': 'Finco, Linda', 'u': 'Nebraska U.'},
        '245__': {'9': 'SISSA', 'a': 'Rare and exotic Higgs decays, including new scalars'},
        '520__': {'9': 'SISSA',
                  'a': 'The latest results in the search for rare and exotic Higgs boson decays are presented.'},
        '65017': ({'2': 'SzGeCERN', 'a': 'Particle Physics - Experiment'},
                  {'2': 'SzGeCERN', 'a': 'Particle Physics - Phenomenology'}),
        '710__': ({'g': 'ATLAS'},
                  {'g': 'CMS'}),
        '8564_': {'u': 'http://cds.cern.ch/record/2708468/files/PoS(LHCP2019)103.pdf',
                  'y': 'Fulltext'},
        '980__': ({'a': 'ARTICLE'},
                  {'a': 'ConferencePaper'})
    }, 200

    with app.test_client() as client:
        resp = client.get('services/cds/{}'.format(mock_record),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 200
        assert resp.json == {
            'abstract': 'The latest results in the search for rare and exotic Higgs boson decays are presented.',
            'authors': ['Finco, Linda'],
            'cds_id': '2708468',
            'files': [{'desc': 'Fulltext',
                       'url': 'http://cds.cern.ch/record/2708468/files/PoS(LHCP2019)103.pdf'}],
            'links': {'doi': '10.22323/1.350.0103',
                      'inspire': 'http://inspirehep.net/record/1769926'},
            'record_types': ['ARTICLE', 'ConferencePaper'],
            'subjects': ['Particle Physics - Experiment',
                         'Particle Physics - Phenomenology'],
            'title': 'Rare and exotic Higgs decays, including new scalars'
        }


@patch('cap.modules.services.views.cds._cds')
def test_cds_other(mock_cds, app, auth_headers_for_superuser):
    mock_record = '11111'
    mock_cds.return_value = {
        '001': '2285583',
        '037__': {'a': 'CERN-LHCC-2017-019'},
        '245__': {'a': 'Technical Design Report for the Phase-II Upgrade '
                       'of the ATLAS Tile Calorimeter'},
        '520__': {'a': 'This Technical Design Report describes the project to '
                       'upgrade the ATLAS Tile Calorimeter for the operation '
                       'at the High Luminosity LHC.'},
        '65017': {'2': 'SzGeCERN', 'a': 'Detectors and Experimental Techniques'},
        '710__': ({'a': 'CERN. Geneva. The LHC experiments Committee'}, {'5': 'PH'}),
        '8564_': ({'u': 'http://cds.cern.ch/record/2285583/files/ATLAS-TDR-028.pdf',
                   'y': 'Fulltext'},
                  {'u': 'http://cds.cern.ch/record/2285583/files/ATLAS-TDR-028.jpg?subformat=icon-180',
                   'x': 'icon-180'}),
        '980__': ({'a': 'SCICOMMPUBLLHCC'}, {'a': 'ATLAS_Reports'}, {'a': 'REPORT'})
    }, 200

    with app.test_client() as client:
        resp = client.get('services/cds/{}'.format(mock_record),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 200
        assert resp.json == {
            'cds_id': '2285583',
            'abstract': 'This Technical Design Report describes the project '
                        'to upgrade the ATLAS Tile Calorimeter for the operation '
                        'at the High Luminosity LHC.',
            'authors': ['CERN. Geneva. The LHC experiments Committee'],
            'files': [{'desc': 'Fulltext',
                       'url': 'http://cds.cern.ch/record/2285583/files/ATLAS-TDR-028.pdf'},
                      {'desc': None,
                       'url': 'http://cds.cern.ch/record/2285583/files/ATLAS-TDR-028.jpg?subformat=icon-180'}],
            'links': {},
            'record_types': ['SCICOMMPUBLLHCC', 'ATLAS_Reports', 'REPORT'],
            'subjects': ['Detectors and Experimental Techniques'],
            'title': 'Technical Design Report for the Phase-II Upgrade of the ATLAS Tile Calorimeter'
        }


@patch('cap.modules.services.views.cds._cds')
def test_cds_deleted_record(mock_cds, app, auth_headers_for_superuser):
    mock_record = '11111'
    mock_cds.return_value = {
        '001': '1',
        '980__': {'c': 'DELETED'}
    }, 200

    with app.test_client() as client:
        resp = client.get('services/cds/{}'.format(mock_record),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 400
        assert resp.json['message'] == 'The record was deleted from CDS.'


@responses.activate
def test_cds_unauthorized(app, auth_headers_for_superuser):
    mock_record = '111'
    responses.add(responses.GET,
                  'https://cds.cern.ch/record/{}/export/xm?ln=en'.format(mock_record),
                  body='<html>Test</html>',
                  headers={'Expires': '-1'},
                  status=200)

    with app.test_client() as client:
        resp = client.get('services/cds/{}'.format(mock_record),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 401
        assert resp.json['message'] == 'You are unauthorized to view this CDS record.'


@patch('cap.modules.services.views.cds._cds', side_effect=ExternalAPIException())
def test_cds_api_exception(mock_cds, app, auth_headers_for_superuser):
    mock_record = '11111'

    with app.test_client() as client:
        resp = client.get('services/cds/{}'.format(mock_record),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 503


@patch('cap.modules.services.views.cds._cds', side_effect=IndexError())
def test_cds_idx_exception(mock_cds, app, auth_headers_for_superuser):
    mock_record = '11111'

    with app.test_client() as client:
        resp = client.get('services/cds/{}'.format(mock_record),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 400
