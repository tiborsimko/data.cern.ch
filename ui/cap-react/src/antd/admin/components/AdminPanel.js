import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import Header from "../containers/Header";
import DocumentTitle from "../../partials/DocumentTitle";
import SchemaWizard from "../components/SchemaWizard";
import Notifications from "../notifications/containers/Notifications";
import { FloatButton, Layout } from "antd";
import Joyride, { STATUS } from "react-joyride";
import { steps } from "../utils/tour/admin";
import TourTooltip from "../utils/tour/TourTooltip";
import { CarOutlined } from "@ant-design/icons";
import useStickyState from "../../hooks/useStickyState";
import { PRIMARY_COLOR } from "../../utils/theme";
import { isEmpty } from "lodash-es";
import { initFormuleSchemaWithNotifications } from "../utils";
import Permissions from "../permissions/Permissions";

const AdminPanel = ({ location, match, getSchema, loading, formuleState }) => {
  useEffect(() => {
    let { schema_name, schema_version } = match.params;

    if (schema_name == "new") {
      // If the schema hasn't been initialized yet (i.e. the user has navigated directly to /new), initialize it
      if (isEmpty(formuleState?.current?.schema)) {
        initFormuleSchemaWithNotifications();
      }
      // Otherwise do nothing as it means it's been already initialized in CreateForm or DropDownBox
    } else {
      getSchema(schema_name, schema_version);
    }
  }, []);

  const [display, setDisplay] = useState("builder");

  const [tourDone, setTourDone] = useStickyState(false, "tourDone");

  const getPageTitle = () =>
    location.pathname.includes("notifications")
      ? "Notifications"
      : location.pathname.includes("permissions")
      ? "Permissions"
      : "Form Builder";

  const getDisplay = () => {
    switch (display) {
      case "notifications":
        return <Notifications />;
      case "permissions":
        return <Permissions isNew={match.params.schema_name === "new"} />;
      default:
        return (
          <SchemaWizard
            loading={isEmpty(formuleState?.current?.schema) || loading}
          />
        );
    }
  };

  return (
    <DocumentTitle title={getPageTitle()}>
      <Layout style={{ height: "100%", padding: 0 }}>
        <Header display={display} setDisplay={setDisplay} />
        <Layout.Content>
          <Joyride
            steps={steps}
            continuous
            disableCloseOnEsc
            showProgress
            showSkipButton
            hideCloseButton
            spotlightPadding={0}
            tooltipComponent={joyrideProps => (
              <TourTooltip total={steps.length} {...joyrideProps} />
            )}
            run={!tourDone && display != "notifications"}
            spotlightClicks
            callback={({ status }) =>
              [STATUS.FINISHED, STATUS.SKIPPED].includes(status) &&
              setTourDone(true)
            }
            styles={{
              options: { primaryColor: PRIMARY_COLOR },
              spotlight: { borderRadius: 0 },
            }}
          />
          {getDisplay()}
          <FloatButton
            icon={<CarOutlined />}
            type="primary"
            shape="square"
            description="Tour"
            onClick={() => setTourDone(false)}
          />
        </Layout.Content>
      </Layout>
    </DocumentTitle>
  );
};

AdminPanel.propTypes = {
  match: PropTypes.object,
  location: PropTypes.object,
  getSchema: PropTypes.func,
  loading: PropTypes.bool,
};

export default AdminPanel;
