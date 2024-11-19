# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016, 2020 CERN.
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
from tempfile import NamedTemporaryFile


def test_validate_without_schema_name_or_url(app, cli_runner):
    res = cli_runner('fixtures validate')

    assert res.exit_code == 2
    assert 'You need to provide the ana-type or the schema-url.' in res.output


def test_validate_with_both_schema_name_and_url(app, cli_runner):
    res = cli_runner('fixtures validate -u schema-url -a analysis-type')

    assert res.exit_code == 2
    assert 'Illegal usage: `schema_url` is mutually exclusive with arguments' in res.output


def test_validate_with_schema_url_and_ana_version(app, cli_runner):
    res = cli_runner('fixtures validate -u schema-url -v 0.0.1')

    assert res.exit_code == 2
    assert 'Illegal usage: `schema_url` is mutually exclusive with arguments' in res.output


def test_validate_with_ana_type_schema_doesnt_exist(app, db, cli_runner):
    res = cli_runner('fixtures validate -a analysis-type')

    assert res.exit_code == 2
    assert 'Schema not found.' in res.output


def test_validate_with_ana_type_with_ana_version_doesnt_exist(app, db, cli_runner, create_schema):
    create_schema('test', experiment='CMS')
    res = cli_runner('fixtures validate -a test -v 0.0.2')

    assert res.exit_code == 2
    assert 'Schema not found.' in res.output


def test_validate_with_ana_type_with_invalid_ana_version(app, db, cli_runner, create_schema):
    create_schema('test', experiment='CMS')
    res = cli_runner('fixtures validate -a test -v version')

    assert res.exit_code == 2
    assert 'Version has to be passed as string <major>.<minor>.<patch>.' in res.output


def test_validate_with_schema_url_invalid_url(app, cli_runner):
    res = cli_runner('fixtures validate -u invalid-schema-url')

    assert res.exit_code == 2
    assert 'Schema not found.' in res.output


def test_validate_with_schema_url_schema_doesnt_exist(app, db, cli_runner):
    res = cli_runner(
        'fixtures validate -u https://analysispreservation.cern.ch/schemas/deposits/records/invalid-schema-v0.0.1.json')

    assert res.exit_code == 2
    assert 'Schema not found.' in res.output


def test_validate_with_schema_url_version_doesnt_exist(app, db, cli_runner, create_schema):
    create_schema('test', experiment='CMS')
    res = cli_runner(
        'fixtures validate -u https://analysispreservation.cern.ch/schemas/deposits/records/test-v0.0.2.json')

    assert res.exit_code == 2
    assert 'Schema not found.' in res.output


def test_validate_with_schema_url_correct_record(
        app, db, es, cli_runner, users, create_schema, create_deposit):
    create_schema('test', experiment='CMS')
    create_deposit(users['cms_user'], 'test')

    res = cli_runner(
        'fixtures validate -u https://analysispreservation.cern.ch/schemas/deposits/records/test-v1.0.0.json')

    assert res.exit_code == 0
    assert '1 record(s) of test found.' in res.output
    assert 'No errors found in record' in res.output


def test_validate_with_schema_url_correct_record_published(
        app, db, es, cli_runner, users, create_schema, create_deposit):
    create_schema('test', experiment='CMS')
    create_deposit(users['cms_user'], 'test', publish=True)

    res = cli_runner(
        'fixtures validate -u https://analysispreservation.cern.ch/schemas/records/test-v1.0.0.json -s published')

    assert res.exit_code == 0
    assert '1 record(s) of test found.' in res.output
    assert 'No errors found in record' in res.output


def test_validate_with_ana_type_correct_record(
        app, db, es, cli_runner, script_info, users, create_schema, create_deposit):
    create_schema('test', experiment='CMS')
    create_deposit(users['cms_user'], 'test')

    res = cli_runner('fixtures validate -a test')

    assert res.exit_code == 0
    assert '1 record(s) of test found.' in res.output
    assert 'No errors found in record' in res.output


def test_validate_with_different_version_records(
        app, db, es, cli_runner, users, create_schema, create_deposit):
    # version 1
    create_schema('test', experiment='CMS', version='1.0.0',
                  deposit_schema={
                      'title': 'test-schema',
                      'type': 'object',
                      'properties': {
                          'basic': {
                              'type': 'string',
                              'enum': ['test1', 'test2']
                          }
                      }
                  })
    create_deposit(users['cms_user'], 'test',
                   {
                       "$schema": "https://analysispreservation.cern.ch/schemas/deposits/records/test-v1.0.0.json",
                       'basic': 'test1'
                   },
                   experiment='CMS')

    # version 2
    create_schema('test', experiment='CMS', version='2.0.0',
                  deposit_schema={
                      'title': 'test-schema',
                      'type': 'object',
                      'properties': {
                          'basic': {
                              'type': 'string',
                              'enum': ['test3', 'test4']
                          }
                      }
                  })

    res = cli_runner('fixtures validate -a test -v 1.0.0 -c 2.0.0')
    assert res.exit_code == 0
    assert '1 record(s) of test found.' in res.output
    assert "'test1' is not one of ['test3', 'test4']" in res.output


def test_validate_with_different_version_records_and_exported_file(
        app, db, es, cli_runner, users, create_schema, create_deposit):
    # version 1
    create_schema('test', experiment='CMS', version='1.0.0',
                  deposit_schema={
                      'title': 'test-schema',
                      'type': 'object',
                      'properties': {
                          'basic': {
                              'type': 'string',
                              'enum': ['test1', 'test2']
                          }
                      }
                  })
    create_deposit(users['cms_user'], 'test',
                   {
                       "$schema": "https://analysispreservation.cern.ch/schemas/deposits/records/test-v1.0.0.json",
                       'basic': 'test1'
                   },
                   experiment='CMS')

    # version 2
    create_schema('test', experiment='CMS', version='2.0.0',
                  deposit_schema={
                      'title': 'test-schema',
                      'type': 'object',
                      'properties': {
                          'basic': {
                              'type': 'string',
                              'enum': ['test3', 'test4']
                          }
                      }
                  })

    with NamedTemporaryFile('r') as tmp:
        res = cli_runner(
            f'fixtures validate -a test -v 1.0.0 -c 2.0.0 -e {tmp.name}')

        assert res.exit_code == 0
        assert '1 record(s) of test found.' in res.output
        assert "'test1' is not one of ['test3', 'test4']" in res.output
        assert "'test1' is not one of ['test3', 'test4']" in tmp.read()
