import React from "react";
import { Alert, Typography } from "antd";
import * as Sentry from "@sentry/react";

class FormuleError extends Error {
  constructor(message) {
    super(message);
    this.name = "FormuleError";
  }
}

class FormuleErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    const formuleError = new FormuleError(error.message);
    formuleError.stack = error.stack;

    // Needed for Sentry to register the error, since it's inside of an ErrorBoundary
    Sentry.captureException(formuleError, { extra: errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert
          type="error"
          message="Error with form schema"
          description={
            <div style={{ whiteSpace: "normal" }}>
              <Typography.Paragraph ellipsis={{ rows: 12, expandable: true }}>
                Your schema might not be following the{" "}
                <a
                  href="https://json-schema.org/specification"
                  target="_blank"
                  rel="noreferrer"
                >
                  JSONSchema specification
                </a>
                . This usually happens when you have manually modified the JSON
                schema and introduced some errors. Please make sure the schema
                follows the specification and try again.
                <br />
                Notes:
                <ul>
                  <li>
                    When you get this error, you usually want to be looking at
                    clear violations of the JSON Schema principles. For example,
                    list or object fields not containing a type or containing
                    children as direct descendants instead of within a{" "}
                    <code>properties</code>
                    or <code>items</code> object.
                  </li>
                  <li>
                    These errors could also be coming from the uiSchema (e.g.
                    non-existing widget/field).
                  </li>
                  <li>
                    If you need help, please contact support at{" "}
                    <a href="mailto: analysis-preservation-support@cern.ch">
                      analysis-preservation-support@cern.ch
                    </a>
                  </li>
                </ul>
              </Typography.Paragraph>
              <Typography.Text>Detailed error message:</Typography.Text>
              <br />
              <code>{this.state.error.message}</code>
            </div>
          }
        />
      );
    }

    return this.props.children;
  }
}

export default FormuleErrorBoundary;
