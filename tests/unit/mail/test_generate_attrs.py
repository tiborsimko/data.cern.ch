# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2021 CERN.
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

from unittest.mock import patch
from cap.modules.mail.attributes import generate_recipients, generate_body, \
    generate_subject


def _generate_schema_config(notification_config):
    return {
        "notifications": {
            "actions": {
                "publish": notification_config
            }
        }
    }

def test_generate_recipients(app, users, location, create_schema, create_deposit):
    user = users['cms_user']
    # mock_user.email = user.email
    config = {
        "recipients": {
            "bcc": [{
                "op": "and",
                "checks": [
                    {
                        "path": "ml_app_use",
                        "condition": "exists"
                    }
                ],
                "mails": {
                    "default": ["ml-conveners-test@cern0.ch", "ml-conveners-jira-test@cern0.ch"]
                }
            }],
            "recipients": [
                'test-mail@cern0.ch',
                {"method": "get_owner"},
                {"method": "get_submitter"},
                {
                    "mails": {
                        "default": ['default@cern0.ch']
                    }
                }
            ]
        }
    }

    _config = _generate_schema_config([config])
    create_schema('test', experiment='CMS', config=_config)
    deposit = create_deposit(user, 'test',
                             {
                                 '$ana_type': 'test',
                                 'general_title': 'Test',
                                 'ml_app_use': True
                             },
                             experiment='CMS',
                             publish=True)

    recipients, cc, bcc = generate_recipients(deposit, config,
        default_ctx={'submitter_id': user.id})
    assert set(recipients) == {'cms_user@cern.ch', 'default@cern0.ch', 'test-mail@cern0.ch'}
    assert set(bcc) == {"ml-conveners-test@cern0.ch", "ml-conveners-jira-test@cern0.ch"}
    assert cc == []


# @patch('cap.modules.mail.custom.body.current_user')
def test_generate_body(app, users, location, create_schema, create_deposit):
    user = users['cms_user']
    # mock_user.email = user.email

    config = {
        "body": {
            "template_file": "mail/body/experiments/cms/questionnaire_message_published.html",
            "ctx": [{
                "name": "cadi_id",
                "path": "analysis_context.cadi_id"
            }, {
                "name": "title",
                "path": "general_title"
            }, {
                "method": "published_url"
            }, {
                "method": "submitter_email"
            }]
        },
        "recipients": {
            "recipients": ["test-mail@cern0.ch"]
        }
    }
    _config = _generate_schema_config([config])
    create_schema('test', experiment='CMS', config=_config)
    deposit = create_deposit(user, 'test',
                             {
                                 '$ana_type': 'test',
                                 'general_title': 'Test',
                                 'analysis_context': {
                                     'cadi_id': 'ABC-11-111'
                                 },
                             },
                             experiment='CMS',
                             publish=True)

    body, _ = generate_body(deposit, config,
        default_ctx={'submitter_id': user.id, 'action': 'publish'})
    assert 'CADI URL: https://cms.cern.ch/iCMS/analysisadmin/cadi?ancode=ABC-11-111' in body
    assert 'Title: Test' in body
    assert 'Submitted by cms_user@cern.ch.' in body

def test_generate_subject(app, users, location, create_schema, create_deposit):
    user = users['cms_user']
    # mock_user.email = user.email

    config = {
        "subject": {
            "template_file": "mail/subject/questionnaire_subject_published.html",
            "ctx": [{
                "name": "cadi_id",
                "path": "analysis_context.cadi_id"
            }, {
                "method": "revision"
            }, {
                "method": "published_id"
            }]
        },
        "recipients": {
            "recipients": ["test-mail@cern0.ch"]
        }
    }
    _config = _generate_schema_config([config])
    create_schema('test', experiment='CMS', config=_config)
    deposit = create_deposit(user, 'test',
                             {
                                 '$ana_type': 'test',
                                 'analysis_context': {
                                     'cadi_id': 'ABC-11-111'
                                 },
                             },
                             experiment='CMS',
                             publish=True)

    pid = deposit['_deposit']['pid']['value']
    subject = generate_subject(deposit, config, 
        default_ctx={'submitter_id': user.id, 'action': 'publish'})
    
    assert subject == f'Questionnaire for ABC-11-111 {pid} - New Published Analysis | CERN Analysis Preservation'

def test_generate_recipients_with_nested_conditions(app, users, location, create_schema, create_deposit):
    user = users['cms_user']
    # mock_user.email = user.email

    config = {
        "recipients": {
            'recipients': [
                {"method": "get_owner"},
                {"method": "get_submitter"},
                {
                    "mails": {
                        "default": ['default@cern0.ch']
                    }
                }
            ],
            'bcc': [{
                'op': 'and',
                "checks": [
                    {
                        "path": "ml_app_use",
                        "condition": "exists",
                    },
                    {
                        # 1st nested: should return true, 1 of them is false and we have or
                        "op": "or",
                        "checks": [{
                            "path": "some_other_field",
                            "condition": "equals",
                            "value": 'yes',
                        }, {
                            "path": "some_field",
                            "condition": "exists"
                        }, {
                            # 2nd nested
                            "op": "and",
                            "checks": [{
                                "path": "some_third_field",
                                "condition": "equals",
                                "value": 'yes',
                            }]
                        }]
                    }
                ],
                "mails": {
                    "default": ["ml-conveners-test@cern0.ch", "ml-conveners-jira-test@cern0.ch"]
                }
            }]
        }
    }
    _config = _generate_schema_config([config])
    create_schema('test', experiment='CMS', config=_config)
    deposit = create_deposit(user, 'test',
                             {
                                 '$ana_type': 'test',
                                 'general_title': 'Test',
                                 'ml_app_use': True,
                                 'some_other_field': 'yes',
                                 'some_third_field': 'yes'
                             },
                             experiment='CMS',
                             publish=True)

    recipients, cc, bcc = generate_recipients(deposit, config,
        default_ctx={'submitter_id': user.id, 'action': 'publish'})
    assert set(recipients) == {'cms_user@cern.ch', 'default@cern0.ch'}
    assert set(bcc) == {"ml-conveners-test@cern0.ch", "ml-conveners-jira-test@cern0.ch"}
    assert cc == []
