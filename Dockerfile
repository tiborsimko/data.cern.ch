# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Base cap image to install on with base python 3.10

FROM python:3.10.10

# Certficates configuartion
ENV PYTHONBUFFERED=0 \
    SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt" \
    REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt" \
    PATH="/root/.local/bin:${PATH}" \
    POETRY_VIRTUALENVS_CREATE=false
COPY docker/base/CERN_Root_Certification_Authority_2.pem /usr/local/share/ca-certificates/CERN_Root_Certification_Authority_2.crt

# Install system dependencies
RUN update-ca-certificates && pip config set global.cert "${REQUESTS_CA_BUNDLE}"
RUN curl -s -L http://cern.ch/linux/docs/krb5.conf -o /etc/krb5.conf
RUN curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc libffi-dev locales libxslt-dev libxml2-dev libssl-dev build-essential python3-dev libldap2-dev libsasl2-dev ldap-utils krb5-user git redis \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install Invenio
ENV WORKING_DIR=/opt/cap
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
ENV CAP_FILES_DIR=${WORKING_DIR}/src/var

# Debug off by default
ARG DEBUG=False
ENV DEBUG=${DEBUG}

# ENABLE_E2E False by default
ARG ENABLE_E2E=False
ENV ENABLE_E2E=${ENABLE_E2E}

# copy everything inside /src
RUN mkdir -p ${WORKING_DIR}/src
COPY ./ ${WORKING_DIR}/src
WORKDIR ${WORKING_DIR}/src

ADD setup.py setup.py
ADD cap/version.py cap/version.py

RUN python -m site
RUN python -m site --user-site

# Install/create static files
RUN mkdir -p ${INVENIO_INSTANCE_PATH}
RUN mkdir -p ${CAP_FILES_DIR}

RUN pip install -e .

RUN cat ./docker/base/CERN_Root_Certification_Authority_2.pem >>  /usr/local/lib/python3.10/site-packages/certifi/cacert.pem

# Copy uwsgi config files
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}

ARG APP_GITHUB_OAUTH_ACCESS_TOKEN
ENV APP_GITHUB_OAUTH_ACCESS_TOKEN=${APP_GITHUB_OAUTH_ACCESS_TOKEN}
ARG APP_GITLAB_OAUTH_ACCESS_TOKEN
ENV APP_GITLAB_OAUTH_ACCESS_TOKEN=${APP_GITLAB_OAUTH_ACCESS_TOKEN}

RUN pip install gunicorn

# Set folder permissions
RUN chgrp -R 0 ${WORKING_DIR} ${CAP_FILES_DIR} && \
    chmod -R g=u ${WORKING_DIR} ${CAP_FILES_DIR}

RUN useradd invenio --uid 1000 --gid 0 && \
    chown -R invenio:root ${WORKING_DIR} ${CAP_FILES_DIR} && \
    chown -R invenio:root /usr/local/lib/python3.10/site-packages/certifi
USER 1000
