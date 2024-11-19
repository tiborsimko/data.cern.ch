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

import json
from pytest import raises, mark
from unittest.mock import patch

from invenio_deposit.signals import post_action
from cap.modules.schemas.helpers import ValidationError

from data.mail_configs import (
    EMPTY_CONFIG, EMPTY_CONFIG_ASSERTIONS,
    DEFAULT_CONFIG, DEFAULT_CONFIG_ASSERTIONS,
    DEFAULT_CONFIG_PLAIN, DEFAULT_CONFIG_PLAIN_ASSERTIONS,
    DEFAULT_CONFIG_WITH_ERRORS, DEFAULT_CONFIG_WITH_ERRORS_ASSERTIONS,
    SIMPLE_CONFIG, SIMPLE_CONFIG_ASSERTIONS,
    SIMPLE_GLOBAL_CTX_CONFIG, SIMPLE_GLOBAL_CTX_CONFIG_ASSERTIONS,
    SIMPLE_GLOBAL_CTX_2_CONFIG, SIMPLE_GLOBAL_CTX_2_CONFIG_ASSERTIONS,
    WRONG_TEMPLATE_FILE_CONFIG, WRONG_TEMPLATE_FILE_CONFIG_ASSERTIONS, 
    NESTED_CONDITION_WITH_ERRORS_CONFIG, NESTED_CONDITION_WITH_ERRORS_CONFIG_ASSERTIONS,
    CTX_EXAMPLES_CONFIG, CTX_EXAMPLES_CONFIG_ASSERTIONS,
    WRONG_CTX_CONFIG, WRONG_CTX_CONFIG_ASSERTIONS,
    CONDITION_RECIPIENTS_CONFIG, CONDITION_RECIPIENTS_CONFIG_ASSERTIONS,
    WRONG_CONDITION_RECIPIENTS_CONFIG, WRONG_CONDITION_RECIPIENTS_CONFIG_ASSERTIONS,
    METHOD_AND_WRONG_CONDITION_RECIPIENTS_CONFIG, METHOD_AND_WRONG_CONDITION_RECIPIENTS_CONFIG_ASSERTIONS,
    MUTLIPLE_PUBLISH_CONFIG, MUTLIPLE_PUBLISH_CONFIG_ASSERTIONS,
    NESTED_CONDITIONS_CONFIG, NESTED_CONDITIONS_CONFIG_ASSERTIONS,
    WRONG_TEMPLATE_CONFIG, WRONG_TEMPLATE_CONFIG_ASSERTIONS,
    HAS_PERMISSION_CONFIG, HAS_PERMISSION_CONFIG_ASSERTIONS,
    CMS_STATS_QUESTIONNAIRE, CMS_STATS_QUESTIONNAIRE_ASSERTIONS,
    WRONG_BASE_TEMPLATE_CONFIG, WRONG_BASE_TEMPLATE_CONFIG_ASSERTIONS
)
from cap.modules.mail.utils import path_value_equals

@mark.parametrize("config,expected",[
    (EMPTY_CONFIG, EMPTY_CONFIG_ASSERTIONS),
    (DEFAULT_CONFIG, DEFAULT_CONFIG_ASSERTIONS),
    (DEFAULT_CONFIG_PLAIN, DEFAULT_CONFIG_PLAIN_ASSERTIONS),
    (DEFAULT_CONFIG_WITH_ERRORS, DEFAULT_CONFIG_WITH_ERRORS_ASSERTIONS),
    (SIMPLE_CONFIG, SIMPLE_CONFIG_ASSERTIONS),
    (SIMPLE_GLOBAL_CTX_CONFIG, SIMPLE_GLOBAL_CTX_CONFIG_ASSERTIONS),
    (SIMPLE_GLOBAL_CTX_2_CONFIG, SIMPLE_GLOBAL_CTX_2_CONFIG_ASSERTIONS),
    (WRONG_TEMPLATE_FILE_CONFIG, WRONG_TEMPLATE_FILE_CONFIG_ASSERTIONS),
    (NESTED_CONDITION_WITH_ERRORS_CONFIG, NESTED_CONDITION_WITH_ERRORS_CONFIG_ASSERTIONS),
    (CTX_EXAMPLES_CONFIG, CTX_EXAMPLES_CONFIG_ASSERTIONS),
    (WRONG_CTX_CONFIG, WRONG_CTX_CONFIG_ASSERTIONS),
    (WRONG_TEMPLATE_CONFIG, WRONG_TEMPLATE_CONFIG_ASSERTIONS),
    (CONDITION_RECIPIENTS_CONFIG, CONDITION_RECIPIENTS_CONFIG_ASSERTIONS),
    (WRONG_CONDITION_RECIPIENTS_CONFIG, WRONG_CONDITION_RECIPIENTS_CONFIG_ASSERTIONS),
    (METHOD_AND_WRONG_CONDITION_RECIPIENTS_CONFIG, METHOD_AND_WRONG_CONDITION_RECIPIENTS_CONFIG_ASSERTIONS),
    (MUTLIPLE_PUBLISH_CONFIG, MUTLIPLE_PUBLISH_CONFIG_ASSERTIONS),
    (NESTED_CONDITIONS_CONFIG, NESTED_CONDITIONS_CONFIG_ASSERTIONS),
    (HAS_PERMISSION_CONFIG, HAS_PERMISSION_CONFIG_ASSERTIONS),
    (CMS_STATS_QUESTIONNAIRE, CMS_STATS_QUESTIONNAIRE_ASSERTIONS),
    (WRONG_BASE_TEMPLATE_CONFIG, WRONG_BASE_TEMPLATE_CONFIG_ASSERTIONS)
])
@patch('cap.modules.mail.conditions.get_cern_extra_data_egroups', lambda x: ['cms-access'])
def test_post_action_mail(app, users, create_deposit, create_schema, client, auth_headers_for_user, config, expected):
    if expected.get("validationError"):
        with raises(ValidationError):
            create_schema('cms-stats-questionnaire', experiment='CMS', version="0.0.1", config=config)
            return
    else:
        create_schema('cms-stats-questionnaire', experiment='CMS', version="0.0.1", config=config)

        creator = users['cms_user']
        user = users['superuser']

        with app.app_context():
            with app.extensions['mail'].record_messages() as outbox:
                deposit = create_deposit(
                    creator,
                    'cms-stats-questionnaire',
                    {
                        '$schema': 'https://analysispreservation.cern.ch/schemas/'
                                'deposits/records/cms-stats-questionnaire-v0.0.1.json',
                        'general_title': 'test analysis',
                        'analysis_context': {
                            'cadi_id': 'ABC-11-111',
                            'wg': 'ABC'
                        },
                        'parton_distribution_functions': {
                            'test': "exists"
                        },
                        'ml_app_use': ['not empty'],
                        'multivariate_discriminants': {
                            'use_of_centralized_cms_apps': {
                                'options': "Yes"
                            }
                        }
                    },
                    experiment='CMS'
                )

                resp = client.post(
                    f"/deposits/{deposit['_deposit']['id']}/actions/publish",
                    headers=auth_headers_for_user(user)
                )

                if expected.get("response"):
                    assert resp.status_code == expected.get("response")
                pid = resp.json['recid']

                ctx = {}
                for ctx_key, ctx_item in expected.get("ctx", {}).items():
                    ctx_type = ctx_item.get("type") 
                    if ctx_type == "response":
                        ctx[ctx_key] = _path_value_equals(ctx_item['path'], resp.json)
                    elif ctx_type == "deposit":
                        ctx[ctx_key] = path_value_equals(ctx_item['path'], deposit)

                if not expected.get("outbox"):
                    assert len(outbox) == 0

                if expected.get("outbox_length"):
                    assert len(outbox) == expected.get("outbox_length")

                for outbox_key, outbox_assert in expected.get("outbox", {}).items():
                    _outbox = outbox[outbox_key]    

                    for _assertion in outbox_assert.get("subject", []):
                        if _assertion[0] is "in":
                            assert _assertion[1].format(**ctx) in _outbox.subject
                        elif _assertion[0] is "equals":
                            assert _assertion[1].format(**ctx) == _outbox.subject

                    for _assertion in outbox_assert.get("body", []):
                        assert _outbox.body
                        if _assertion[0] is "in":
                            assert _assertion[1].format(**ctx) in _outbox.body
                        elif _assertion[0] is "equals":
                            assert _assertion[1].format(**ctx) == _outbox.body

                    for _assertion in outbox_assert.get("html", []):
                        assert _outbox.html

                        if _assertion[0] is "in":
                            assert _assertion[1].format(**ctx) in _outbox.html
                        elif _assertion[0] is "equals":
                            assert _assertion[1].format(**ctx) == _outbox.html
                        elif _assertion[0] is "pid":
                            if _assertion[1] is "in":
                                assert _assertion[2].format(pid=pid) in _outbox.html
                            elif _assertion[1] is "equals":
                                assert _assertion[2].format(pid=pid) == _outbox.html

                    for rec_type in ["recipients", "bcc", "cc"]:
                        for _assertion in outbox_assert.get("recipients", {}).get(rec_type, []):
                            _list = []
                            if rec_type is "recipients":
                                _list = _outbox.recipients
                            elif rec_type is "bcc":
                                _list = _outbox.bcc
                            elif rec_type is "cc":
                                _list = _outbox.cc

                            if _assertion[0] is "in":
                                assert _assertion[1] in _list
                            elif _assertion[0] is "notin":
                                assert _assertion[1] not in _list

def _path_value_equals(path, record):
    """Given a string path, retrieve the JSON item."""
    paths = path.split(".")
    data = record
    try:
        for i in range(0, len(paths)):
            data = data[paths[i]]
        return data
    except:
        return None
