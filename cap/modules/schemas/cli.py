# * coding: utf8 *
#
# This file is part of CERN Analysis Preservation Framework.
# Copyright (C) 2016 CERN.
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
# MA 021111307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""CAP Schema cli."""

import itertools
import json
import os
import subprocess
import tempfile

import click
import jsonpatch
import requests
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_accounts.models import Role, User
from invenio_db import db
from invenio_jsonschemas.errors import JSONSchemaNotFound
from invenio_oauth2server.models import Token
from invenio_search import current_search_client
from jsonschema import Draft7Validator, exceptions
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from cap.cli import MutuallyExclusiveOption
from cap.modules.deposit.errors import DepositValidationError
from cap.modules.fixtures.cli import fixtures
from cap.modules.schemas.helpers import ValidationError
from cap.modules.schemas.models import Schema
from cap.modules.schemas.resolvers import (
    resolve_schema_by_name_and_version,
    resolve_schema_by_url,
    schema_name_to_url,
)
from cap.modules.schemas.utils import actions_from_type, is_later_version

DEPOSIT_REQUIRED_FIELDS = [
    '_buckets',
    '_deposit',
    '_files',
    '_experiment',
    '_fetched_from',
    '_user_edited',
    '_access',
]


@fixtures.command()
@click.option(
    '--permissions',
    '-p',
    required=True,
    multiple=True,
    help='Role permission actions. Accepts multiple options.',
)
@click.option(
    '--role',
    '-r',
    'roles',
    multiple=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=[
        "users",
    ],
    help='Roles with access to the record',
)
@click.option(
    '--user',
    '-u',
    'users',
    multiple=True,
    cls=MutuallyExclusiveOption,
    mutually_exclusive=[
        "roles",
    ],
    help='User with access to the record',
)
# deposit / record / schema
@click.option('--deposit', '_type', flag_value='deposit', default=True)
@click.option('--record', '_type', flag_value='record')
@click.option('--schema', '_type', flag_value='schema')
# allow / remove / deny
@click.option('--allow', 'schema_action', flag_value='allow', default=True)
@click.option('--deny', 'schema_action', flag_value='deny')
@click.option('--remove', 'schema_action', flag_value='remove')
@click.option(
    '--schema-version', '-v', 'schema_version', help='The schema version.'
)
@click.argument('schema-name')
@with_appcontext
def permissions(
    schema_name, permissions, roles, users, _type, schema_action, schema_version
):
    """Schema permission command group.

    Allows/Denies/Removes certain actions to roles, in order to
    have access to a deposit/record/schema.
    Examples:
        cap fixtures permissions
            -p read -p admin -r testegroup@cern.ch --allow --deposit SCHEMA_NAME
            -p read -r test-egroup@cern.ch --deny --deposit SCHEMA_NAME
            -p read -r test-egroup@cern.ch --allow --record SCHEMA_NAME
            -p read -p admin -r test-egroup@cern.ch --allow --schema SCHEMA_NAME
            -p read -p admin -u test-user@cern.ch --allow --deposit SCHEMA_NAME
            -p read -u test-user@cern.ch --deny --deposit SCHEMA_NAME
            -p read -u test-user@cern.ch --allow --record SCHEMA_NAME
            -p read -p admin -u test-user@cern.ch --allow --schema SCHEMA_NAME
    """
    if not (roles or users):
        raise click.BadParameter(
            'ERROR: Users (-u) or roles (-r) are required arguments'
        )
    msg = f'{schema_name}'
    try:
        if schema_version:
            msg += f'-v{schema_version}'
            schema = Schema.get(schema_name, schema_version)
        else:
            schema = Schema.get_latest(schema_name)
    except JSONSchemaNotFound:
        raise click.secho(f'Schema {msg} does not exist.', fg='red')

    # create the correct action names, and
    # check if action is subscribed and can be used
    requested_actions = actions_from_type(_type, permissions)
    allowed_actions = current_app.extensions['invenio-access'].actions

    for action in requested_actions:
        if action not in allowed_actions.keys():
            raise click.secho(f'Action {action} is not registered.', fg='red')

    # check if roles exist
    for role in roles:
        try:
            Role.query.filter_by(name=role).one()
        except NoResultFound:
            raise click.secho(f'Role with name {role} not found.', fg='red')

    # check if users exist
    for user in users:
        try:
            User.query.filter_by(email=user).one()
        except NoResultFound:
            raise click.secho(f'User with email {user} not found.', fg='red')

    # create all combinations of actions and roles
    try:
        actions_roles = list(itertools.product(requested_actions, roles))
        roles_logs = schema.process_action_roles(schema_action, actions_roles)
        # create all combinations of actions and users
        actions_users = list(itertools.product(requested_actions, users))
        users_logs = schema.process_action_users(schema_action, actions_users)
    except IntegrityError:
        return click.secho("Action user/role already exists.", fg="red")
    click.secho("Process finished.", fg="green")
    errors = [log for log in roles_logs if log.get('status') == 'error']
    errors += [log for log in users_logs if log.get('status') == 'error']

    for e in errors:
        click.secho(
            f"User/Role \"{e.get('role')}\" - \"{e.get('message')}\"",
            fg="yellow",
        )


@fixtures.command()
@with_appcontext
def generate_tokens():
    token_file_path = current_app.config.get('TESTS_E2E_TOKEN_FILE')
    user_list = [
        "info@inveniosoftware.org",
        "cms@inveniosoftware.org",
        "atlas@inveniosoftware.org",
        "alice@inveniosoftware.org",
        "lhcb@inveniosoftware.org",
        "faser@inveniosoftware.org",
        "random@inveniosoftware.org",
    ]
    for user_email in user_list:
        token = _get_or_create_token("testtoken", user_email)
        with open(token_file_path, 'a') as f:
            f.write(f"{user_email}:{token}\n")
            click.secho(f'User: {user_email} - Token: {token}', fg='green')
    click.secho('Tokens saved at {}'.format(token_file_path), fg='green')
    return


def _get_or_create_token(token_name, user_email):
    """Return method to fetch or create a user write token."""
    user = User.query.filter_by(email=user_email).first()

    if user:
        token_ = Token.query.filter_by(user_id=user.id).first()
        if not token_:
            token_ = Token.create_personal(
                token_name, user.id, scopes=['deposit:write']
            )
            db.session.add(token_)
        db.session.commit()
        return token_.access_token
    else:
        return None


@fixtures.command()
@click.option('--current', default='draft4', type=click.STRING)
@click.option('--new', default='draft7', type=click.STRING)
@click.option('--run', is_flag=True)
@with_appcontext
def migrate(current, new, run):
    """Command to migrate the versions of jsonschemas.

    Options:
    1. --current: Current version of jsonschema. Eg: 'draft4'
    2. --new: New version of jsonschema to migrate. Eg: 'draft7'
    3. --run: Flag to commit the changes in the db.

    Eg: cap fixtures migrate --current 'draft4' --new 'draft7' --run
    """
    # Verify npm environment and install alterschema.
    subprocess.check_output('npm -v', shell=True)
    subprocess.check_output('npm init -y', shell=True)
    subprocess.check_output('npm install alterschema', shell=True)

    schemas = Schema.query.all()
    for schema_model in schemas:
        click.secho(f'Migrating {schema_model.name}', fg='green')
        for attr in ['deposit_schema', 'record_schema']:
            # Migrate individual schema
            schema = getattr(schema_model, attr)

            temp_path = store_schema_temporarily(schema)
            try:
                output = subprocess.check_output(
                    f'node_modules/.bin/alterschema --from {current} --to {new} {temp_path}',  # noqa
                    shell=True,
                )
                click.secho('Alterschema ran successfully!')
                new_schema = json.loads(output)
            except subprocess.CalledProcessError as e:
                click.secho(f'alterschema command failed: {str(e)}', fg='red')
                continue

            handle_required_fields(new_schema)
            handle_dependencies_fields(new_schema)
            handle_enum_enumnames_fields(new_schema)

            alterschema_patch = jsonpatch.make_patch(schema, new_schema)
            click.secho(f'{attr}: {alterschema_patch}')

            validator = Draft7Validator(new_schema)
            try:
                validator.check_schema(new_schema)
            except exceptions.SchemaError as e:
                click.secho(
                    f'Schema {schema_model.name} field {attr} is not valid: {e.message}',  # noqa
                    fg='red',
                )
                continue

            setattr(schema_model, attr, new_schema)

            if run:
                click.secho('Commiting to the database', fg='green')
                db.session.commit()

    click.secho('Migration done successfully!', fg='green')


@fixtures.command()
@click.option(
    '--schema-url',
    '-u',
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["ana_type", "ana_version"],
    help='The url of the schema used for validation.',
)
@click.option(
    '--ana-type',
    '-a',
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["schema_url"],
    help='The analysis type of the schema used for validation.',
)
@click.option(
    '--ana-version', '-v', help='The analysis version of the records.'
)
@click.option(
    '--compare-with',
    '-c',
    help='The schema version, that the ' 'records should be compared to.',
)
@click.option(
    '--status',
    '-s',
    default='draft',
    type=click.Choice(['draft', 'published']),
    help='The metadata type that will be used for validation.',
)
@click.option(
    '--export',
    '-e',
    type=click.Path(),
    help='A file where, the validation errors can be saved.',
)
@click.option(
    '--export-type',
    '-et',
    default=None,
    type=click.Choice(['md']),
    help='The export type that will be used for output.',
)
@with_appcontext
def validate(
    schema_url, ana_type, ana_version, compare_with, status, export, export_type
):
    """Validate deposit or record metadata based on their schema.

    Provide the schema url OR ana-type and version, as well as the schema version
    that you want to compare the records you get, to. E.g.

    If you do not provide an ana-version, it will get the latest. If you do
    not provide a -c parameter, the records will compare the data to their
    own schema.

    cap fixtures validate -u https://analysispreservation.cern.ch/schemas/deposits/records/test-v2.0.0.json -c 1.0.0  # noqa
    cap fixtures validate -a test -c 1.0.0
    """
    try:
        if schema_url:
            schema = resolve_schema_by_url(schema_url)
        elif ana_type:
            schema = resolve_schema_by_name_and_version(ana_type, ana_version)
        else:
            raise click.UsageError(
                'You need to provide the ana-type or the schema-url.'
            )
    except JSONSchemaNotFound:
        raise click.UsageError('Schema not found.')
    except ValueError:
        raise click.UsageError(
            'Version has to be passed as string <major>.<minor>.<patch>.'
        )

    # differentiate between drafts/published
    from cap.modules.deposit.api import CAPDeposit
    from cap.modules.records.api import CAPRecord

    if status == 'draft':
        search_path = 'deposits-records'
        cap_record_class = CAPDeposit
    else:
        search_path = 'records'
        cap_record_class = CAPRecord

    # get all the records for this specific schema/type combination
    records = current_search_client.search(
        index=f"{search_path}-{schema.name}-v{schema.version}",
        body={
            "query": {
                "bool": {
                    "must": [
                        {"match": {"_deposit.status": status}},
                        {
                            "match": {
                                "$schema": schema_name_to_url(
                                    schema.name, schema.version
                                )
                            }
                        },
                    ]
                }
            }
        },
        size=5000,
    )['hits']['hits']
    pids = [rec['_id'] for rec in records]

    click.secho(
        f'{len(records)} record(s) of {schema.name} found.\n', fg='green'
    )

    total_errors = []
    for pid in pids:
        cap_record = cap_record_class.get_record(pid)
        cap_record_pid = cap_record.get('_deposit', {}).get('id')
        cap_record_cadi_id = cap_record.get('basic_info', {}).get('cadi_id')
        cap_host = 'https://analysispreservation.cern.ch/drafts'
        # get the url of the schema version, used for validation
        if compare_with:
            cap_record['$schema'] = schema_name_to_url(
                schema.name, compare_with
            )
        try:
            cap_record.validate()
            click.secho(f'No errors found in record {pid}', fg='green')
        except DepositValidationError as exc:
            if export_type == 'md':
                msg = (
                    '- [ ] Errors in **CADI ID:** '
                    + f'{cap_record_cadi_id or "?"}'
                    + f' - **[link]({cap_host}/{cap_record_pid})** :\n'
                )
                msg += "\n| Field Path | Error | \n| ---------- | ----- | \n"
                for err in exc.errors:
                    _err = err.res
                    msg += f"| ```{_err.get('field')}``` |"
                    msg += f" {_err.get('message')}  | \n"
                msg += "----\n"
            else:
                error_list = '\n'.join(str(err.res) for err in exc.errors)
                msg = (
                    f'Errors in {pid} - CADI '
                    + f'id: {cap_record_cadi_id or "?"}'
                    + f' - {cap_host}/{cap_record_pid} :\n{error_list}'
                )

            click.secho(msg, fg='red')

            if export:
                total_errors.append(msg)

    # export the errors in a file
    if export:
        with open(export, 'w') as out:
            out.writelines('\n\n'.join(err for err in total_errors))
        click.secho(f'Errors saved at {export}.', fg='red')


@fixtures.command()
@click.option(
    '--dir',
    '-d',
    type=click.Path(exists=True),
    help='The directory of the schemas to be added to the db.',
)
@click.option(
    '--url', '-u', help='The url of the schema to be added to the db.'
)
@click.option(
    '--force',
    '-f',
    is_flag=True,
    help='Force add the schema without validation.',
)
@click.option(
    '--force-version',
    '-fv',
    is_flag=True,
    help='Force disable version checking.',
)
@click.option(
    '--replace',
    '-r',
    is_flag=True,
    help='It this schema/version exists, update it.',
)
@with_appcontext
def schemas(dir, url, force, force_version, replace):
    """Add schemas to CAP.

    Add schemas either by downloading them from a url, or by adding
    them from a path. If no args are provided, then the schemas from the
    default path will be added to CAP.

    examples:
        cap fixtures schemas
        cap fixtures schemas --dir cap/folder/schemas
        cap fixtures schemas --url https://schemas.org/my-schema.json
    """
    if dir:
        add_fixtures_from_path(dir, force_version=force_version)
    if url:
        resp = requests.get(url)
        if not resp.ok:
            click.secho(
                f'Please provide a public url to a json file. '
                f'Error {resp.status_code}.',
                fg='red',
            )
            return

        try:
            data = resp.json()
            if not has_all_required_fields(data) and not force:
                click.secho(
                    f'Missing required fields. Make sure that all of: '
                    f'{DEPOSIT_REQUIRED_FIELDS} are in the json.',
                    fg='red',
                )  # noqa
                return
            add_schema_from_json(
                data, replace=replace, force_version=force_version
            )
        except (json.JSONDecodeError, ValueError):
            click.secho('Error in decoding the returned json.', fg='red')

    # by default, just add the fixtures from the default path
    if not dir and not url:
        add_fixtures_from_path(
            current_app.config.get('SCHEMAS_DEFAULT_PATH'),
            replace=replace,
            force_version=True,
        )


def add_fixtures_from_path(dir, replace=None, force_version=None):
    """Add fixtures from a specified path to CAP."""
    for root, dirs, files in os.walk(dir):
        json_filepaths = [
            os.path.join(root, f) for f in files if f.endswith(".json")
        ]

        for filepath in json_filepaths:
            with open(filepath, 'r') as f:
                try:
                    json_content = json.load(f)
                    add_schema_from_json(
                        json_content,
                        replace=replace,
                        force_version=force_version,
                    )
                except ValueError:
                    click.secho(f'Not valid json in {filepath} file', fg='red')


def add_schema_from_json(data, replace=None, force_version=None):
    """Add or update schema, using a json file."""
    allow_all = data.pop("allow_all", False)
    version = data['version']
    name = data['name']

    try:
        with db.session.begin_nested():
            try:
                _schema = Schema.get(name=name, version=version)
                if replace:
                    _schema.update(**data)
                    db.session.add(_schema)
                else:
                    click.secho(f'{name}-{version} already exists in the db.')
                    return
            except JSONSchemaNotFound:
                try:
                    _schema = Schema.get_latest(name=name)
                    if (
                        is_later_version(_schema.version, version)
                        and not force_version
                    ):
                        click.secho(
                            f'A later version ({_schema.version}) of '
                            f'{name} is already in the db. Error while '
                            f'adding {name}-{version}',
                            fg='red',
                        )
                        return
                    else:
                        _schema = Schema(**data)
                        db.session.add(_schema)
                except JSONSchemaNotFound:
                    _schema = Schema(**data)
                    db.session.add(_schema)

        # throws error if you try to re-insert the same action roles
        if allow_all and not replace:
            _schema.add_read_access_for_all_users()

        db.session.commit()
        click.secho(f'{name} has been added.', fg='green')
    except ValidationError as err:
        click.secho(err, fg='red')
        click.secho(
            f'Configuration is invalid. ' f'Aborting update for schema {name}.',
            fg='red',
        )
        return
    except IntegrityError:
        click.secho(f'An db error occurred while adding {name}.', fg='red')


def has_all_required_fields(data):
    """Check if there are any missing required fields in a json schema."""
    deposit_as_record = data.get('use_deposit_as_record')
    schemas_to_check = (
        [data['deposit_schema']]
        if deposit_as_record
        else [data['deposit_schema'], data['record_schema']]
    )

    for _schema in schemas_to_check:
        schema_fields = _schema.get('properties', {}).keys()

        # if there are no properties, we do not check
        if schema_fields:
            for req_field in DEPOSIT_REQUIRED_FIELDS:
                if req_field not in schema_fields:
                    return False
    return True


def store_schema_temporarily(schema):
    """Store schema in a temporary file."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp:
        temp.write(json.dumps(schema).encode('utf-8'))
        return temp.name


def handle_enum_enumnames_fields(schema):
    """Convert enum, enumNames to oneOf in a schema."""
    if isinstance(schema, dict):
        items_to_check = schema.items()
        modifications = []
        for key, value in items_to_check:
            if key == 'enum' and 'enumNames' in schema:
                enum_values = schema['enum']
                enum_names = schema['enumNames']
                one_of_array = [
                    {'const': val, 'title': name}
                    for val, name in zip(enum_values, enum_names)
                ]
                modifications.append(('remove', 'enum'))
                modifications.append(('remove', 'enumNames'))
                modifications.append(('add', 'oneOf', one_of_array))
            else:
                handle_enum_enumnames_fields(value)

        for operation, key, *value in modifications:
            if operation == 'remove':
                del schema[key]
            elif operation == 'add':
                schema[key] = value[0]

    elif isinstance(schema, list):
        for item in schema:
            handle_enum_enumnames_fields(item)


def handle_required_fields(schema):
    """Convert required from bool to list in a schema."""
    if isinstance(schema, dict):
        if 'properties' in schema:
            required_properties = []
            for property, value in schema['properties'].items():
                if isinstance(value, dict):
                    if value.get('required', False) == 'true':
                        del value['required']
                        required_properties.append(property)
                    handle_required_fields(value)
            if required_properties:
                schema['required'] = required_properties
        else:
            for value in schema.values():
                handle_required_fields(value)
    elif isinstance(schema, list):
        for item in schema:
            handle_required_fields(item)


def handle_dependencies_fields(schema):
    """Convert dependencies from list to object in schema."""
    if isinstance(schema, dict):
        for key, value in list(schema.items()):
            if key == 'properties':
                for prop, val in value.items():
                    if (
                        isinstance(val, dict)
                        and 'dependencies' in val
                        and isinstance(val['dependencies'], list)
                    ):
                        dependencies = val.pop('dependencies')
                        if dependencies:
                            if 'dependentRequired' not in schema:
                                schema['dependentRequired'] = {}
                            schema['dependentRequired'][prop] = dependencies
            if isinstance(value, dict) or isinstance(value, list):
                handle_dependencies_fields(value)
    elif isinstance(schema, list):
        for item in schema:
            handle_dependencies_fields(item)
