import { useEffect, useState } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import {
  Alert,
  Layout,
  Space,
  Typography,
  Tabs,
  Col,
  Card,
  Button,
} from "antd";
import CollectionPermissions from "../../collection/CollectionPermissions";
import {
  getSchemaPermissions,
  postSchemaPermissions,
  deleteSchemaPermissions,
  updateSchemaConfig,
} from "../../../actions/builder";
import AddPermissions from "./AddPermissions";
import { Map } from "immutable";
import {
  CloseSquareFilled,
  EditFilled,
  PlusCircleOutlined,
} from "@ant-design/icons";

import { configSchema } from "../utils/schemaSettings";
import { FormuleForm } from "react-formule";

// Left as documentation
/*
  const initialStatePermissions = Map({
    deposit: {
      read: { users: [], roles: [] },
      update: { users: [], roles: [] },
      admin: { users: [], roles: [] },
      review: { users: [], roles: [] },
      create: { users: [], roles: [] },
    },
    records: {
      read: { users: [], roles: [] },
      review: { users: [], roles: [] },
    },
  });
*/

const Permissions = ({
  schemaName,
  schemaVersion,
  permissions = null,
  getSchemaPermissions,
  postSchemaPermissions,
  deleteSchemaPermissions,
  config,
  updateSchemaConfig,
  isNew,
}) => {
  const [editable, setEditable] = useState(false);
  const [addEnabled, setAddEnabled] = useState(false);
  useEffect(() => {
    !isNew && getSchemaPermissions(schemaName, schemaVersion);
  }, []);

  const addSchemaPermissionsToEmail = (
    email,
    permissions,
    type = "user",
    action = "add"
  ) => {
    let permission_data = {};
    const _type = type == "user" ? "users" : "roles";
    permissions.map(p => {
      if (p.startsWith("record-schema-")) {
        let action = p.replace("record-schema-", "");
        if (!permission_data["record"]) permission_data["record"] = {};
        if (!permission_data["record"][action])
          permission_data["record"][action] = {};

        permission_data["record"][action][_type] = [email];
      } else if (p.startsWith("deposit-schema-")) {
        let action = p.replace("deposit-schema-", "");
        if (!permission_data["deposit"]) permission_data["deposit"] = {};
        if (!permission_data["deposit"][action])
          permission_data["deposit"][action] = {};
        permission_data["deposit"][action][_type] = [email];
      }
    });

    if (action == "delete")
      deleteSchemaPermissions(schemaName, schemaVersion, permission_data);
    else postSchemaPermissions(schemaName, schemaVersion, permission_data);
  };

  return (
    <Layout
      style={{ height: "100%", padding: "20px", flex: 1, display: "flex" }}
    >
      <Col span={18}>
        <Tabs
          tabPosition="left"
          items={[
            {
              label: "Collection settings",
              key: "collection",
              children: (
                <Card title="Collection info & settings">
                  <FormuleForm
                    {...configSchema}
                    formData={config.toJS()}
                    onChange={data => updateSchemaConfig(data.formData)}
                  />
                </Card>
              ),
            },
            {
              label: "Permissions",
              key: "permissions",
              children: (
                <Card
                  title="Permissions"
                  extra={
                    <Space>
                      {!addEnabled && (
                        <Button
                          icon={
                            editable ? <CloseSquareFilled /> : <EditFilled />
                          }
                          size="small"
                          onClick={() => setEditable(!editable)}
                        >
                          {editable ? "Close" : "Edit"}
                        </Button>
                      )}
                      {!editable && (
                        <Button
                          icon={
                            addEnabled ? (
                              <CloseSquareFilled />
                            ) : (
                              <PlusCircleOutlined />
                            )
                          }
                          size="small"
                          onClick={() => setAddEnabled(!addEnabled)}
                        >
                          {addEnabled ? "Close" : "Add"}
                        </Button>
                      )}
                    </Space>
                  }
                >
                  {addEnabled && (
                    <Alert
                      banner
                      message={
                        "Search for CERN users and egroups and give them access to the collection."
                      }
                      type="info"
                    />
                  )}
                  {!addEnabled ? (
                    <>
                      <Space direction="vertical" style={{ marginBottom: 20 }}>
                        <Typography.Paragraph style={{ marginBottom: 0 }}>
                          Here you can manage access to your{" "}
                          <Typography.Text strong>
                            {schemaName} {schemaVersion && `(${schemaVersion})`}
                          </Typography.Text>{" "}
                          collection. You can determine who can perform specific
                          action for both states of your document
                          (draft/published)
                        </Typography.Paragraph>

                        <Space direction="vertical">
                          <Typography.Text>
                            <Typography.Text strong>Actions: </Typography.Text>
                            <Typography.Text keyboard>read</Typography.Text>,
                            <Typography.Text keyboard>create</Typography.Text>,
                            <Typography.Text keyboard>update</Typography.Text>,
                            <Typography.Text keyboard>admin</Typography.Text>,
                            <Typography.Text keyboard>review</Typography.Text>
                          </Typography.Text>
                        </Space>
                      </Space>
                      {editable && (
                        <Alert
                          banner
                          message={
                            "By (un)selecting permissions below you can give and remove access to users/egroups"
                          }
                          type="info"
                        />
                      )}
                      <CollectionPermissions
                        permissions={permissions ? Map(permissions) : Map({})}
                        handlePermissions={addSchemaPermissionsToEmail}
                        editable={editable}
                      />
                    </>
                  ) : (
                    <AddPermissions
                      permissions={permissions}
                      editable={editable}
                      handlePermissions={addSchemaPermissionsToEmail}
                    />
                  )}
                </Card>
              ),
            },
          ]}
        />
      </Col>
    </Layout>
  );
};

Permissions.propTypes = {
  schemaConfig: PropTypes.object,
  createNotificationCategory: PropTypes.func,
};

const mapStateToProps = state => {
  return {
    schemaName: state.builder.getIn(["config", "name"]),
    schemaVersion: state.builder.getIn(["config", "version"]),
    permissions: state.builder.get("permissions"),
    config: state.builder.get("config"),
  };
};

const mapDispatchToProps = dispatch => ({
  getSchemaPermissions: (schema, version) =>
    dispatch(getSchemaPermissions(schema, version)),
  postSchemaPermissions: (schema, version, permissions) =>
    dispatch(postSchemaPermissions(schema, version, permissions)),
  deleteSchemaPermissions: (schema, version, permissions) =>
    dispatch(deleteSchemaPermissions(schema, version, permissions)),
  updateSchemaConfig: config => dispatch(updateSchemaConfig(config)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Permissions);
