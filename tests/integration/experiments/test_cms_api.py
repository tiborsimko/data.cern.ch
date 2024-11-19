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

from unittest.mock import patch
from pytest import mark

from cap.modules.experiments.errors import ExternalAPIException


################
# api/cms/cadi
################
def test_get_cms_cadi_when_user_from_outside_cms_returns_403(
        client, users, auth_headers_for_user):
    resp = client.get('/cms/cadi/EXO-17-023',
                      headers=auth_headers_for_user(users['lhcb_user']))

    assert resp.status_code == 403


@patch('cap.modules.experiments.views.cms.get_from_cadi_by_id',
       return_value={})
def test_get_cms_cadi_when_cms_user_returns_200(mock_get_from_cadi_by_id,
                                                client, users,
                                                auth_headers_for_user):
    resp = client.get('/cms/cadi/ANA-00-001',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.status_code == 200


@patch('cap.modules.experiments.views.cms.get_from_cadi_by_id',
       return_value={})
def test_get_cms_cadi_when_non_existing_cadi_number_returns_empty_object(
        mock_get_from_cadi_by_id, client, auth_headers_for_superuser):
    resp = client.get('/cms/cadi/ABC-12-1234',
                      headers=auth_headers_for_superuser)

    assert resp.json == {}


@patch('cap.modules.experiments.views.cms.get_from_cadi_by_id')
def test_get_cms_cadi_when_existing_cadi_number_returns_object_with_parsed_data(
        mock_get_from_cadi_by_id, client, auth_headers_for_superuser):
    cadi_response = {
        'conference': '',
        'conferenceStatus': '',
        'code': 'ANA-00-000',
        'targetConference': None,
        'approvalTalk': 'https://indico.cern.ch/event/event.pdf',
        'creationDate': '2014-02-05',
        'updateDate': '2014-07-26',
        'pas': 'http://cms.cern.ch:80/pas.pdf',
        'id': 1,
        'targetPubPeriod': None,
        'targetDatePreApp': '19/12/2014',
        'papertar': 'http://cms.cern.ch:80/paper.tgz',
        'awg': 'HIG',
        'contact': {
            'cmsId': 1234,
            'hrId': 5678,
            'username': 'contact.user',
            'email': 'contact.user@example.com'
        },
        'creator': {
            'cmsId': 4321,
            'hrId': 8765,
            'username': 'creator.user',
            'email': 'creator.user@example.com'
        },
        'updater': {
            'cmsId': 4583,
            'hrId': 411861,
            'username': 'updater.user',
            'email': 'updater.user@example.com'
        },
        'relatedNotesInfo': [{
            'noteId':
            'CMS AN-2014/000',
            'url':
            'http://cms.cern.ch/noteInfo.jsp?cmsnoteid=CMS+AN-2014%2F000'
        }, {
            'noteId':
            'CMS AN-2013/000',
            'url':
            'http://cms.cern.ch/noteInfo.jsp?cmsnoteid=CMS+AN-2013%2F000'
        }],
        'status': 'PUB',
        'url': 'https://twiki.cern.ch/twikiurl',
        'creatorName': 'Creator User',
        'publicationStatus': 'Free',
        'paper': 'http://cms.cern.ch:80/paper.pdf',
        'description': 'Projections for 2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh) in 3000 fb-1',
        'name': '2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh)',
        'hepData': '',
    }
    mock_get_from_cadi_by_id.return_value = cadi_response

    resp = client.get('/cms/cadi/ANA-00-000',
                      headers=auth_headers_for_superuser)

    mock_get_from_cadi_by_id.assert_called_with('ANA-00-000')

    assert resp.json == {
        'description':
        'Projections for 2HDM Higgs studies (H->ZZ and A->Zh) in 3000 fb-1',
        'name':
        '2HDM Higgs studies (H->ZZ and A->Zh)',
        'contact':
        'contact.user@example.com',
        'creator':
        'creator.user@example.com',
        'updater':
        'updater.user@example.com',
        'created':
        '2014-02-05',
        'updated': '2014-07-26',
        'twiki':
        'https://twiki.cern.ch/twikiurl',
        'paper':
        'http://cms.cern.ch:80/paper.pdf',
        'paper_tar':
        'http://cms.cern.ch:80/paper.tgz',
        'pas':
        'http://cms.cern.ch:80/pas.pdf',
        'awg':
        'HIG',
        'publication_status':
        'Free',
        'status':
        'PUB',
        'cadi_id':
        'ANA-00-000',
        'conference':
        '',
        'hepData':
        '',
        'relatedNotes': [{
            'id':
            'AN-2014/000',
            'url':
            'http://cms.cern.ch/noteInfo.jsp?cmsnoteid=CMS+AN-2014%2F000'
        }, {
            'id':
            'AN-2013/000',
            'url':
            'http://cms.cern.ch/noteInfo.jsp?cmsnoteid=CMS+AN-2013%2F000'
        }]
    }


@patch('cap.modules.experiments.views.cms.get_from_cadi_by_id',
       side_effect=ExternalAPIException())
def test_get_cms_cadi_when_cadi_server_replied_with_an_error_returns_503(
        mock_get_from_cadi_by_id, app, auth_headers_for_superuser):
    with app.test_client() as client:
        resp = client.get('/cms/cadi/ABC-12-1234',
                          headers=auth_headers_for_superuser)

    assert resp.status_code == 503


def test_get_cms_cadi_when_cadi_not_matches_regex(app,
                                                  auth_headers_for_superuser):
    with app.test_client() as client:
        resp = client.get('/cms/cadi/ABC-12-ABC',
                          headers=auth_headers_for_superuser)

    assert resp.status_code == 400
    assert resp.json == {
        "message": "This CADI ID is invalid. Please provide an "
        "input in the form of [A-Z0-9]{3}-[0-9]{2}-[0-9]{3}",
        "status": 400
    }


############################
# api/cms/datasets - new API
############################
def test_get_datasets_suggestions_when_user_from_outside_cms_returns_403(
        client, users, auth_headers_for_user):
    headers = auth_headers_for_user(users['lhcb_user'])

    resp = client.get('/cms/mc-datasets?query=q', headers=headers)
    assert resp.status_code == 403

    resp = client.get('/cms/primary-datasets?query=q', headers=headers)
    assert resp.status_code == 403


def test_get_datasets_suggestions_when_cms_user_returns_200(
        client, users, auth_headers_for_user, das_datasets_index):
    headers = auth_headers_for_user(users['cms_user'])

    resp = client.get('/cms/primary-datasets?query=q', headers=headers)
    assert resp.status_code == 200

    resp = client.get('/cms/mc-datasets?query=q', headers=headers)
    assert resp.status_code == 200


def test_get_datasets_suggestions_when_no_query_passed_returns_empty_list(
        client, users, auth_headers_for_user, das_datasets_index):
    headers = auth_headers_for_user(users['cms_user'])

    resp = client.get('/cms/mc-datasets?query=', headers=headers)
    assert resp.json == []

    resp = client.get('/cms/primary-datasets?query=', headers=headers)
    assert resp.json == []

@mark.skip("@use_args decorator raises Validation Error if no args")
def test_get_datasets_suggestions_when_no_query_arg_returns_400(
        client, users, auth_headers_for_user, das_datasets_index):
    headers = auth_headers_for_user(users['cms_user'])

    resp = client.get('/cms/mc-datasets', headers=headers)
    assert resp.status_code == 400
    assert resp.json['message'] == {
        "query": ["Missing data for required field."]
    }

    resp = client.get('/cms/primary-datasets', headers=headers)
    assert resp.status_code == 400
    assert resp.json['message'] == {
        "query": ["Missing data for required field."]
    }


def test_get_primary_datasets_suggestions_returns_correct_suggestions(
        client, users, auth_headers_for_user, das_datasets_index):
    headers = auth_headers_for_user(users['cms_user'])

    resp = client.get('/cms/primary-datasets?query=/datas*', headers=headers)
    assert sorted(resp.json) == sorted([
        '/dataset1/run1/AOD', '/dataset1/run2/AOD', '/dataset2/run1/RECO',
        '/dataset2/run2/RECO', '/dataset5/run1/ALCARECO'
    ])

    resp = client.get('/cms/primary-datasets?query=/dataset*/run2',
                      headers=headers)
    assert sorted(resp.json) == sorted(
        ['/dataset1/run2/AOD', '/dataset2/run2/RECO'])

    # empty
    resp = client.get('/cms/primary-datasets?query=/datasets', headers=headers)
    assert resp.json == []


def test_get_mc_datasets_suggestions_returns_correct_suggestions(
        client, users, auth_headers_for_user, das_datasets_index):
    headers = auth_headers_for_user(users['cms_user'])

    resp = client.get('/cms/mc-datasets?query=/datas*', headers=headers)
    assert sorted(resp.json) == sorted([
        '/dataset3/run1/AODSIM', '/dataset3/run2/AODSIM',
        '/dataset4/run1/AODSIM', '/dataset4/run2/AODSIM',
        '/dataset6/run1/SIM-GEN-AOD'
    ])

    resp = client.get('/cms/mc-datasets?query=/dataset*/run2', headers=headers)
    assert sorted(resp.json) == sorted(
        ['/dataset3/run2/AODSIM', '/dataset4/run2/AODSIM'])

    # empty
    resp = client.get('/cms/mc-datasets?query=/datasets', headers=headers)
    assert resp.json == []


###############################
# api/cms/datasets - main API
###############################
def test_get_main_datasets_suggestions_when_user_from_outside_cms_returns_403(
        client, users, auth_headers_for_user):
    resp = client.get('/cms/datasets?query=q',
                      headers=auth_headers_for_user(users['lhcb_user']))

    assert resp.status_code == 403


def test_get_main_datasets_suggestions_when_cms_user_returns_200(
        client, users, auth_headers_for_user, das_datasets_index_main):
    resp = client.get('/cms/datasets?query=q',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.status_code == 200


def test_get_main_datasets_suggestions_when_no_query_passed_returns_empty_list(
        client, users, auth_headers_for_user, das_datasets_index_main):
    resp = client.get('/cms/datasets?query=',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == []

@mark.skip("@use_args decorator raises Validation Error if no args")
def test_get_main_datasets_suggestions_when_no_query_arg_returns_400(
        client, users, auth_headers_for_user, das_datasets_index):
    headers = auth_headers_for_user(users['cms_user'])

    resp = client.get('/cms/datasets', headers=headers)
    assert resp.status_code == 400
    assert resp.json['message'] == {
        "query": ["Missing data for required field."]
    }


def test_get_main_datasets_suggestions_returns_correct_suggestions(
        client, users, auth_headers_for_user, das_datasets_index_main):
    resp = client.get('/cms/datasets?query=/datas*',
                      headers=auth_headers_for_user(users['cms_user']))

    assert sorted(resp.json) == sorted(
        ['/dataset1/run1', '/dataset2', '/dataset1/run2'])

    resp = client.get('/cms/datasets?query=/dataset*/run',
                      headers=auth_headers_for_user(users['cms_user']))

    assert sorted(resp.json) == sorted(['/dataset1/run1', '/dataset1/run2'])

    resp = client.get('/cms/datasets?query=/datasets',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == []

    resp = client.get('/cms/datasets?query=*other_',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == ['/another_dataset']


##################
# api/cms/triggers
##################
def test_get_triggers_suggestions_when_user_from_outside_cms_returns_403(
        client, users, auth_headers_for_user):
    resp = client.get('/cms/triggers?query=q&dataset=D',
                      headers=auth_headers_for_user(users['lhcb_user']))

    assert resp.status_code == 403


def test_get_triggers_suggestions_when_cms_user_returns_200(
        client, users, auth_headers_for_user, cms_triggers_index):
    resp = client.get('/cms/triggers?query=q&dataset=D',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.status_code == 200


def test_get_triggers_suggestions_when_no_query_passed_returns_empty_list(
        client, users, auth_headers_for_user, cms_triggers_index):
    resp = client.get('/cms/triggers?query=&dataset=D',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == []


def test_get_triggers_suggestions_when_no_query_or_dataset_passed_returns_all(
        client, users, auth_headers_for_user, cms_triggers_index):
    resp = client.get('/cms/triggers?query=&dataset=',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == sorted([
        'Another_Trigger', 'Trigger2', 'Another_One', 'Trigger1', 'Trigger_2'
    ])


def test_get_triggers_suggestions_when_missing_params_throws_400(
        client, users, auth_headers_for_user, cms_triggers_index):
    resp = client.get('/cms/triggers',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.status_code == 400


def test_get_triggers_suggestions_returns_correct_suggestions(
        client, users, auth_headers_for_user, cms_triggers_index):
    resp = client.get('/cms/triggers?query=Sss&dataset=/Dataset1/sth/sth/sth',
                      headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == []

    resp = client.get(
        '/cms/triggers?query=trigg&dataset=/Dataset1/sth/sth/sth',
        headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == sorted(['Trigger1', 'Trigger_2'])

    resp = client.get(
        '/cms/triggers?query=T&dataset=/Dataset1/sth/sth/sth&year=2012',
        headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == ['Trigger_2']

    resp = client.get(
        '/cms/triggers?query=T&dataset=/Dataset1/sth/sth/sth&year=2013',
        headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == []

    resp = client.get(
        '/cms/triggers?query=Another&dataset=Dataset1/sth/sth/sth',
        headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == ['Another_Trigger']

    resp = client.get(
        '/cms/triggers?query=Trigger1&dataset=/Dataset2/sth/sth/sth',
        headers=auth_headers_for_user(users['cms_user']))

    assert resp.json == ['Trigger1']
