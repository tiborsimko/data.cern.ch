# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
#

FROM python:3.10.10

# Certficates configuartion
ENV PYTHONBUFFERED=0 \
    SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt" \
    REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt" \
    PATH="/root/.local/bin:${PATH}" \
    POETRY_VIRTUALENVS_CREATE=false
COPY CERN_Root_Certification_Authority_2.pem /usr/local/share/ca-certificates/CERN_Root_Certification_Authority_2.crt

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
