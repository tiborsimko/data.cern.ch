import { useMemo } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Space,
  Tag,
  Typography,
} from "antd";
import { transformSchema } from "../../../partials/Utils/schema";
import JSONSchemaPreviewer from "../../../partials/JSONSchemaPreviewer";
import {
  CodeOutlined,
  FolderOutlined,
  InfoCircleOutlined,
  UserOutlined,
} from "@ant-design/icons";
import OverviewLoading from "./OverviewLoading";
import DepositFilesList from "../../../partials/FileList";
import { calculateCollaborators } from "../../utils/calculateCollaborators";
import InfoArrayBox from "../../../partials/infoArrayBox";
import Reviews from "../../../partials/Reviews";

const Overview = ({
  canUpdate,
  schemas = { schema: null },
  metadata,
  schema,
  webhooks,
  files,
  edit,
  draft_id,
  status,
  revision,
  mySchema,
  access,
  loading,
  history,
}) => {
  const { users, roles } = useMemo(
    () => calculateCollaborators(access),
    [access]
  );

  const infoArray = [
    {
      text: `${revision} revision(s)`,
      icon: <InfoCircleOutlined />,
    },
    {
      text: `${users || 0} users / ${roles || 0} roles`,
      icon: <UserOutlined />,
    },
    {
      text: `${webhooks && webhooks.length} repositories`,
      icon: <CodeOutlined />,
    },
    {
      text: `${files && files.size} files`,
      icon: <FolderOutlined />,
    },
    {
      text: `${(schema && schema.version) || "-"} schema version`,
      icon: <InfoCircleOutlined />,
    },
  ];
  if (loading)
    return (
      <Col xxl={16} lg={18} xs={22} sm={22}>
        <OverviewLoading />
      </Col>
    );
  return (
    <Col xxl={16} lg={18} xs={22} sm={22} style={{ paddingBottom: "15px" }}>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Row
          justify="space-around"
          style={{ background: "#fff", padding: "5px 0" }}
        >
          {infoArray.map((item, idx) => (
            <Tag key={idx} icon={item.icon} style={{ margin: "5px" }}>
              {item.text}
            </Tag>
          ))}
        </Row>
        {status == "published" && (
          <Alert
            type="warning"
            message="Warning"
            description="This is a published version. If you want to upload files and repos or update form metadata and the title you have to change to Draft mode"
            showIcon
            action={
              <Button
                data-cy="changeToDraftButton"
                onClick={() => edit(draft_id)}
              >
                Change to Draft
              </Button>
            }
          />
        )}
        {mySchema && mySchema.name == "cms-stats-questionnaire" && (
          <Alert
            type="warning"
            showIcon
            message="Warning"
            description={
              <Typography.Text>
                For your {(mySchema && mySchema.fullname) || "document"} , to be{" "}
                <Typography.Text strong>reviewed</Typography.Text> you need to{" "}
                <Typography.Text strong>Publish</Typography.Text> it first
                (through settings tab)
              </Typography.Text>
            }
          />
        )}

        <Card
          title="Metadata"
          extra={
            <Space size="middle">
              {canUpdate && (
                <Button
                  key="edit"
                  onClick={() => {
                    history.push(`/drafts/${draft_id}/edit`);
                  }}
                >
                  Edit
                </Button>
              )}
              <Button
                key="more"
                onClick={() => {
                  history.push({
                    pathname: `/drafts/${draft_id}/edit`,
                    state: { mode: "preview" },
                  });
                }}
              >
                Show More
              </Button>
            </Space>
          }
        >
          {schemas && schemas.schema && (
            <div style={{ maxHeight: "30vh", overflowX: "hidden" }}>
              <JSONSchemaPreviewer
                formData={metadata}
                schema={transformSchema(schemas.schema)}
                schemaType={mySchema}
                uiSchema={schemas.uiSchema || {}}
                display="list"
              >
                <span />
              </JSONSchemaPreviewer>
            </div>
          )}
        </Card>
        <Reviews />
        <Card title="Connected Repositories">
          {webhooks && webhooks.length > 0 ? (
            <InfoArrayBox items={webhooks} type="repositories" />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No connected repositories yet"
            />
          )}
        </Card>
        <Card title="Uploaded Repositories">
          {files &&
          files.size > 0 &&
          files.filter(item => item.key.startsWith("repositories")).size > 0 ? (
            <DepositFilesList files={files} renderList={["repositories"]} />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No uploaded repositories yet"
            />
          )}
        </Card>
        <Card title="Uploaded Files">
          {files &&
          files.size > 0 &&
          files.filter(item => !item.key.startsWith("repositories")).size >
            0 ? (
            <DepositFilesList files={files} renderList={["files"]} />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No uploaded files yet"
            />
          )}
        </Card>
      </Space>
    </Col>
  );
};

Overview.propTypes = {
  canUpdate: PropTypes.bool,
  schemas: PropTypes.object,
  metadata: PropTypes.object,
  schema: PropTypes.object,
  webhooks: PropTypes.object,
  files: PropTypes.object,
  edit: PropTypes.func,
  draft_id: PropTypes.string,
  status: PropTypes.string,
  revision: PropTypes.string,
  mySchema: PropTypes.object,
  access: PropTypes.object,
  loading: PropTypes.bool,
  history: PropTypes.object,
};

export default Overview;
