import PropTypes from "prop-types";
import { ConnectedRouter } from "connected-react-router";
import { Provider } from "react-redux";
import App from "../antd/App";
import { ConfigProvider } from "antd";
import { MatomoProvider, createInstance } from "@datapunt/matomo-tracker-react";
import { theme } from "./utils/theme";
import { getConfigFor } from "../config";

const PIWIK_URL = getConfigFor("PIWIK_URL");
const PIWIK_SITE_ID = getConfigFor("PIWIK_SITE_ID");

export const matomoInstance =
  PIWIK_URL && PIWIK_SITE_ID
    ? createInstance({
        urlBase: PIWIK_URL,
        siteId: PIWIK_SITE_ID,
      })
    : null;

const Root = ({ store, history }) => {
  return (
    <Provider store={store}>
      <MatomoProvider value={matomoInstance}>
        <ConnectedRouter history={history}>
          <ConfigProvider theme={theme}>
            <App />
          </ConfigProvider>
        </ConnectedRouter>
      </MatomoProvider>
    </Provider>
  );
};

Root.propTypes = {
  store: PropTypes.object.isRequired,
  history: PropTypes.object.isRequired,
};

export default Root;
