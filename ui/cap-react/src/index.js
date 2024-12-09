import { createRoot } from "react-dom/client";
import store, { history } from "./store/configureStore";
import Root from "./antd/Root";
import * as Sentry from "@sentry/react";
import { getConfigFor } from "./config";

// import "antd/dist/reset.css";
import "./style.less";

const SENTRY_UI_DSN = getConfigFor("SENTRY_UI_DSN");
const ENV = getConfigFor("ENV");

if (SENTRY_UI_DSN && ENV) {
  Sentry.init({
    dsn: SENTRY_UI_DSN,
    environment: ENV,
    release: import.meta.env.VITE_SENTRY_RELEASE,
  });
}

const container = document.getElementById("app");
const root = createRoot(container);

root.render(<Root store={store} history={history} />);
