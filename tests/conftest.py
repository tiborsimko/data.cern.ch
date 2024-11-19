# -*- coding: utf-8 -*-
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
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""Pytest configuration."""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from flask import current_app
from flask.cli import ScriptInfo
from flask_principal import ActionNeed
from flask_security import login_user

from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts.testutils import create_test_user
from invenio_app.config import APP_DEFAULT_SECURE_HEADERS
from invenio_db import db as db_
from invenio_deposit.minters import deposit_minter
from invenio_deposit.scopes import write_scope
from invenio_files_rest.models import Location
from invenio_indexer.api import RecordIndexer
from invenio_jsonschemas.errors import JSONSchemaNotFound
from invenio_jsonschemas.proxies import current_jsonschemas
from invenio_oauth2server.models import Client, Token
from invenio_oauthclient.models import RemoteAccount
from invenio_pidstore.resolver import Resolver
from invenio_search import current_search, current_search_client

from click.testing import CliRunner
from sqlalchemy_utils.functions import create_database, database_exists
from werkzeug.local import LocalProxy

from cap.cli import cli
from cap.factory import create_api
from cap.modules.auth.models import OAuth2Token
from cap.modules.deposit.api import CAPDeposit as Deposit
from cap.modules.experiments.permissions import exp_need_factory
from cap.modules.experiments.search.cms_triggers import CMS_TRIGGERS_ES_CONFIG
from cap.modules.experiments.search.das import DAS_DATASETS_ES_CONFIG
from cap.modules.experiments.utils.cms import \
    cache_cms_triggers_in_es_from_file
from cap.modules.experiments.utils.das import \
    cache_das_datasets_in_es_from_file

from cap.modules.repos.models import (GitRepository, GitWebhook,
                                      GitWebhookSubscriber)
from cap.modules.schemas.models import Schema
from cap.modules.schemas.resolvers import resolve_schema_by_url
from cap.modules.user.utils import get_role_name_by_id, get_user_email_by_id

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@pytest.fixture()
def cli_runner(app):
    runner = CliRunner(env={'FLASK_APP': 'cap/wsgi.py'})
    script_info = ScriptInfo(create_app=lambda info: app)

    def run(command):
        """Run the command from the CLI."""
        command_args = command.split()
        return runner.invoke(cli, command_args, obj=script_info)

    yield run


@pytest.fixture(scope='session')
def instance_path():
    """Default instance path."""
    path = tempfile.mkdtemp()

    yield path

    shutil.rmtree(path)


@pytest.fixture(scope='session')
def env_config(instance_path):
    """Default instance path."""
    os.environ.update(APP_INSTANCE_PATH=os.environ.get('INSTANCE_PATH',
                                                       instance_path), )

    return os.environ


@pytest.fixture(scope='session')
def default_config():
    """Default configuration."""
    APP_DEFAULT_SECURE_HEADERS['force_https'] = False
    APP_DEFAULT_SECURE_HEADERS['session_cookie_secure'] = False

    return dict(DEBUG_TB_ENABLED=False,
                APP_DEFAULT_SECURE_HEADERS=APP_DEFAULT_SECURE_HEADERS,
                CELERY_ALWAYS_EAGER=True,
                CELERY_CACHE_BACKEND='memory',
                task_eager_propagates=True,
                CELERY_RESULT_BACKEND='cache',
                SQLALCHEMY_DATABASE_URI='postgresql://cap:cap@localhost/cap-test',
                JSONSCHEMAS_HOST='analysispreservation.cern.ch',
                SERVER_NAME='analysispreservation.cern.ch',
                ACCESS_CACHE=None,
                DEBUG=False,
                TESTING=True,
                APP_GITLAB_OAUTH_ACCESS_TOKEN='testtoken',
                MAIL_DEFAULT_SENDER="analysis-preservation-support@cern.ch",
                CADI_REGEX="^[A-Z]{3}-[0-9]{2}-[0-9]{3}$",
                CMS_STATS_COMMITEE_AND_PAGS=dict({
                    'ABC': {
                        'params': {
                            'primary': 'Admin Rev 1',
                            'secondary': 'Admin Rev 2'
                        },
                        'contacts': [
                            'admin-rev-1@cern0.ch',
                            'admin-rev-2@cern0.ch',
                            'admin-rev-group-1@cern0.ch',
                        ]
                    },
                    'ABD': {
                        'contacts': [

                        ]
                    }
                }),    
                PDF_FORUM_MAIL='pdf-forum-test@cern0.ch',
                CONVENERS_ML_MAIL='ml-conveners-test@cern0.ch',
                CONVENERS_ML_JIRA_MAIL='ml-conveners-jira-test@cern0.ch',
                CMS_HYPERNEWS_EMAIL_FORMAT='hn-cms-{}@cern0.ch',
                GITHUB_CAP_TOKEN="testtokengithub",
                GITLAB_CAP_TOKEN="testtokengitlab",
                CMS_STATS_QUESTIONNAIRE_ADMIN_ROLES='cms-admins@cern0.ch',
                RATELIMIT_APPLICATION='1000/minute',
                RECORDS_FILES_REST_ENDPOINTS={},
                APP_HEALTH_BLUEPRINT_ENABLED=False)


@pytest.fixture(scope='session')
def app(base_app):
    """Flask application fixture."""
    yield base_app


@pytest.fixture(scope='session')
def create_app():
    return create_api


@pytest.fixture(scope='session')
def base_app(create_app, default_config, request):
    app_ = create_app(**default_config)

    with app_.app_context():
        yield app_


@pytest.fixture()
def client(base_app):
    """Test client for the base application fixture.
    Scope: function
    If you need the database and search indexes initialized, simply use the
    Pytest-Flask fixture ``client`` instead. This fixture is mainly useful if
    you need a test client without needing to initialize both the database and
    search indexes.
    """
    with base_app.test_client() as client:
        yield client


@pytest.fixture(scope='module')
def appctx(base_app):
    """Application context for the current base application.
    Scope: module
    This fixture pushes an application context on the stack, so that
    ``current_app`` is defined and e.g ``url_for`` will also work.
    """
    with base_app.app_context():
        yield base_app


@pytest.fixture(scope='module')
def script_info(base_app):
    """Get ScriptInfo object for testing a CLI command.
    Scope: module
    .. code-block:: python
        def test_cmd(script_info):
            runner = CliRunner()
            result = runner.invoke(mycmd, obj=script_info)
            assert result.exit_code == 0
    """
    return ScriptInfo(create_app=lambda info: base_app)


@pytest.fixture
def db(base_app):
    """Setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture
def location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(name='testloc', uri=tmppath, default=True)
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def users(db):
    """Create users."""
    users = {
        'cms_user': create_user_with_access(db.session, 'cms_user@cern.ch',
                                            'cms-access'),
        'cms_user2': create_user_with_access(db.session, 'cms_user2@cern.ch',
                                             'cms-access'),
        'alice_user': create_user_with_access(db.session, 'alice_user@cern.ch',
                                              'alice-access'),
        'alice_user2': create_user_with_access(db.session,
                                               'alice_user2@cern.ch',
                                               'alice-access'),
        'atlas_user': create_user_with_access(db.session, 'atlas_user@cern.ch',
                                              'atlas-access'),
        'atlas_user2': create_user_with_access(db.session,
                                               'atlas_user2@cern.ch',
                                               'atlas-access'),
        'lhcb_user': create_user_with_access(db.session, 'lhcb_user@cern.ch',
                                             'lhcb-access'),
        'lhcb_user2': create_user_with_access(db.session, 'lhcb_user2@cern.ch',
                                              'lhcb-access'),
        'faser_user': create_user_with_access(db.session, 'faser_user@cern.ch',
                                              'faser-access'),
        'faser_user2': create_user_with_access(db.session, 'faser_user2@cern.ch',
                                              'faser-access'),
        'superuser': create_user_with_access(db.session, 'superuser@cern.ch',
                                             'superuser-access'),
        'random': create_user_with_access(db.session, 'random@cern0.ch'),
    }

    db.session.commit()

    return users


@pytest.fixture()
def remote_accounts(db, users):
    """Create Remote Accounts for experiment groups."""
    with db.session.begin_nested():
        accounts = [
            RemoteAccount.create(1, 'dev', dict(groups=['cms-members'])),
            RemoteAccount.create(2, 'dev', dict(groups=['cms-members'])),
            RemoteAccount.create(3, 'dev', dict(groups=['alice-member'])),
            RemoteAccount.create(5, 'dev', dict(groups=['atlas-active-members-all'])),
            RemoteAccount.create(8, 'dev', dict(groups=['faser-all'])),
            RemoteAccount.create(7, 'dev', dict(groups=['lhcb-general']))
        ]

    db.session.commit()
    return accounts


@pytest.fixture()
def superuser(db, clear_caches):
    """Create superuser."""
    superuser = create_user_with_access(db.session, 'superuser@cern.ch',
                                        'superuser-access')

    db.session.commit()

    return superuser


@pytest.fixture()
def clear_caches():
    yield
    get_user_email_by_id.cache_clear()
    get_role_name_by_id.cache_clear()
    resolve_schema_by_url.cache_clear()


@pytest.fixture
def es(base_app):
    """Provide Search access."""
    list(current_search.delete(ignore=[400, 404]))
    current_search_client.indices.delete(index='*')
    list(current_search.create())
    current_search_client.indices.refresh()
    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='*')


@pytest.fixture
def create_schema(db, clear_caches):
    """Returns function to add a schema to db."""
    def _add_schema(name,
                    deposit_schema=None,
                    is_indexed=True,
                    use_deposit_as_record=True,
                    version="1.0.0",
                    config=None,
                    schema_record_permissions=None,
                    **kwargs):
        """Add new schema into db."""
        default_json = {'title': {'type': 'string'}}

        try:
            schema = Schema.get(name, version)
        except JSONSchemaNotFound:
            schema = Schema(name=name,
                            version=version,
                            is_indexed=is_indexed,
                            use_deposit_as_record=use_deposit_as_record,
                            deposit_schema=deposit_schema or default_json,
                            config=config,
                            **kwargs)
            db.session.add(schema)
            db.session.commit()

            if schema_record_permissions:
                schema.modify_record_permissions(schema_record_permissions)
            if not schema.experiment:
                schema.add_read_access_for_all_users()
                db.session.commit()
        return schema

    yield _add_schema


def bearer_auth(token):
    """Create authentication headers (with a valid oauth2 token)."""
    return [('Authorization', 'Bearer {0}'.format(token['token'].access_token))
            ]


@pytest.fixture
def auth_headers_for_example_user(example_user, auth_headers_for_user):
    return auth_headers_for_user(example_user)


@pytest.fixture
def auth_headers_for_user(base_app, db):
    """Return method to generate write token for user."""
    def _write_token(user):
        """Return json headers with write oauth token for given user."""
        client_ = Client.query.filter_by(user_id=user.id).first()

        if not client_:
            client_ = Client(
                client_id=user.id,
                client_secret='client_secret_{}'.format(user.id),
                name='client_test_{}'.format(user.id),
                description='',
                is_confidential=False,
                user_id=user.id,
                _redirect_uris='',
                _default_scopes='',
            )
            db.session.add(client_)

        token_ = Token.query.filter_by(user_id=user.id).first()

        if not token_:
            token_ = Token(
                client_id=client_.client_id,
                user_id=user.id,
                access_token='dev_access_{}'.format(user.id),
                refresh_token='dev_refresh_{}'.format(user.id),
                expires=datetime.utcnow() + timedelta(hours=10),
                is_personal=False,
                is_internal=True,
                _scopes=write_scope.id,
            )
            db.session.add(token_)
        db.session.commit()

        return bearer_auth(
            dict(token=token_,
                 auth_header=[
                     ('Authorization',
                      'Bearer {0}'.format(token_.access_token)),
                 ]))

    return _write_token


def get_default_mapping(name, version):
    mapping = {
        "mappings": {
            "properties": {
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
    }
    return mapping


@pytest.fixture
def auth_headers_for_superuser(superuser, auth_headers_for_user):
    return auth_headers_for_user(superuser)


@pytest.fixture
def json_headers():
    """JSON headers."""
    return [('Content-Type', 'application/json'),
            ('Accept', 'application/json')]


@pytest.fixture
def create_deposit(app, db, es, location, create_schema):
    """Returns function to create a new deposit."""
    def minimal_metadata(url):
        return {'$schema': url}

    def _create_deposit(user,
                        schema_name,
                        metadata=None,
                        experiment=None,
                        files={},
                        publish=False,
                        mapping=None,
                        deposit_schema=None,
                        version="1.0.0"):
        """Create a new deposit for given user and schema name.

        e.g cms-analysis-v0.0.1,
        with minimal metadata defined for this schema type.
        """
        # create schema for record
        with app.test_request_context():
            default_mapping = mapping if mapping \
                else get_default_mapping(schema_name, version)

            schema = create_schema(schema_name,
                                   experiment=experiment,
                                   deposit_schema=deposit_schema,
                                   deposit_mapping=default_mapping,
                                   version=version)
            deposit_schema_url = current_jsonschemas.path_to_url(
                schema.deposit_path)

            metadata = metadata or minimal_metadata(deposit_schema_url)
            login_user(user)
            id_ = uuid4()
            deposit_minter(id_, metadata)
            deposit = Deposit.create(metadata, id_=id_)

            for k, v in files.items():
                deposit.files[k] = v
            if files:
                deposit.commit()

            db.session.commit()

        if publish:
            deposit.publish()
            _, record = deposit.fetch_published()
            RecordIndexer().index(record)

            current_search.flush_and_refresh(schema.record_index)

        current_search.flush_and_refresh(schema.deposit_index)

        return Deposit.get_record(deposit.id)

    yield _create_deposit


@pytest.fixture
def deposit(example_user, create_deposit):
    """New deposit with files."""
    return create_deposit(
        example_user,
        'cms-analysis',
        experiment='CMS',
    )


@pytest.fixture
def record(example_user, create_deposit):
    """Example record."""
    return create_deposit(example_user,
                          'cms-analysis-v0.0.1',
                          experiment='CMS',
                          publish=True)


@pytest.fixture
def record_metadata(deposit):
    """Example record metadata."""
    return deposit.get_record_metadata()


@pytest.fixture
def schema(db):
    """Example schema."""
    schema = Schema(name='test-schema', fullname='Test Schema')
    db.session.add(schema)
    db.session.commit()
    return schema


@pytest.fixture
def cms_user_me_data(users):
    """CMS user data returned by /me endpoint."""
    return {
        "collaborations": [
            "CMS",
        ],
        "current_experiment": "CMS",
        "deposit_groups": [{
            "deposit_group": "cms-questionnaire",
            "description": "Create a CMS Questionnaire",
            "name": "CMS Questionnaire"
        }, {
            "deposit_group": "cms-analysis",
            "description": "Create a CMS Analysis (analysis metadata, \
                            workflows, etc)",
            "name": "CMS Analysis"
        }],
        "email": users['cms_user'].email,
        "id": users['cms_user'].id
    }


@pytest.fixture
def das_datasets_index(es):
    """Example datasets under DAS datasets index."""
    source = [{
        'name': '/dataset1/run1/AOD'
    }, {
        'name': '/dataset1/run2/AOD'
    }, {
        'name': '/dataset2/run1/RECO'
    }, {
        'name': '/dataset2/run2/RECO'
    }, {
        'name': '/dataset3/run1/AODSIM'
    }, {
        'name': '/dataset3/run2/AODSIM'
    }, {
        'name': '/dataset4/run1/AODSIM'
    }, {
        'name': '/dataset4/run2/AODSIM'
    }, {
        'name': '/dataset5/run1/ALCARECO'
    }, {
        'name': '/dataset6/run1/SIM-GEN-AOD'
    }
    ]

    cache_das_datasets_in_es_from_file(source)

    current_search.flush_and_refresh(DAS_DATASETS_ES_CONFIG['alias'])


@pytest.fixture
def das_datasets_index_main(es):
    """Example datasets under DAS datasets index."""
    source = [{
        'name': '/dataset1/run1'
    }, {
        'name': '/dataset1/run2'
    }, {
        'name': '/dataset2'
    }, {
        'name': '/another_dataset'
    }]

    cache_das_datasets_in_es_from_file(source)

    current_search.flush_and_refresh(DAS_DATASETS_ES_CONFIG['alias'])


@pytest.fixture
def cms_triggers_index(es):
    """Example triggers under CMS triggers index."""
    source = [
        {
            'dataset': 'Dataset1',
            'year': 2011,
            'trigger': 'Trigger1'
        },
        {
            'dataset': 'Dataset1',
            'year': 2012,
            'trigger': 'Trigger_2'
        },
        {
            'dataset': 'dataset2',
            'year': 2012,
            'trigger': 'Trigger_2'
        },
        {
            'dataset': 'Dataset1',
            'year': 2011,
            'trigger': 'Another_Trigger'
        },
        {
            'dataset': 'Dataset2',
            'year': 2011,
            'trigger': 'Trigger1'
        },
        {
            'dataset': 'Dataset2',
            'year': 2011,
            'trigger': 'Trigger2'
        },
        {
            'dataset': 'Dataset2',
            'year': 2011,
            'trigger': 'Another_One'
        },

        # some duplicates to check aggregations
        {
            'dataset': 'Dataset1',
            'year': 2010,
            'trigger': 'Trigger1'
        },
        {
            'dataset': 'Dataset1',
            'year': 2010,
            'trigger': 'Trigger_2'
        }
    ]

    cache_cms_triggers_in_es_from_file(source)
    current_search.flush_and_refresh(CMS_TRIGGERS_ES_CONFIG['alias'])


@pytest.fixture
def get_git_attributes(app, users, auth_headers_for_user, create_deposit):
    owner = users['cms_user']
    deposit = create_deposit(owner, 'test-analysis-v0.0.1')
    pid = deposit['_deposit']['id']
    bucket = deposit.files.bucket
    headers = auth_headers_for_user(owner)

    return owner, deposit, pid, bucket, headers


@pytest.fixture
def get_record_pid_uuid(app, users, create_deposit, create_schema):
    owner = users['cms_user']
    create_schema('deposits/records/test-v0.0.1', experiment='CMS')
    deposit = create_deposit(owner, 'test-v0.0.1')
    pid = deposit['_deposit']['id']

    resolver = Resolver(pid_type='depid',
                        object_type='rec',
                        getter=lambda x: x)
    _, uuid = resolver.resolve(pid)
    return pid, str(uuid)


def create_user_with_access(session, username, action=None):
    user = _datastore.find_user(email=username)

    if not user:
        user = create_test_user(email=username, password='pass')

    if action:
        session.add(ActionUsers.allow(ActionNeed(action), user=user))

    return user


def assign_egroup_to_experiment(egroup_name, exp):
    role = _datastore.find_or_create_role(egroup_name)
    exp_need = exp_need_factory(exp)

    db_.session.add(ActionRoles.allow(exp_need, role=role))

    db_.session.commit()

    return role


def add_role_to_user(user, rolename):
    role = _datastore.find_or_create_role(rolename)

    _datastore.add_role_to_user(user, role)


@pytest.fixture
def github_repo(db, github_token):
    repo = GitRepository(
        external_id=12345,
        host='github.com',
        owner='owner',
        name='repository',
    )
    db.session.add(repo)
    db.session.commit()
    return repo


@pytest.fixture()
def clean_schema_acceess_cache(base_app, db, github_repo):
    from cap.modules.schemas.imp import (get_cached_indexed_schemas_for_user_create,
                                       get_cached_indexed_schemas_for_user_read,
                                       get_cached_indexed_record_schemas_for_user_create,
                                       get_cached_indexed_record_schemas_for_user_read
                                       )
    get_cached_indexed_schemas_for_user_create.delete_memoized()
    get_cached_indexed_schemas_for_user_read.delete_memoized()
    get_cached_indexed_record_schemas_for_user_create.delete_memoized()
    get_cached_indexed_record_schemas_for_user_read.delete_memoized()
    yield
    get_cached_indexed_schemas_for_user_create.delete_memoized()
    get_cached_indexed_schemas_for_user_read.delete_memoized()
    get_cached_indexed_record_schemas_for_user_create.delete_memoized()
    get_cached_indexed_record_schemas_for_user_read.delete_memoized()



@pytest.fixture
def github_release_webhook(db, github_repo):
    webhook = GitWebhook(event_type='release',
                         repo_id=github_repo.id,
                         external_id=666,
                         secret='mysecretsecret')
    db.session.add(webhook)
    db.session.commit()
    return webhook


@pytest.fixture
def github_push_webhook_sub(db, github_repo, deposit, example_user):
    webhook = GitWebhook(event_type='push',
                         repo_id=github_repo.id,
                         external_id=666,
                         branch='mybranch',
                         secret='mysecretsecret')
    db.session.add(webhook)
    subscriber = GitWebhookSubscriber(record_id=deposit.id,
                                      user_id=example_user.id)
    webhook.subscribers.append(subscriber)
    db.session.commit()
    return subscriber


@pytest.fixture
def github_release_webhook_sub(db, deposit, github_repo, example_user):
    webhook = GitWebhook(event_type='release',
                         repo_id=github_repo.id,
                         external_id=666,
                         secret='mysecretsecret')
    db.session.add(webhook)
    subscriber = GitWebhookSubscriber(record_id=deposit.id,
                                      user_id=example_user.id)
    webhook.subscribers.append(subscriber)
    db.session.commit()
    return subscriber


@pytest.fixture
def gitlab_repo(db, gitlab_token):
    repo = GitRepository(
        external_id=12345,
        host='gitlab.cern.ch',
        owner='owner_name',
        name='myrepository',
    )
    db.session.add(repo)
    db.session.commit()
    return repo


@pytest.fixture
def gitlab_push_webhook_sub(db, gitlab_repo, deposit, example_user):
    webhook = GitWebhook(event_type='push',
                         repo_id=gitlab_repo.id,
                         external_id=666,
                         branch='mybranch',
                         secret='mysecretsecret')
    db.session.add(webhook)
    subscriber = GitWebhookSubscriber(record_id=deposit.id,
                                      user_id=example_user.id)
    webhook.subscribers.append(subscriber)
    db.session.commit()
    return subscriber


@pytest.fixture
def gitlab_release_webhook_sub(db, deposit, gitlab_repo, example_user):
    webhook = GitWebhook(event_type='release',
                         repo_id=gitlab_repo.id,
                         external_id=666,
                         secret='mysecretsecret')
    db.session.add(webhook)
    subscriber = GitWebhookSubscriber(record_id=deposit.id,
                                      user_id=example_user.id)
    webhook.subscribers.append(subscriber)
    db.session.commit()
    return subscriber


@pytest.fixture
def github_token(db, example_user):
    token = OAuth2Token(name='github',
                        user_id=example_user.id,
                        token_type='bearer',
                        access_token='some-token')
    db.session.add(token)
    db.session.commit()
    return token


@pytest.fixture
def example_user(users):
    return users['cms_user']


@pytest.fixture
def gitlab_token(db, example_user):
    token = OAuth2Token(name='gitlab',
                        user_id=example_user.id,
                        token_type='bearer',
                        access_token='some-token')
    db.session.add(token)
    db.session.commit()
    return token


@pytest.fixture
def git_repo_tar():
    return b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03\xed\xd4\xc1N\x830\x18' \
            b'\x07p\xce>\x05/\x80\xc2\xb7\xb6\xc0a\x07\x13w\xf4\xe2\x0b,-\x94' \
            b'\xb9\x04(i\xbbE\xdf\xde\xa2^\xc4\xa0\x99a1\xcb\xfe\xbfKIK' \
            b'\xd2~\xf9\xf7\xeb _\xb6\xbb\xd6(\xd9n\x9f\xb5\xac\xb5\x8d\x96' \
            b'\x97\x06B\x88\xf71\x98\x8ea\x91E\xd9\x8a\x0bN\x82\xe7\x9c\x87' \
            b'\xf9\x8c\xf1\x15\x8fvg8\xcb7\x07\xe7\xa5\r[Zc\xfcO\xff\xfd' \
            b'\xb6>-\xeeBp\x8a+\xd3u\xba\xf7kE*WT\x88F5\xacH\xd3\xa6P\xaa\xccKQ' \
            b'\xc9\xb4.\xa9\x0c\x93\xa9*$k\xea\x9b\xff>3,\xa7\xd2\xb6\x97' \
            b'\xbdl_\xdd\xde\rV;m\x8f\xd2\xefM\x9fx\xed|b\xf5`\x92\xcf{q\xf7' \
            b'\xe7=\xc6~\xc8s>\xdf\xff\xe1\xfbk\xffSF\xc4"\xbe`\x9d\xb3\xae' \
            b'\xbc\xffO\xc8\xffis\xff\xf0\xb8\xb9\xed\xeaS\xf7\xf8x\xff\xd9|' \
            b'\xfeD\xd3\xfc\x89\x8d\xf7\xe5\x1c\x05O]y\xfec\xcc\xf1\x18s\xdc' \
            b'\x18\x1bWr\xc0\xeb\x0e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
            b'\x00\x00\x00\x00pq\xde\x00h\xd6\xb3\xb6\x00(\x00\x00'


@pytest.fixture
def file_tar():
    return b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03+I-.Q(J-\xc8WH' \
            b'\xcb/RHN,\xe0\x02\x00\xeb\xd5!\xe0\x12\x00\x00\x00'
