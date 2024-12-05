FROM nginx:1.24


RUN apt-get update
RUN apt-get install -y curl bash


RUN curl -sL https://deb.nodesource.com/setup_18.x  | bash -
RUN apt-get install -y nodejs

RUN apt-get update && apt-get -y install  git python g++ make
RUN npm install --global yarn

ENV WORKING_DIR=/tmp/cap
ENV NGINX_HTML_DIR=/usr/share/nginx/html
ENV NODE_OPTIONS="--max-old-space-size=8192"

RUN mkdir -p $NGINX_HTML_DIR

# We invalidate cache always because there is no easy way for now to detect
# if something in the whole git repo changed. For docker git clone <url> <dir>
# is always the same so it caches it.
ARG CACHE_DATE=$(date)

# get the code at a specific commit
RUN git clone https://github.com/cernanalysispreservation/analysispreservation.cern.ch.git $WORKING_DIR/

WORKDIR $WORKING_DIR/

ARG BRANCH_NAME

RUN echo $BRANCH_NAME

RUN git fetch --all

RUN if [ ! -z $BRANCH_NAME ]; then \
      # run commands to checkout a branch
      echo "Checkout branch $BRANCH_NAME" && \
      git checkout $BRANCH_NAME && \
      git pull origin $BRANCH_NAME; \
    fi

RUN git log -10 --pretty=oneline --decorate

RUN cp -rfp $WORKING_DIR/docker/nginx/nginx.conf /etc/nginx/nginx.conf

WORKDIR $WORKING_DIR/ui

ARG PIWIK_ENV=dev
ARG ENABLE_E2E

ARG CAP_PIWIK_URL
ARG CAP_PIWIK_SITEID_DEV
ARG CAP_PIWIK_SITEID_PROD
ARG CAP_PIWIK_SITEID_QA
ARG CAP_PIWIK_SITEID_TEST

ARG PIWIK_URL
ARG PIWIK_SITEID_DEV
ARG PIWIK_SITEID_PROD
ARG PIWIK_SITEID_QA
ARG PIWIK_SITEID_TEST

RUN echo "" >> $WORKING_DIR/ui/cap-react/.env
RUN echo "" >> $WORKING_DIR/ui/cap-react/.env
RUN echo "PIWIK_URL=$CAP_PIWIK_URL" >> $WORKING_DIR/ui/cap-react/.env
RUN echo "ENABLE_E2E=$ENABLE_E2E" >> $WORKING_DIR/ui/cap-react/.env

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN if [[ $PIWIK_ENV == "dev" ]]; then \
        echo "PIWIK_SITEID=$CAP_PIWIK_SITEID_DEV" >> $WORKING_DIR/ui/cap-react/.env; \
    fi

RUN if [[ $PIWIK_ENV == "prod" ]]; then \
        echo "PIWIK_SITEID=$CAP_PIWIK_SITEID_PROD" >> $WORKING_DIR/ui/cap-react/.env; \
    fi

RUN if [[ $PIWIK_ENV == "qa" ]]; then \
        echo "PIWIK_SITEID=$CAP_PIWIK_SITEID_QA" >> $WORKING_DIR/ui/cap-react/.env; \
    fi

RUN if [[ $PIWIK_ENV == "test" ]]; then \
        echo "PIWIK_SITEID=$CAP_PIWIK_SITEID_TEST" >> $WORKING_DIR/ui/cap-react/.env; \
    fi

RUN echo "=========================="
RUN echo $CAP_PIWIK_SITEID_TEST 
RUN echo $PIWIK_SITEID_TEST
RUN echo "=========================="
RUN less $WORKING_DIR/ui/cap-react/.env
RUN echo "=========================="

RUN yarn config set cache ~/.my-yarn-cache-dir

RUN pwd
RUN yarn install
# RUN yarn upgrade

RUN yarn workspace cap-react build
RUN pwd
RUN ls ./cap-react/dist/*
RUN cp -rfp ./cap-react/dist/* $NGINX_HTML_DIR

# build docs general
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
