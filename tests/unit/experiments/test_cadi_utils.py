# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016, 2017 CERN.
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
"""Tests for CADI utils methods."""

from __future__ import absolute_import

from flask import current_app

import responses
from cap.modules.deposit.errors import DepositDoesNotExist
from cap.modules.experiments.errors import ExternalAPIException
from cap.modules.experiments.serializers import CADISchema
from cap.modules.experiments.utils.cadi import (get_all_from_cadi,
                                                get_deposit_by_cadi_id,
                                                get_from_cadi_by_id,
                                                synchronize_cadi_entries)
from conftest import _datastore, assign_egroup_to_experiment
from invenio_accounts.testutils import create_test_user
from invenio_search import current_search
from ldap import LDAPError
from unittest.mock import patch, MagicMock
from pytest import raises


@responses.activate
@patch('cap.modules.experiments.utils.cadi.get_sso_cookie_for_cadi')
def test_get_from_cadi_by_id(mock_get_sso_cookie_for_cadi, app):
    cookie = dict(cookies_are='example_cookie')
    cadi_id = 'EXO-00-000'
    cadi_resp = {
        u'Conference': '',
        u'conferenceStatus': '',
        u'code': 'dEXO-00-000',
        u'targetConference': None,
        u'approvalTalk': 'https://indico.cern.ch/event/event.pdf',
        u'updaterDate': '24/12/2014',
        u'PAS': 'http://cms.cern.ch:80/pas.pdf',
        u'id': 1,
        u'updaterName': 'Updater User',
        u'targetPubPeriod': None,
        u'targetDatePreApp': '19/12/2014',
        u'PAPERTAR': 'http://cms.cern.ch:80/paper.tgz',
        u'contact': 'Contact User',
        u'status': 'PUB',
        u'description': 'Description',
        u'URL': 'https://twiki.cern.ch/twikiurl',
        u'creatorName': 'Creator User',
        u'publicationStatus': 'Free',
        u'name': 'Name',
        u'PAPER': 'http://cms.cern.ch:80/paper.pdf'
    }

    mock_get_sso_cookie_for_cadi.return_value = cookie
    responses.add(responses.GET,
                  current_app.config['CADI_GET_RECORD_URL'].format(id=cadi_id),
                  json=cadi_resp,
                  status=200)

    output = get_from_cadi_by_id(cadi_id)

    # check that requst to glance is called with correct url and cookie
    url = 'https://icms.cern.ch/tools-api/restplus/relay/' + \
          'piggyback/cadi/history/capInfo/{id}'.format(id=cadi_id)
    assert responses.calls[0].request.url == url
    assert responses.calls[0].request._cookies == cookie

    # check the response
    assert output == cadi_resp


@responses.activate
@patch('cap.modules.experiments.utils.cadi.generate_krb_cookie',
       MagicMock(return_value=dict(cookies_are='example_cookie')))
def test_get_from_cadi_by_id_when_no_entry_with_given_cadi_id_returns_empty_dict(
        app):
    cadi_id = 'non-existing'
    # CADI API returns empty list, when no match with given id
    cadi_resp = dict()

    responses.add(
        responses.GET,
        current_app.config['CADI_GET_RECORD_URL'].format(id='NON-EXISTING'),
        json=cadi_resp,
        status=200)

    output = get_from_cadi_by_id(cadi_id)

    # check the response
    assert output == {}


@responses.activate
@patch('cap.modules.experiments.utils.cadi.get_sso_cookie_for_cadi',
       MagicMock(return_value=dict(cookies_are='example_cookie')))
def test_get_from_cadi_by_id_when_cadi_server_down_returns_503(app):
    cadi_id = 'EXO-00-000'

    responses.add(responses.GET,
                  current_app.config['CADI_GET_RECORD_URL'].format(id=cadi_id),
                  status=500)

    with raises(ExternalAPIException):
        get_from_cadi_by_id(cadi_id)


@responses.activate
@patch('cap.modules.experiments.utils.cadi.get_sso_cookie_for_cadi',
       MagicMock(side_effect=ExternalAPIException()))
def test_get_from_cadi_by_id_when_cadi_server_down_while_asking_for_auth_returns_503(
        app):
    cadi_id = 'EXO-00-000'

    with raises(ExternalAPIException):
        get_from_cadi_by_id(cadi_id)


@responses.activate
@patch('cap.modules.experiments.utils.cadi.get_sso_cookie_for_cadi')
def test_get_all_from_cadi(mock_get_sso_cookie_for_cadi, app):
    cookie = dict(cookies_are='example_cookie')
    cadi_resp = dict(_embedded=dict(cadiLineCapInfoList=[
        dict(code=u'dEXO-00-001', status=u'Inactive'),
        dict(code=u'dEXO-00-002', status=u'PUB'),
        dict(code=u'dEXO-00-003', status=u'SUPERSEDED')
    ]))

    mock_get_sso_cookie_for_cadi.return_value = cookie
    responses.add(responses.GET,
                  current_app.config['CADI_GET_ALL_URL'],
                  json=cadi_resp,
                  status=200)

    output = list(get_all_from_cadi())

    # check that request to glance is called with correct url and cookie
    url = 'https://icms.cern.ch/tools-api/restplus/relay/piggyback/' + \
          'cadi/history/capInfo'
    assert responses.calls[0].request.url == url
    assert responses.calls[0].request._cookies == cookie

    # check that inactive|supseded analysis are not returned
    assert dict(code='dEXO-00-001', status='Inactive') not in output
    assert dict(code='dEXO-00-003', status='SUPERSEDED') not in output

    # check that inactive|supseded analysis are not returned
    assert output == [dict(code='dEXO-00-002', status='PUB')]


@responses.activate
@patch('cap.modules.experiments.utils.cadi.get_sso_cookie_for_cadi',
       MagicMock(return_value=dict(cookies_are='example_cookie')))
def test_get_all_from_cadi_when_cadi_server_down_returns_503(app):
    responses.add(responses.GET,
                  current_app.config['CADI_GET_ALL_URL'],
                  status=500)

    with raises(ExternalAPIException):
        get_all_from_cadi()


@responses.activate
@patch('cap.modules.experiments.utils.cadi.get_sso_cookie_for_cadi',
       MagicMock(side_effect=ExternalAPIException()))
def test_get_all_from_cadi_when_cadi_server_down_while_asking_for_auth_returns_503(
        app):
    with raises(ExternalAPIException):
        get_all_from_cadi()


def test_parse_cadi_entry():
    cadi_resp = {
        'conference':
        '',
        'conferenceStatus':
        '',
        'code':
        'ANA-00-000',
        'targetConference':
        None,
        'approvalTalk':
        'https://indico.cern.ch/event/event.pdf',
        'creationDate':
        '2014-02-05',
        'updateDate':
        '2014-07-26',
        'pas':
        'http://cms.cern.ch:80/pas.pdf',
        'id':
        1,
        'targetPubPeriod':
        None,
        'targetDatePreApp':
        '19/12/2014',
        'papertar':
        'http://cms.cern.ch:80/paper.tgz',
        'awg':
        'HIG',
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
        'status':
        'PUB',
        'url':
        'https://twiki.cern.ch/twikiurl',
        'creatorName':
        'Creator User',
        'publicationStatus':
        'Free',
        'paper':
        'http://cms.cern.ch:80/paper.pdf',
        'description':
        'Projections for 2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh) in 3000 fb-1',
        'name':
        '2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh)',
        'hepData':
        '',
    }

    serializer = CADISchema()
    parsed = serializer.dump(cadi_resp).data

    assert parsed == {
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
        'created': '2014-02-05',
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


def test_parse_cadi_entry_when_entry_missing_some_fields():
    cadi_resp = {
        u'code': 'EXO-00-000',
        u'paper': 'http://cms.cern.ch:80/paper.pdf',
        u'description':
        'Projections for 2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh) in 3000 fb-1',
        u'name': '2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh)'
    }

    serializer = CADISchema()
    parsed = serializer.dump(cadi_resp).data

    assert parsed == {
        'description':
        'Projections for 2HDM Higgs studies (H->ZZ and A->Zh) in 3000 fb-1',
        'name': '2HDM Higgs studies (H->ZZ and A->Zh)',
        'contact': '',
        'creator': '',
        'updater': '',
        'created': '',
        'updated': '',
        'twiki': '',
        'paper': 'http://cms.cern.ch:80/paper.pdf',
        'paper_tar': '',
        'pas': '',
        'hepData': '',
        'publication_status': '',
        'status': '',
        'cadi_id': 'EXO-00-000',
        'awg': '',
        'conference': ''
    }


def test_get_deposit_by_cadi_id_returns_correct_deposit(
        app, es, create_deposit, superuser):
    cadi_id = 'EXO-00-001'
    deposit = create_deposit(superuser,
                             'cms-analysis', {
                                 '$ana_type': 'cms-analysis',
                                 'basic_info': {
                                     'cadi_id': cadi_id
                                 }
                             },
                             mapping={
                                'mappings': {
                                    'properties': {
                                        "basic_info": {
                                            "type": "object",
                                            "properties": {
                                                "cadi_id": {
                                                    "type": "keyword"
                                                }
                                            }
                                        }
                                    }
                                }
                             })
    create_deposit(superuser, 'cms-analysis', {
        '$ana_type': 'cms-analysis',
        'basic_info': {
            'cadi_id': 'EXO-00-002'
        }
    })

    assert get_deposit_by_cadi_id(cadi_id) == deposit


def test_get_deposit_by_cadi_id_when_no_match_raises_DepositDoesNotExist(
        app, es, create_deposit, superuser):
    create_deposit(superuser,
                   'cms-analysis', {
                       '$ana_type': 'cms-analysis',
                       'basic_info': {
                           'cadi_id': 'EXO-00-001'
                       }
                   },
                   mapping={
                       'mappings': {
                            'properties': {
                                "basic_info": {
                                    "type": "object",
                                    "properties": {
                                        "cadi_id": {
                                            "type": "keyword"
                                        }
                                    }
                                },
                                "_collection": {
                                    "type": "object",
                                    "properties": {
                                        "fullname": {
                                            "type": "keyword"
                                        },
                                        "name": {
                                            "type": "keyword"
                                        },
                                        "version": {
                                            "type": "keyword"
                                        }
                                    }
                                }
                            }
                       }
                   })

    with raises(DepositDoesNotExist):
        get_deposit_by_cadi_id('EXO-00-002')


# @TOFIX schemas module still uses mappings from files, that's why we use existing schemas
# this should be patched in schemas PR
@patch(
    'cap.modules.experiments.utils.cadi.get_all_from_cadi',
    MagicMock(return_value=[{
        'conference':
        '',
        'conferenceStatus':
        '',
        'code':
        'EXO-00-000',
        'targetConference':
        None,
        'approvalTalk':
        'https://indico.cern.ch/event/event.pdf',
        'creationDate':
        '2014-02-05',
        'updateDate':
        '2014-07-26',
        'pas':
        'http://cms.cern.ch:80/pas.pdf',
        'id':
        1,
        'targetPubPeriod':
        None,
        'targetDatePreApp':
        '19/12/2014',
        'papertar':
        'http://cms.cern.ch:80/paper.tgz',
        'awg':
        'HIG',
        'contact': {
            'cmsId': 1234,
            'hrId': 5678,
            'username': 'contact.user',
            'email': 'owner@cern.ch'
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
        'status':
        'PUB',
        'url':
        'https://twiki.cern.ch/twikiurl',
        'creatorName':
        'Creator User',
        'publicationStatus':
        'Free',
        'paper':
        'http://cms.cern.ch:80/paper.pdf',
        'description':
        'Projections for 2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh) in 3000 fb-1',
        'name':
        '2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh)',
        'hepData':
        '',
    }]))
@patch('cap.modules.user.utils.does_user_exist_in_ldap',
       MagicMock(return_value=True))
@patch('cap.modules.user.utils.does_egroup_exist_in_ldap',
       MagicMock(return_value=True))
@patch('cap.modules.experiments.utils.cadi.get_user_mail_from_ldap',
       MagicMock(return_value='owner@cern.ch'))
def test_synchronize_cadi_entries_when_entry_doesnt_exist_creates_a_new_one_and_assigns_all_the_permissions_correctly(
        base_app, db, es, location, create_schema):
    create_schema('cms-analysis', experiment='CMS', version='0.0.1')

    owner = create_test_user('owner@cern.ch')
    cms_members_group_with_r_access = assign_egroup_to_experiment(
        'cms-members@cern.ch', 'CMS')
    cms_admin_groups_with_admin_access = [
        _datastore.find_or_create_role('cms-physics-coordinator@cern.ch'),
        _datastore.find_or_create_role('cms-cap-admin@cern.ch'),
        _datastore.find_or_create_role('cms-phys-conveners-exo@cern.ch'),
    ]
    db.session.commit()

    # deposit with this cadi id doesn't exist
    with raises(DepositDoesNotExist):
        get_deposit_by_cadi_id('EXO-00-000')

    synchronize_cadi_entries()

    current_search.flush_and_refresh('deposits-records')

    # deposit with this cadi id created
    deposit = get_deposit_by_cadi_id('EXO-00-000')

    assert deposit == {
        'cadi_info': {
            'description':
            'Projections for 2HDM Higgs studies (H->ZZ and A->Zh) in 3000 fb-1',
            'name':
            '2HDM Higgs studies (H->ZZ and A->Zh)',
            'contact':
            'owner@cern.ch',
            'creator':
            'creator.user@example.com',
            'updater':
            'updater.user@example.com',
            'created':
            '2014-02-05',
            'updated':
            '2014-07-26',
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
        },
        'general_title': '2HDM Higgs studies (H->ZZ and A->Zh)',
        '_fetched_from': 'cadi',
        '_user_edited': False,
        'basic_info': {
            'cadi_id': 'EXO-00-000'
        },
        '$schema':
        'https://analysispreservation.cern.ch/schemas/deposits/records/cms-analysis-v0.0.1.json',
        '_deposit': {
            'id': deposit['_deposit']['id'],
            'status': 'draft',
            'owners': []
        },
        '_experiment': 'CMS',
        '_access': {
            'deposit-read': {
                'users': [owner.id],
                'roles': [cms_members_group_with_r_access.id] +
                [x.id for x in cms_admin_groups_with_admin_access]
            },
            'deposit-update': {
                'users': [owner.id],
                'roles': [x.id for x in cms_admin_groups_with_admin_access]
            },
            'deposit-admin': {
                'users': [owner.id],
                'roles': [x.id for x in cms_admin_groups_with_admin_access]
            }
        },
        '_files': []
    }


@patch('cap.modules.experiments.utils.cadi.get_all_from_cadi',
       MagicMock(return_value=[dict(code=u'dEXO-00-001', status=u'Free')]))
@patch('cap.modules.user.utils.does_user_exist_in_ldap',
       MagicMock(side_effect=LDAPError))
@patch('cap.modules.user.utils.does_egroup_exist_in_ldap',
       MagicMock(side_effect=LDAPError))
def test_synchronize_cadi_entries_when_LDAP_error_occured_during_permissions_assigning_entry_was_not_saved_in_db_or_es(
        base_app, db, es, location, create_schema):
    create_schema('cms-analysis', experiment='CMS', version='0.0.1')

    synchronize_cadi_entries()

    current_search.flush_and_refresh('deposits-records')

    with raises(DepositDoesNotExist):
        get_deposit_by_cadi_id('EXO-00-001')


# @TOFIX schemas module still uses mappings from files, that's why we use existing schemas
# this should be patched in schemas PR
# To check the functionality of `user_edited` key in deposit.
@patch('cap.modules.experiments.utils.cadi.get_all_from_cadi',
       MagicMock(
           return_value=[{
               u'conference': '',
               u'conferenceStatus': '',
               u'code': 'EXO-00-000',
               u'targetConference': None,
               u'approvalTalk': 'https://indico.cern.ch/event/event.pdf',
               u'creationDate': '2014-02-05',
               u'updateDate': '2014-07-26',
               u'pas': 'http://cms.cern.ch:80/pas.pdf',
               u'id': 1,
               u'updaterName': 'Updater User',
               u'targetPubPeriod': None,
               u'targetDatePreApp': '19/12/2014',
               u'papertar': 'http://cms.cern.ch:80/paper.tgz',
               u'creator': {
                    'cmsId': 4321,
                    'hrId': 8765,
                    'username': 'creator.user',
                    'email': 'creator.user@example.com'
                },
                u'contact': {
                    'cmsId': 1234,
                    'hrId': 5678,
                    'username': 'contact.user',
                    'email': 'contact.user@example.com'
                },
               u'status': 'PUB',
               u'url': 'https://twiki.cern.ch/twikiurl',
               u'publicationStatus': 'Free',
               u'paper': 'http://cms.cern.ch:80/paper.pdf',
               u'description': 'Projections for 2HDM Higgs studies',
               u'name': '2HDM Higgs studies (H-&gt;ZZ and A-&gt;Zh)'
           }]))
def test_synchronize_cadi_entries_when_entry_exist_updates_cadi_info(
        base_app, appctx, db, es, superuser, create_deposit):
    create_deposit(
        superuser, 'cms-analysis', {
            'version': '0.0.1',
            '$ana_type': 'cms-analysis',
            'basic_info': {
                'cadi_id': 'EXO-00-001'
            }
        })
    # deposit with this cadi id already exists
    deposit = get_deposit_by_cadi_id('EXO-00-001')

    with base_app.test_request_context():
        synchronize_cadi_entries()

        updated_deposit = get_deposit_by_cadi_id('EXO-00-000')

        assert updated_deposit == {
        'version': '0.0.1',
        'basic_info': {
            'cadi_id': 'EXO-00-001'
        },
        '_deposit': {
            'id': deposit['_deposit']['id'],
            'status': 'draft',
            'owners': [superuser.id],
            'created_by': superuser.id
        },
        '$schema':
        'https://analysispreservation.cern.ch/schemas/deposits/records/cms-analysis-v1.0.0.json',
        '_experiment': None,
        '_access': {
            'deposit-read': {
                'users': [superuser.id],
                'roles': []
            },
            'deposit-update': {
                'users': [superuser.id],
                'roles': []
            },
            'deposit-admin': {
                'users': [superuser.id],
                'roles': []
            }
        },
        '_user_edited': True,
        '_files': [],
        'cadi_info': {
            'status': 'PUB',
            'contact': 'contact.user@example.com',
            'creator': 'creator.user@example.com',
            'publication_status': 'Free',
            'twiki': 'https://twiki.cern.ch/twikiurl',
            'pas': 'http://cms.cern.ch:80/pas.pdf',
            'name': '2HDM Higgs studies (H->ZZ and A->Zh)',
            'description': 'Projections for 2HDM Higgs studies',
            'created': '2014-02-05',
            'updated': '2014-07-26',
            'updater': '',
            'awg': '', 'conference': '',
            'paper': 'http://cms.cern.ch:80/paper.pdf',
            'paper_tar': 'http://cms.cern.ch:80/paper.tgz',
            'hepData': ''
        }
    }
