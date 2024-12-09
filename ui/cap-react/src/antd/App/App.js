import { Suspense, useEffect } from "react";
import { Switch, Route } from "react-router-dom";
import PropTypes from "prop-types";
import WelcomePage from "../welcome";
import IndexPage from "../index/IndexPage";

import AboutPage from "../about";
import PolicyPage from "../policy";

import noRequireAuth from "../auth/NoAuthorizationRequired";
import requireAuth from "../auth/AuthorizationRequired";

import Header from "../partials/Header";
import Footer from "../partials/Footer";

import DocumentTitle from "../partials/DocumentTitle";
import { Layout, Row, Spin } from "antd";

import { HOME, WELCOME, ABOUT, POLICY, CMS } from "../routes";

import ErrorPage from "../utils/ErrorPage";
import * as Sentry from "@sentry/react";
import useTrackPageViews from "../hooks/useTrackPageViews";
import { lazy } from "react";
import Loading from "../routes/Loading/Loading";
import MessageBanner from "../partials/MessageBanner";
import { FormuleContext } from "react-formule";
import { theme } from "../utils/theme";
import { customFieldTypes, customFields } from "../forms/formuleConfig";
import { isEmpty } from "lodash-es";
import { transformSchema } from "../partials/Utils/schema";
import FormuleErrorBoundary from "./FormuleErrorBoundary";

const AdminPage = lazy(() => import("../admin"));

const App = ({
  initCurrentUser,
  loadingInit,
  history,
  roles,
  synchronizeFormuleState,
  formDataChange,
}) => {
  useEffect(() => {
    initCurrentUser(history.location.state);
  }, []);

  useTrackPageViews(history.location.pathname);

  const handleFormuleStateChange = newState => {
    synchronizeFormuleState(newState);
    const newFormData = { ...newState.formData };
    if (!isEmpty(newFormData)) {
      formDataChange(newFormData);
    }
  };

  const isAdmin =
    roles && (roles.get("isSuperUser") || roles.get("schemaAdmin").size > 0);

  if (loadingInit) {
    return (
      <Layout className="__mainLayout__">
        <Row style={{ height: "100%" }} align="middle" justify="center">
          <Spin size="large" />
        </Row>
      </Layout>
    );
  }

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
            <MessageBanner />
          </Layout.Header>
          <Layout.Content className="__mainContent__">
            <Suspense fallback={<Loading pastDelay />}>
              <FormuleContext
                synchronizeState={handleFormuleStateChange}
                theme={theme}
                customFieldTypes={customFieldTypes}
                customFields={customFields}
                transformSchema={transformSchema}
                errorBoundary={FormuleErrorBoundary}
              >
                <Switch>
                  <Route
                    path={WELCOME}
                    component={noRequireAuth(WelcomePage)}
                  />
                  <Route path={ABOUT} component={AboutPage} />
                  <Route path={POLICY} component={PolicyPage} />
                  {isAdmin && <Route path={CMS} component={AdminPage} />}
                  <Route path={HOME} component={requireAuth(IndexPage)} />
                </Switch>
              </FormuleContext>
            </Suspense>
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
  roles: PropTypes.object,
};

export default App;
