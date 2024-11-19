# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# CERN Analysis Preservation is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file
# for more details.
"""CAP config."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'check-manifest>=0.35',
    # 'coverage>=5.2.1',
    # 'isort>=4.3',
    # 'mock>=2.0.0',
    # 'pydocstyle>=2.0.0',
    # 'pytest-cov==2.5.1',
    # 'pytest-invenio>=1.0.5,<=1.3.4',
    # 'pytest-mock>=1.6.0',
    # 'pytest-pep8>=1.0.6',
    # 'pytest-random-order>=0.5.4',
    # 'pytest==5.3.5',
    # 'responses==0.10.6',
    'pytest-cov>=3',
    'pytest>=7',
    'responses>=0.22.0',
]

extras_require = {'docs': ['Sphinx>=1.5.1'], 'tests': tests_require}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

extras_require['ldap'] = ['python-ldap>=2.4.39']

# Do not include in all requirement
extras_require['xrootd'] = [
    # 'invenio-xrootd>=1.0.0a6',
    # 'xrootdpyfs>=0.1.5',
]

setup_requires = ['Babel>=2.4.0', 'pytest-runner>=3.0.0,<5']

install_requires = [
    # CAP Base
    'Flask==1.1',
    'click==8.0.0',
    'jinja2==3.0.3',
    'itsdangerous==2.0.1',
    'werkzeug==1.0.1',
    'Flask-Caching==1.5.0',
    'Flask-Debugtoolbar',
    'flask-wtf==0.15.1',
    'flask-login==0.4.1',

    # CAP specific libraries
    'jsonref>=1.0.0',
    'jsonresolver>=0.3.2',
    'PyGithub>=1.35',
    'python-gitlab>=1.0.2',
    'python-ldap==3.1.0',
    'python-cern-sso-krb==1.3.3',
    'gssapi>=1.7.3',
    'Authlib==0.15.1',
    'uWSGI==2.0.21',
    'uwsgi-tools==1.1.1',
    'uwsgitop==0.10',
    'webargs==5.5.0',
    'gspread==3.7.0',
    'paramiko==2.7.1',
    'cachetools==3.1.0',
    'urllib3==1.26',
    'coolname==1.1.0',
    'requests-gssapi>=1.2.3',
    'swagger-spec-validator==2.7.6',
    'prometheus-flask-exporter==0.20.3',
    'suds==1.1.2',
    'wtforms==2.2.1',
    'beautifulsoup4>=4',
    'pandas>=1.5',
    'marshmallow==2.17.0',
    'reana-client==0.9.3',
    'reana-commons[yadage,snakemake]',
    'jsonschema-specifications',

    # Invenio Base Deps
    'invenio-base==1.2.5',
    'invenio-admin==1.1.2',
    'invenio-assets==1.1.3',
    'invenio-formatter==1.0.2',
    'invenio-mail==1.0.2',
    'invenio-rest==1.1.2',
    'invenio-theme==1.1.4',
    'invenio-celery@git+https://github.com/cernanalysispreservation/invenio-celery.git@mock/v1.1.1#egg=invenio-celery',
    'invenio-logging[sentry,sentry-sdk] @ git+https://github.com/inveniosoftware/invenio-logging@94bc56117593eae62ba975d576e8c7b991311c0d',

    # Invenio Auth Deps
    'invenio-access==1.3.0',
    'invenio-accounts==1.1.1',
    'invenio-oauth2server==1.0.4',
    'invenio-oauthclient @ git+https://github.com/cernanalysispreservation/invenio-oauthclient.git@v1.1.3-openid',
    'invenio-userprofiles @ git+https://github.com/cernanalysispreservation/invenio-userprofiles.git@v1.0.1',

    # Invenio Metadata Deps
    'invenio-indexer @ git+https://github.com/cernanalysispreservation/invenio-indexer.git@os-2-new',
    'invenio-jsonschemas @ git+https://github.com/cernanalysispreservation/invenio-jsonschemas.git@v1.0.1',
    'invenio-oaiserver@git+https://github.com/cernanalysispreservation/invenio-oaiserver.git@os-2-new',
    'invenio-pidstore==1.1.0',
    'invenio-records-rest@git+https://github.com/cernanalysispreservation/invenio-records-rest.git@os-2-new#egg=invenio-records-rest',
    'invenio-records-ui==1.0.1',
    'invenio-records==1.3.0',
    'invenio-search-ui==1.1.1',
    'invenio-search @ git+https://github.com/cernanalysispreservation/invenio-search.git@mock/v1.2.3#egg=invenio-search[opensearch2]',

    # Invenio Files deps
    'invenio-files-rest @ git+https://github.com/cernanalysispreservation/invenio-files-rest.git@mock/v1.0.5#egg=invenio-files-rest',
    'invenio-records-files @ git+https://github.com/cernanalysispreservation/invenio-records-files.git@new#egg=invenio-records-files',

    # Database deps
    'invenio-db[postgresql,versioning]==1.0.13',

    # Invenio required deps
    'invenio-deposit @ git+https://github.com/cernanalysispreservation/invenio-deposit.git@os-2',
    'invenio-accounts-rest==1.0.0a4',
    'invenio-query-parser @ git+https://github.com/cernanalysispreservation/invenio-query-parser.git@os',
    'invenio[auth,base,metadata,postgresql]==3.2.0',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('cap', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='cap',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='cap cern analysis preservation',
    license='MIT',
    author='CERN',
    author_email='analysis-preservation-support@cern.ch',
    url='https://github.com/cernanalysispreservation/analysispreservation.cern.ch',  # noqa
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': ['cap = cap.cli:cli'],
        'invenio_access.actions': [
            'cms_access = '
            'cap.modules.experiments.permissions:cms_access_action',
            'cms_pag_convener_access = '
            'cap.modules.experiments.permissions:cms_pag_convener_action_all',
            'lhcb_access = '
            'cap.modules.experiments.permissions:lhcb_access_action',
            'alice_access = '
            'cap.modules.experiments.permissions:alice_access_action',
            'atlas_access = '
            'cap.modules.experiments.permissions:atlas_access_action',
            # deposit actions
            'deposit_schema_create = '
            'cap.modules.schemas.permissions:deposit_schema_create_action_all',
            'deposit_schema_read = '
            'cap.modules.schemas.permissions:deposit_schema_read_action_all',
            'deposit_schema_update = '
            'cap.modules.schemas.permissions:deposit_schema_update_action_all',
            'deposit_schema_admin = '
            'cap.modules.schemas.permissions:deposit_schema_admin_action_all',
            'deposit_schema_clone = '
            'cap.modules.schemas.permissions:deposit_schema_clone_action_all',
            'deposit_schema_review = '
            'cap.modules.schemas.permissions:deposit_schema_review_action_all',
            'deposit_schema_delete = '
            'cap.modules.schemas.permissions:deposit_schema_delete_action_all',
            'deposit_schema_upload = '
            'cap.modules.schemas.permissions:deposit_schema_upload_action_all',
            # record actions
            'record_schema_create = '
            'cap.modules.schemas.permissions:record_schema_create_action_all',
            'record_schema_read = '
            'cap.modules.schemas.permissions:record_schema_read_action_all',
            'record_schema_update = '
            'cap.modules.schemas.permissions:record_schema_update_action_all',
            'record_schema_admin = '
            'cap.modules.schemas.permissions:record_schema_admin_action_all',
            'record_schema_delete = '
            'cap.modules.schemas.permissions:record_schema_delete_action_all',
            # schema actions
            'schema_object_read = '
            'cap.modules.schemas.permissions:schema_read_action_all',
            'schema_object_admin = '
            'cap.modules.schemas.permissions:schema_admin_action_all',
            'faser_access = '
            'cap.modules.experiments.permissions:faser_access_action',
        ],
        'invenio_base.api_apps': [
            'cap_access = cap.modules.access.ext:CAPAccess',
            'cap_cache = cap.modules.cache.ext:CAPCache',
            'cap_deposit = cap.modules.deposit.ext:CAPDeposit',
            'cap_experiments = cap.modules.experiments.ext:CAPExperiments',
            'cap_fixtures = cap.modules.fixtures.ext:CAPFixtures',
            'cap_xrootd = cap.modules.xrootd.ext:CapXRootD',
            'cap_auth = cap.modules.auth.ext:CAPOAuth',
            'cap_mail = cap.modules.mail.ext:CAPMail',
            'cap_logging = cap.modules.logging.ext:CAPLogging',
        ],
        'invenio_base.api_blueprints': [
            'cap = cap.views:blueprint',
            'cap_user = cap.modules.user.views:user_blueprint',
            'cap_oauth2server_settings = '
            ' cap.modules.oauth2server.views.settings:blueprint',
            'cap_oauth2server_server = '
            ' cap.modules.oauth2server.views.server:blueprint',
            'cap_atlas = cap.modules.experiments.views.atlas:atlas_bp',
            'cap_lhcb = cap.modules.experiments.views.lhcb:lhcb_bp',
            'cap_cms = cap.modules.experiments.views.cms:cms_bp',
            'cap_workflows = cap.modules.workflows.views:workflows_bp',
            'cap_services = cap.modules.services.views:blueprint',
            'cap_schemas = cap.modules.schemas.views:blueprint',
            'cap_auth = cap.modules.auth.views:blueprint',
            'cap_repos = cap.modules.repos.views:repos_bp',
            'invenio_oauthclient = invenio_oauthclient.views.client:blueprint',
        ],
        'invenio_celery.tasks': [
            # 'cap_deposit = cap.modules.deposit.loaders',
            'cap_cms = cap.modules.experiments.tasks.cms',
            'cap_lhcb = cap.modules.experiments.tasks.lhcb',
        ],
        'invenio_search.mappings': [],
        'invenio_pidstore.minters': [
            'cap_record_minter = '
            'cap.modules.records.minters:cap_record_minter',
            'cap_deposit_minter = '
            'cap.modules.deposit.minters:cap_deposit_minter',
        ],
        'invenio_pidstore.fetchers': [
            'cap_record_fetcher = '
            'cap.modules.records.fetchers:cap_record_fetcher',
            'cap_deposit_fetcher = '
            'cap.modules.deposit.fetchers:cap_deposit_fetcher',
        ],
        'invenio_records.jsonresolver': [
            'schemas = cap.modules.schemas.resolvers',
        ],
        'invenio_db.models': [
            'cap_reana_model = cap.modules.workflows.models',
            'analysis_schema_model = cap.modules.schemas.models',
            'status_check_model = cap.modules.services.models',
            'auth = cap.modules.auth.models',
            'repos_model = cap.modules.repos.models',
        ],
        'invenio_db.alembic': ['cap = cap:alembic'],
        'invenio_config.module': ['cap = cap.config'],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 3',
    ],
)
