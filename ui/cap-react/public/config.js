(() => {
  const CONFIG = {
    ENV: null,
    PIWIK_URL: null,
    PIWIK_SITE_ID: null,
    SENTRY_UI_DSN: null,
    ENABLE_E2E: false,
  };

  Object.defineProperty(window, "CONFIG", { value: Object.freeze(CONFIG) });
})();
