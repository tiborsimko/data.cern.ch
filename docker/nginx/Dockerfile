# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# CERN Analysis Preservation is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

FROM nginx:1.24


RUN apt-get update
RUN apt-get install -y curl bash


RUN curl -sL https://deb.nodesource.com/setup_16.x  | bash -
RUN apt-get install -y nodejs

RUN apt-get update && apt-get -y install  git python g++ make
RUN npm install --global yarn

COPY ./docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./docker/nginx/conf.d/* /etc/nginx/conf.d/
COPY ./docker/nginx/ssl/private/test.key /etc/ssl/private/test.key
COPY ./docker/nginx/ssl/certs/test.crt /etc/ssl/certs/test.crt

ENV WORKING_DIR=/tmp/cap
ENV NGINX_HTML_DIR=/usr/share/nginx/html
ENV NODE_OPTIONS="--max-old-space-size=8192"

RUN mkdir -p $NGINX_HTML_DIR

# We invalidate cache always because there is no easy way for now to detect
# if something in the whole git repo changed. For docker git clone <url> <dir>
# is always the same so it caches it.
ARG CACHE_DATE=$(date)

ARG PIWIK_ENV=dev
ARG CAP_PIWIK_URL
ARG PIWIK_ENV
ARG CAP_PIWIK_SITEID_DEV
ARG CAP_PIWIK_SITEID_PROD

RUN echo "" >> .env
RUN echo "" >> .env
RUN echo "PIWIK_URL=$CAP_PIWIK_URL" >> .env

RUN if [[ $PIWIK_ENV == "dev" ]]; then \
        echo "PIWIK_SITEID=$CAP_PIWIK_SITEID_DEV" >> .env; \
    fi

RUN if [[ $PIWIK_ENV == "prod" ]]; then \
        echo "PIWIK_SITEID=$CAP_PIWIK_SITEID_PROD" >> .env; \
    fi


# build frontend
COPY ./ui/cap-react $WORKING_DIR/ui/
WORKDIR $WORKING_DIR/ui/

RUN yarn config set cache ~/.my-yarn-cache-dir
RUN yarn install
RUN yarn upgrade
RUN yarn build

RUN cp -rfp ./dist/* $NGINX_HTML_DIR


# build docs general
COPY ./docs $WORKING_DIR/docs/
WORKDIR $WORKING_DIR/docs

RUN yarn
RUN yarn build

RUN mkdir -p $NGINX_HTML_DIR/docs/general
RUN cp -rfp ./_book/* $NGINX_HTML_DIR/docs/general


# build docs API
RUN git clone https://github.com/cernanalysispreservation/cap-api-docs.git $WORKING_DIR/cap-api-docs/
WORKDIR $WORKING_DIR/cap-api-docs

RUN npm install
RUN npm run build

RUN mkdir -p $NGINX_HTML_DIR/docs/api
RUN cp -rfp ./web_deploy/* $NGINX_HTML_DIR/docs/api


# build docs client
RUN git clone https://github.com/cernanalysispreservation/cap-client.git $WORKING_DIR/cap-client/
WORKDIR $WORKING_DIR/cap-client/docs

RUN yarn
RUN yarn build

RUN mkdir -p $NGINX_HTML_DIR/docs/client
RUN cp -rfp ./_book/* $NGINX_HTML_DIR/docs/client
