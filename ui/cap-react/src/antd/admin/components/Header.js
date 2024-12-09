import { useState } from "react";
import PropTypes from "prop-types";
import {
  Col,
  Menu,
  Modal,
  Row,
  Tabs,
  Grid,
  Popconfirm,
  Typography,
  Button,
  Tooltip,
} from "antd";
import {
  DiffOutlined,
  DownloadOutlined,
  FormOutlined,
  HomeOutlined,
  NotificationOutlined,
  SaveOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { CMS } from "../../routes";
import { CodeViewer } from "react-formule";
import { CodeDiffViewer } from "react-formule";

const { useBreakpoint } = Grid;
const Header = ({
  config,
  pushPath,
  saveSchemaChanges,
  formuleState,
  display,
  setDisplay,
}) => {
  const [diffModal, setDiffModal] = useState(false);
  const screens = useBreakpoint();

  const diffModalTabStyle = {
    overflowX: "scroll",
    overflowY: "auto",
    maxHeight: "calc(100vh - 300px)",
  };

  const formuleCurrentSchema = formuleState?.current?.schema;
  const formuleCurrentUiSchema = formuleState?.current?.uiSchema;

  const _getSchema = () => {
    const fileData = JSON.stringify(
      {
        deposit_schema: formuleCurrentSchema,
        deposit_options: formuleCurrentUiSchema,
        ...config.toJS(),
      },
      null,
      4
    );

    const a = document.createElement("a");
    const file = new Blob([fileData], { type: "text/json" });
    const { name, version } = config.toJS();
    const versionStr = version ? `v${version}` : "";
    a.href = URL.createObjectURL(file);
    a.download = `${
      name || "cap-schema"
    }-export${versionStr}-${Date.now()}.json`;
    a.click();
  };
  const _renderSchemaPreview = schemaPreviewDisplay => {
    let previews = {
      uiSchema: (
        <CodeViewer
          value={JSON.stringify(formuleCurrentUiSchema, null, 2)}
          lang="json"
          height="100%"
          reset
        />
      ),
      schema: (
        <CodeViewer
          value={JSON.stringify(formuleCurrentSchema, null, 2)}
          lang="json"
          height="100%"
          reset
        />
      ),
      uiSchemaDiff: (
        <CodeDiffViewer
          left={JSON.stringify(formuleState?.initial?.uiSchema, null, 2)}
          right={JSON.stringify(formuleCurrentUiSchema, null, 2)}
          lang="json"
          height="100%"
        />
      ),
      schemaDiff: (
        <CodeDiffViewer
          left={JSON.stringify(formuleState?.initial?.schema, null, 2)}
          right={JSON.stringify(formuleCurrentSchema, null, 2)}
          lang="json"
          height="100%"
        />
      ),
    };

    return previews[schemaPreviewDisplay]; //?
  };

  const getMenuItem = (key, label, icon, onClick, className) => ({
    key,
    label: (
      <Tooltip title={!screens.lg && label}>
        <Button
          icon={icon}
          type={key === "save" ? "primary" : "text"}
          onClick={onClick}
          className={className}
        >
          {screens.lg && label}
        </Button>
      </Tooltip>
    ),
    style: { padding: "0 10px 0 0" },
  });

  return (
    <Row align="middle" style={{ color: "#fff" }}>
      <Modal
        open={diffModal}
        onCancel={() => setDiffModal(false)}
        width={1000}
        footer={null}
      >
        <Tabs
          defaultActiveKey="schema"
          items={[
            {
              key: "schema",
              label: "Schema",
              children: _renderSchemaPreview("schema"),
              style: diffModalTabStyle,
            },
            {
              key: "uiSchema",
              label: "UI Schema",
              children: _renderSchemaPreview("uiSchema"),
              style: diffModalTabStyle,
            },
            {
              key: "schemaDiff",
              label: "Schema Diff",
              children: _renderSchemaPreview("schemaDiff"),
              style: diffModalTabStyle,
            },
            {
              key: "uiSchemaDiff",
              label: "UI Schema Diff",
              children: _renderSchemaPreview("uiSchemaDiff"),
              style: diffModalTabStyle,
            },
          ]}
        />
      </Modal>

      <Col xs={4} sm={4} lg={5} order={1}>
        <Menu
          mode="horizontal"
          className="no-bottom-border"
          items={[
            {
              key: "admin",
              label: (
                <Popconfirm
                  title={
                    <Typography.Text>
                      Are you sure you want to go back to the admin screen?
                      <br />
                      You will lose all unsaved changes
                    </Typography.Text>
                  }
                  okType="link"
                  okText="Leave"
                  cancelText="Keep editing"
                  placement="bottom"
                  onConfirm={() => pushPath(CMS)}
                >
                  <Button type="text" icon={<HomeOutlined />}>
                    {screens.lg && "Admin Home Page"}
                  </Button>
                </Popconfirm>
              ),
              style: { padding: "0 10px" },
            },
          ]}
        />
      </Col>
      <Col xs={{ span: 24, order: 3 }} sm={{ span: 11, order: 2 }} lg={7}>
        <Menu
          mode="horizontal"
          selectedKeys={display}
          style={{ justifyContent: screens.sm ? "flex-end" : "center" }}
          onClick={({ key }) => setDisplay(key)}
          items={[
            { key: "builder", label: "Form Builder", icon: <FormOutlined /> },
            {
              key: "notifications",
              label: "Notifications",
              icon: <NotificationOutlined />,
              className: "tour-notifications-tab",
            },
            {
              key: "permissions",
              label: "Settings",
              icon: <SettingOutlined />,
              className: "tour-settings-tab",
            },
          ]}
        />
      </Col>
      <Col xs={{ span: 20, order: 2 }} sm={{ span: 9, order: 3 }} lg={12}>
        <Menu
          mode="horizontal"
          selectable={false}
          style={{
            justifyContent: "flex-end",
          }}
          className="no-bottom-border"
          items={[
            getMenuItem("export", "Export Schema", <DownloadOutlined />, () =>
              _getSchema()
            ),
            getMenuItem(
              "diff",
              "Diff",
              <DiffOutlined />,
              () => setDiffModal(true),
              "tour-diff"
            ),
            getMenuItem("save", "Save updates", <SaveOutlined />, () =>
              saveSchemaChanges()
            ),
          ]}
        />
      </Col>
    </Row>
  );
};

Header.propTypes = {
  config: PropTypes.object,
  pushPath: PropTypes.func,
  saveSchemaChanges: PropTypes.func,
  formuleState: PropTypes.object,
  display: PropTypes.string,
  setDisplay: PropTypes.func,
};

export default Header;
