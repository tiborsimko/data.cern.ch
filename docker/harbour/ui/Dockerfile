FROM node:18-alpine AS build

RUN apk add --no-cache git

ENV WORKING_DIR=/tmp/cap

WORKDIR $WORKING_DIR

ARG SENTRY_URL
ARG SENTRY_ORG
ARG SENTRY_PROJECT
ARG SENTRY_AUTH_TOKEN
ARG SENTRY_RELEASE

ENV SENTRY_URL=$SENTRY_URL
ENV SENTRY_ORG=$SENTRY_ORG
ENV SENTRY_PROJECT=$SENTRY_PROJECT
ENV SENTRY_AUTH_TOKEN=$SENTRY_AUTH_TOKEN
ENV VITE_SENTRY_RELEASE=$SENTRY_RELEASE

RUN mkdir -p ui/cap-react

WORKDIR $WORKING_DIR/ui

# build CAP UI
COPY ./ui ${WORKING_DIR}/ui
RUN yarn install
RUN yarn workspace cap-react build
WORKDIR ${WORKING_DIR}/ui/cap-react
RUN yarn sentry:create-release
RUN yarn sentry:sourcemaps
RUN yarn sentry:finalize-release

# build general docs
COPY ./docs ${WORKING_DIR}/docs
WORKDIR $WORKING_DIR/docs
RUN yarn install
RUN yarn build

# build API docs
RUN git clone https://github.com/cernanalysispreservation/cap-api-docs.git $WORKING_DIR/cap-api-docs/
WORKDIR $WORKING_DIR/cap-api-docs
RUN npm install --maxsockets 1
RUN npm run build

# build client docs
RUN git clone https://github.com/cernanalysispreservation/cap-client.git $WORKING_DIR/cap-client/
WORKDIR $WORKING_DIR/cap-client/docs
RUN yarn install
RUN yarn build


FROM nginx:1.24

ENV WORKING_DIR=/tmp/cap
ENV NGINX_HTML_DIR=/usr/share/nginx/html/
RUN mkdir -p $NGINX_HTML_DIR

# Exclude source maps from the final image
RUN echo *.map >> .dockerignore
COPY ./docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=build ${WORKING_DIR}/ui/cap-react/dist/ $NGINX_HTML_DIR
COPY --from=build ${WORKING_DIR}/docs/_book/ $NGINX_HTML_DIR/docs/general
COPY --from=build ${WORKING_DIR}/cap-api-docs/web_deploy/ $NGINX_HTML_DIR/docs/api
COPY --from=build ${WORKING_DIR}/cap-client/docs/_book/ $NGINX_HTML_DIR/docs/client
