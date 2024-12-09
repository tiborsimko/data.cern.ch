import { fetchRecordsResults } from "../../actions/common";
import DashboardList from "../dashboard/components/DashboardList";
import { _getCollectionList } from "../dashboard/utils";
import RichEditorWidget from "../forms/RichEditorWidget";
import ErrorScreen from "../partials/Error";
import CollectionPermissions from "./CollectionPermissions";
import { CloseOutlined, EditOutlined, SaveOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Empty,
  Row,
  Select,
  Space,
  Tag,
  Typography,
  notification,
} from "antd";
import axios from "../../axios";
import PropTypes from "prop-types";
import { useEffect, useState } from "react";
import { connect } from "react-redux";

const Collection = ({
  match,
  fetchRecordsResults,
  error,
  results,
  schemaData,
  history,
  loading,
  roles,
}) => {
  const [readme, setReadme] = useState();
  const [editing, setEditing] = useState();

  useEffect(() => {
    // get URL params collection_name and version
    let { collection_name, version = null } = match.params;

    // fetch results for the deposit/records
    fetchRecordsResults(collection_name, version);
  }, []);

  useEffect(() => {
    setReadme(schemaData.getIn(["config", "readme"]));
  }, [schemaData]);

  // //  display error screen when error occurs
  if (error) {
    return <ErrorScreen message={error} />;
  }

  let { collection_name, version } = match.params;

  let lists = _getCollectionList(results);

  const cancelEdit = () => {
    setReadme(schemaData.getIn(["config", "readme"]));
    setEditing(false);
  };

  const saveEdit = () => {
    axios
      .patch(
        `/api/jsonschemas/${schemaData.get("name")}/${schemaData.get(
          "version"
        )}`,
        [
          {
            op: "add",
            path: "/config/readme",
            value: readme,
          },
        ]
      )
      .then(() => {
        notification.success({
          message: "Readme updated",
        });
      })
      .catch(() =>
        notification.error({
          message: "Readme not updated",
          description:
            "Error while updating the collection's readme, please try again",
        })
      );

    setEditing(false);
  };

  return (
    <Row justify="center" style={{ padding: "30px 0" }}>
      <Col xs={22} lg={18} xl={14}>
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          <Row justify="space-between" wrap={false}>
            <Col>
              <Typography.Title level={3}>
                {schemaData.has("fullname") && schemaData.get("fullname")}
              </Typography.Title>
              <Tag color="geekblue">{schemaData.get("name")}</Tag>
            </Col>
            <Col>
              <Select
                defaultValue={version ? version : "allversions"}
                style={{ width: 110 }}
                onChange={val =>
                  val == "allversions"
                    ? history.push(`/collection/${collection_name}`)
                    : history.push(`/collection/${collection_name}/${val}`)
                }
              >
                <Select.Option value="allversions" key="allversions">
                  All Versions
                </Select.Option>
                {schemaData.has("versions") &&
                  schemaData.get("versions").map(item => (
                    <Select.Option value={item} key={item}>
                      {item}
                    </Select.Option>
                  ))}
              </Select>
            </Col>
          </Row>
          <Typography.Text>
            {schemaData.hasIn(["config", "description"])
              ? schemaData.getIn(["config", "description"])
              : "No Description"}
          </Typography.Text>

          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Card
                title="Read me"
                extra={
                  (roles.get("isSuperUser") ||
                    roles.get("schemaAdmin").get(schemaData.get("name"))) &&
                  (editing ? (
                    <Space>
                      <Button
                        key="cancel"
                        icon={<CloseOutlined />}
                        onClick={cancelEdit}
                      >
                        Cancel
                      </Button>
                      <Button
                        key="save"
                        icon={<SaveOutlined />}
                        type="primary"
                        onClick={saveEdit}
                      >
                        Save
                      </Button>
                    </Space>
                  ) : (
                    <Button
                      key="edit"
                      icon={<EditOutlined />}
                      onClick={() => setEditing(true)}
                    >
                      Edit
                    </Button>
                  ))
                }
                style={{ body: {
                  padding: "1px 0 0 0",
                  maxHeight: "300px",
                  overflowY: "auto",
                }}}
              >
                {readme || editing ? (
                  <RichEditorWidget
                    value={readme}
                    readonly={!editing}
                    height={editing ? 300 : 0}
                    noBorder={!editing}
                    onChange={e => setReadme(e)}
                  />
                ) : (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No Content"
                  />
                )}
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <DashboardList
                header="Latest Drafts"
                loading={loading}
                listType="draft"
                list={lists["drafts"]}
              />
            </Col>
            <Col xs={24} md={12}>
              <DashboardList
                header="Latest Published"
                loading={loading}
                listType="published"
                list={lists["published"]}
              />
            </Col>
          </Row>

          <Row>
            <Col xs={24}>
              <Card title="Permissions">
                <CollectionPermissions
                  permissions={schemaData.getIn(["config", "permissions"])}
                />
              </Card>
            </Col>
          </Row>
        </Space>
      </Col>
    </Row>
  );
};

Collection.propTypes = {
  schema: PropTypes.object,
  roles: PropTypes.object,
  schemaData: PropTypes.object,
  match: PropTypes.object,
  results: PropTypes.object,
  history: PropTypes.object,
  error: PropTypes.object,
  loading: PropTypes.bool,
  fetchRecordsResults: PropTypes.func,
};

const mapStateToProps = state => ({
  results: state.collection.getIn(["results"]),
  depositGroups: state.auth.getIn(["currentUser", "depositGroups"]),
  roles: state.auth.getIn(["currentUser", "roles"]),
  schemaData: state.collection.get("schema_data"),
  loading: state.collection.get("loading"),
  error: state.collection.get("error"),
});

const mapDispatchToProps = dispatch => ({
  fetchRecordsResults: (name, version) =>
    dispatch(fetchRecordsResults(name, version)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Collection);
