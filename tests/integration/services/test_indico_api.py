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
import responses
from unittest.mock import patch

from cap.modules.experiments.errors import ExternalAPIException


@patch('cap.modules.services.views.indico._indico')
def test_indico_empty_list(mock_indico, app, auth_headers_for_superuser):
    mock_indico_id = '1111'
    mock_indico.return_value = {u'count': 0, u'additionalInfo': {}, u'_type': u'HTTPAPIResult',
                                u'url': u'https://indico.cern.ch/export/event/1111.json',
                                u'ts': 1568636014, u'results': []}, 200

    with app.test_client() as client:
        resp = client.get('services/indico/{}'.format(mock_indico_id), headers=auth_headers_for_superuser)

        assert resp.status_code == 200
        assert resp.json == []


@patch('cap.modules.services.views.indico._indico', side_effect=ExternalAPIException())
def test_indico_exception(mock_indico, app, auth_headers_for_superuser):
    mock_indico_id = '848989'

    with app.test_client() as client:
        resp = client.get('services/indico/{}'.format(mock_indico_id), headers=auth_headers_for_superuser)

        assert resp.status_code == 503
        assert resp.json['message'] == 'External API replied with an error.'


@responses.activate
def test_get_indico_by_event_id(app, auth_headers_for_superuser):
    indico_url = 'https://indico.cern.ch/export/event/{}.json'
    indico_event_id = '845525'
    indico_resp = {
        "count": 1, "additionalInfo": {}, "_type": "HTTPAPIResult", "ts": 1567434578,
        "url": "https:\/\/indico.cern.ch\/export\/event\/845525.json?pretty=yes",
        "results": [{
            "folders": [],
            "creationDate": {"date": "2019-09-02", "tz": "Europe/Zurich", "time": "16:28:54.167656"},
            "startDate":{"date": "2019-09-02", "tz": "Europe/Zurich", "time": "17:00:00"},
            "endDate": {"date": "2019-09-02", "tz": "Europe/Zurich", "time": "19:00:00"},
            "_type": "Conference", "hasAnyProtection": False, "description": "",
            "roomMapURL": "https:\/\/maps.cern.ch\/mapsearch\/mapsearch.htm?n=['3\/R-002']",
            "creator": {
                "affiliation": "", "_type": "Avatar", "last_name": "Koutsakis",
                "emailHash": "514487040d28517d3c94700dd987e10e",
                "_fossil": "conferenceChairMetadata", "fullName": "Koutsakis, Ilias",
                "first_name": "Ilias", "id": "77851"
            },
            "material": [], "note":{},
            "visibility":{"id": "", "name": "Everywhere"},
            "roomFullname": "3/R-002 - Teacher Training Room",
            "references": [], "address":"", "timezone": "Europe/Zurich",
            "id":"845525", "category":"TEST Category", "room":"3/R-002",
            "title":"cap-test-event", "url":"https://indico.cern.ch/event/845525/",
            "chairs": [{
              "person_id": 4680087, "affiliation": "CERN", "_type": "ConferenceChair",
              "last_name": "Fokianos", "db_id": 771323, "_fossil": "conferenceChairMetadata",
              "emailHash": "0bc625725a7099d0e24b738432077ba2",
              "fullName": "Fokianos, Pamfilos", "first_name": "Pamfilos", "id": "771323"
            }],
            "location": "CERN", "_fossil": "conferenceMetadata", "type": "simple_event", "categoryId": 2
        }]
    }

    responses.add(responses.GET,
                  indico_url.format(indico_event_id),
                  json=indico_resp, status=200)

    with app.test_client() as client:
        resp = client.get('/services/indico/{}'.format(indico_event_id),
                          headers=auth_headers_for_superuser)

        assert resp.status_code == 200
        assert resp.json['indico_event_id'] == indico_event_id
