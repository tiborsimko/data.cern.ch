# -*- coding: utf-8 -*-
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2022 CERN.
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

"""Deposit validators."""

import os

from flask import current_app
from jsonschema._types import draft7_type_checker
# from jsonschema._utils import load_schema
from jsonschema_specifications import REGISTRY as SPECIFICATIONS
from jsonschema.validators import Draft7Validator, create, extend

from cap.modules.deposit.validators.services import fetch_data_from_url
from cap.modules.deposit.validators.users import (
    find_field_copy,
    validate_field_schema_editing,
)
from cap.modules.experiments.validators import (
    validate_cms_trigger,
    validate_das_path,
    validate_unique_cadi,
)

deposit_validators = dict(Draft7Validator.VALIDATORS)

if not os.environ.get("CAP_CMS_VALIDATION_DISABLE"):
    deposit_validators['x-validate-cms-trigger'] = validate_cms_trigger
    deposit_validators['x-validate-das-path'] = validate_das_path
deposit_validators['x-validate-unique-cadi'] = validate_unique_cadi
# deposit_validators['x-validate-cadi-id'] = validate_cadi_id

deposit_validators['x-cap-fetch'] = fetch_data_from_url
DepositValidator = extend(Draft7Validator, validators=deposit_validators)
NoRequiredValidator = extend(DepositValidator, {'required': None})


# Minimal Validator to be used for extending with custom schema validation
# mainly used to traverse the schema
INCLUDE_VALIDATORS = [
    '$ref',
    'allOf',
    'anyOf',
    'dependencies',
    'items',
    'not',
    'oneOf',
    'patternProperties',
    'properties',
]
minimal_validators = {
    i: v
    for i, v in Draft7Validator.VALIDATORS.items()
    if i in INCLUDE_VALIDATORS
}

MinimalValidator = create(
    SPECIFICATIONS.contents(
        "http://json-schema.org/draft-07/schema#",
    ),
    validators=minimal_validators,
    type_checker=draft7_type_checker,
    version="draft7-clean",
    id_of=lambda schema: schema.get("id", ""),
)


CUSTOM_VALIDATORS = {
    "x-cap-permission": validate_field_schema_editing,
    "x-cap-copy": find_field_copy,
    "x-cap-copyto": find_field_copy,
}


def get_custom_validator(schema):
    resolver = current_app.extensions[
        'invenio-records'
    ].ref_resolver_cls.from_schema(schema)
    validator = extend(MinimalValidator, validators=CUSTOM_VALIDATORS)
    validator = validator(schema, resolver=resolver)
    return validator
