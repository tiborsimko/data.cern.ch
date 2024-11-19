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

from sqlalchemy.exc import IntegrityError

from cap.modules.schemas.models import Schema
from invenio_jsonschemas.errors import JSONSchemaNotFound
from invenio_search import current_search
from pytest import mark, raises

from conftest import add_role_to_user, _datastore


def test_when_schema_with_same_name_and_version_raises_IntegrityError(db):
    with raises(IntegrityError):
        schema = {
            'name': 'cms-analysis',
            'deposit_schema': {},
            'major': 1,
            'minor': 0,
            'patch': 1
        }
        db.session.add(Schema(**schema))
        db.session.add(Schema(**schema))
        db.session.commit()


def test_when_schema_name_contains_forbidden_characters_raises_AssertionError(
        db):
    with raises(ValueError):
        schema = {
            'name': 'cmsanalysis,\\',
            'deposit_schema': {},
        }
        db.session.add(Schema(**schema))
        db.session.commit()


def test_create_newer_version_of_existing_schema(db):
    schema = {
        'name': 'cms-analysis',
        'deposit_schema': {},
        'major': 1,
        'minor': 0,
        'patch': 1
    }
    db.session.add(Schema(**schema))
    schema.update({'patch': 2})
    db.session.add(Schema(**schema))
    db.session.commit()

    assert Schema.query.count() == 2


def test_schema_stringify(db):
    schema = Schema(
        **{
            'name': 'cms-analysis',
            'deposit_schema': {},
            'major': 1,
            'minor': 0,
            'patch': 2
        })
    db.session.add(schema)
    db.session.commit()

    assert str(schema) == 'cms-analysis-v1.0.2'


def test_deposit_path_and_index(db):
    schema = Schema(
        **{
            'name': 'cms-analysis',
            'deposit_schema': {},
            'major': 1,
            'minor': 0,
            'patch': 2
        })
    db.session.add(schema)
    db.session.commit()

    assert schema.deposit_path == 'deposits/records/cms-analysis-v1.0.2.json'
    assert schema.deposit_index == 'deposits-records-cms-analysis-v1.0.2'


def test_record_path_and_index(db):
    schema = Schema(
        **{
            'name': 'cms-analysis',
            'deposit_schema': {},
            'major': 1,
            'minor': 0,
            'patch': 2
        })
    db.session.add(schema)
    db.session.commit()

    assert schema.record_path == 'records/cms-analysis-v1.0.2.json'
    assert schema.record_index == 'records-cms-analysis-v1.0.2'


def test_get_when_schema_doesnt_exist_raises_JSONSchemaNotFound(db):
    with raises(JSONSchemaNotFound):
        Schema.get('non-existing', '1.0.0')


def test_get(db):
    schema = Schema(name='test-schema')
    db.session.add(schema)
    db.session.add(Schema(name='test-schema', version='2.0.0'))
    db.session.add(Schema(name='another-schema', version='1.0.1'))
    db.session.commit()

    assert Schema.get('test-schema', '1.0.0') == schema


# @mark.parametrize("path,jsonschema", [
#   ('http://analysispreservation.cern.ch/api/schemas/deposits/records/example-analysis-v1.0.1', 'deposit_schema'),
#   ('http://analysispreservation.cern.ch/api/schemas/deposits/records/options/example-analysis-v1.0.1', 'deposit_options'),
#   ('http://analysispreservation.cern.ch/api/schemas/records/example-analysis-v1.0.1', 'record_schema'),
#   ('http://analysispreservation.cern.ch/api/schemas/records/options/example-analysis-v1.0.1', 'record_options')
# ])
# def test_resolve_returns_correct_jsonschema(path, jsonschema, db):
#    schema = Schema(**{
#        'name': 'example-analysis',
#        'major': 1,
#        'minor': 0,
#        'patch': 1,
#        'deposit_schema': {'title': 'Example Deposit Schema'},
#        'record_schema': {'title': 'Example Record Schema'},
#        'deposit_options': {'title': 'Example Deposit Options Schema'},
#        'record_options': {'title': 'Example Record Options Schema'}
#    })
#    db.session.add(schema)
#    db.session.commit()
#
#    assert Schema.resolve(path) == (schema, getattr(schema, jsonschema))
#
#
# @mark.parametrize("path,field", [
#   ('http://analysispreservation.cern.ch/api/schemas/deposits/records/cms-analysis-v1.0.1', 'deposit_schema'),
#   ('http://analysispreservation.cern.ch/schemas/deposits/records/options/cms-analysis-v1.0.1', 'deposit_options'),
#   ('http://analysispreservation.cern.ch/schemas/records/options/cms-analysis-v1.0.1', 'deposit_options'),
#   ('https://analysispreservation.cern.ch/api/schemas/records/cms-analysis-v1.0.1.json', 'deposit_schema'),
#   ('deposits/records/cms-analysis-v1.0.1', 'deposit_schema'),
#   ('records/options/cms-analysis-v1.0.1', 'deposit_options')
# ])
# def test_resolve_when_use_deposit_as_record_flag_returns_deposit_schemas(db, path, field):
#    schema = Schema(
#        name='cms-analysis', major=1, minor=0, patch=1,
#        deposit_schema={'title': 'deposit'},
#        deposit_options={'title': 'deposit_options'},
#        use_deposit_as_record = True
#    )
#    db.session.add(schema)
#    db.session.commit()
#
#    assert Schema.resolve(path) == getattr(schema, field)
#
#
# @mark.parametrize("path", [
#   ('http://weird-host.cern.ch/api/schemas/deposits/records/cms-analysis-v1.0.1'),
#   ('http://analysispreservation.cern.ch/api/wrong-endpoint/deposits/records/cms-analysis-v1.0.1'),
#   ('http://analysispreservation.cern.ch/api/schemas/wrong-type/cms-analysis-v1.0.1'),
#   ('http://analysispreservation.cern.ch/api/schemas/deposits/records/non-existing-schema-v1.0.1'),
#   ('http://analysispreservation.cern.ch/api/schemas/records/non-existing-schema-v1.0.1'),
#   ('http://analysispreservation.cern.ch/api/schemas/deposits/records/cms-analysis-v0.0.0'),
#   ('http://analysispreservation.cern.ch/api/schemas/deposits/records/schemas/schemas/cms-analysis-v0.0.0'),
#   ('http://analysispreservation.cern.ch/api/schemas/records/cmsanalysisv0.0.0'),
# ])
# def test_resolve_when_wrong_path_raises_JSONSchemaNotFound(db, path):
#    schema = Schema(
#        name='cms-analysis', major=1, minor=0, patch=1,
#        deposit_schema={'title': 'deposit'},
#        record_schema={'title': 'record'},
#        deposit_options={'title': 'deposit_options'},
#        record_options={'title': 'record_options'}
#    )
#    db.session.add(schema)
#    db.session.commit()
#
#    with raises(JSONSchemaNotFound):
#        Schema.resolve(path)
#
#
# def test_get_by_fullpath_when_non_existing_raise_JSONSchemaNotFound(db):
# with raises(JSONSchemaNotFound):
# Schema.get_by_fullpath('/non-existing/schema/ana2-v2.1.1')
##
##
def test_get_latest_version_of_schema(db):
    latest_schema = Schema(name='my-schema', version='2.4.3')
    db.session.add(Schema(name='my-schema', version='0.6.6'))
    db.session.add(Schema(name='my-schema', version='1.5.5'))
    db.session.add(Schema(name='my-schema', version='2.3.4'))
    db.session.add(Schema(name='my-schema', version='2.4.0'))
    db.session.add(Schema(name='different-schema', version='3.5.4'))
    db.session.add(latest_schema)
    db.session.commit()

    assert Schema.get_latest('my-schema') == latest_schema


def test_get_latest_version_of_schema_when_schema_with_given_name_doesnt_exist_raises_JSONSchemaNotFound(
        db):
    with raises(JSONSchemaNotFound):
        Schema.get_latest('non-existing')


def test_on_save_mapping_is_created_and_index_name_added_to_mappings_map(
        db, es):
    schema = Schema(
        name='cms-schema',
        is_indexed=True,
        record_mapping={
            'mappings': {
                'properties': {
                    "title": {
                        "type": "text"
                    }
                }
            }
        },
        deposit_mapping={
            'mappings':
                {
                    'properties': {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                }
        })
    db.session.add(schema)
    db.session.commit()

    assert 'deposits-records-cms-schema-v1.0.0' in current_search.mappings.keys(
    )
    assert 'records-cms-schema-v1.0.0' in current_search.mappings.keys()

    assert es.indices.exists('deposits-records-cms-schema-v1.0.0')
    assert es.indices.exists('records-cms-schema-v1.0.0')

    assert es.indices.get_mapping('records-cms-schema-v1.0.0') == {
        'records-cms-schema-v1.0.0':
            {
                'mappings': {
                    'properties': {
                        'title': {
                            'type': 'text'
                        }
                    }
                }
            }
    }

    assert es.indices.get_mapping('deposits-records-cms-schema-v1.0.0') == {
        'deposits-records-cms-schema-v1.0.0':
            {
                'mappings':
                    {
                        'properties': {
                            'keyword': {
                                'type': 'keyword'
                            }
                        }
                    }
            }
    }

    db.session.delete(schema)
    db.session.commit()

    assert not es.indices.exists('deposits-records-cms-schema-v1.0.0')
    assert not es.indices.exists('records-cms-schema-v1.0.0')

    assert 'deposits-records-cms-schema-v1.0.0' not in current_search.mappings.keys(
    )
    assert 'records-cms-schema-v1.0.0' not in current_search.mappings.keys()
