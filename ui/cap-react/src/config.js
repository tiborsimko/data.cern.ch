import * as Sentry from "@sentry/react";

export function getConfigFor(configKey, notSetValue = null) {
  try {
    return window.CONFIG[configKey] != null
      ? window.CONFIG[configKey]
      : notSetValue;
  } catch (error) {
    Sentry.captureException(error);
    console.error(error); // eslint-disable-line no-console
    return notSetValue;
  }
}
