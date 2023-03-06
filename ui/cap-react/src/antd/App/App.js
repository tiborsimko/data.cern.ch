import React, { useEffect } from "react";
import { Switch, Route } from "react-router-dom";
import PropTypes from "prop-types";
import "./App.less";
import WelcomePage from "../welcome";
import IndexPage from "../index/IndexPage";

import AboutPage from "../about";
import PolicyPage from "../policy";
import SchemasPage from "../schemas";

import noRequireAuth from "../auth/NoAuthorizationRequired";
import requireAuth from "../auth/AuthorizationRequired";

import Header from "../partials/Header";
import Footer from "../partials/Footer";

import DocumentTitle from "../partials/DocumentTitle";
import { Layout, Row, Spin } from "antd";

import Loadable from "react-loadable";
import { HOME, WELCOME, ABOUT, POLICY, CMS, SCHEMAS } from "../routes";
import Loading from "../routes/Loading";
import ErrorPage from "../util/ErrorPage";
import * as Sentry from "@sentry/react";
import useTrackPageViews from "../hooks/useTrackPageViews";

const CMSIndex = Loadable({
  loader: () => import("../admin"),
  loading: Loading,
  delay: 300,
});

const App = ({ initCurrentUser, loadingInit, history }) => {
  useEffect(() => {
    initCurrentUser(history.location.state);
  }, []);

  useTrackPageViews(history.location.pathname);

  if (loadingInit)
    return (
      <Layout className="__mainLayout__">
        <Row style={{ height: "100%" }} align="middle" justify="center">
          <Spin size="large" />
        </Row>
      </Layout>
    );

  return (
    <DocumentTitle title="Dashboard">
      <Sentry.ErrorBoundary
        fallback={({ error, componentStack }) => (
          <ErrorPage error={error} componentStack={componentStack} />
        )}
      >
        <Layout className="__mainLayout__">
          <Layout.Header className="__mainHeader__">
            <Header />
          </Layout.Header>
          <Layout.Content className="__mainContent__">
            <Switch>
              <Route path={WELCOME} component={noRequireAuth(WelcomePage)} />
              <Route path={ABOUT} component={AboutPage} />
              <Route path={POLICY} component={PolicyPage} />
              <Route path={CMS} component={CMSIndex} />
              <Route path={SCHEMAS} component={SchemasPage} />
              <Route path={HOME} component={requireAuth(IndexPage)} />
            </Switch>
          </Layout.Content>
          <Layout.Footer>
            <Footer />
          </Layout.Footer>
        </Layout>
      </Sentry.ErrorBoundary>
    </DocumentTitle>
  );
};

App.propTypes = {
  initCurrentUser: PropTypes.func,
  loadingInit: PropTypes.bool,
  history: PropTypes.object,
};

export default App;
