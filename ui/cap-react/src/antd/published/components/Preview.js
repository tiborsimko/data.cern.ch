import JSONSchemaPreviewer from "../../partials/JSONSchemaPreviewer";
import Reviews from "../../partials/Reviews";
import { transformSchema } from "../../partials/Utils/schema";
import { COLLECTION_BASE } from "../../routes";
import { shouldDisplayTabButton } from "../utils";
import SideBar from "./SideBar";
import {
  EditOutlined,
  ExportOutlined,
  InfoCircleOutlined,
} from "@ant-design/icons";
import {
  Space,
  Tag,
  Button,
  Row,
  Col,
  Radio,
  Grid,
  Layout,
  Tooltip,
} from "antd";
import { PageHeader } from "@ant-design/pro-layout";
import PropTypes from "prop-types";
import { useState } from "react";
import { Link } from "react-router-dom";
import dayjs from "dayjs";

const Preview = ({
  history,
  files,
  status,
  schemaType,
  draft_id,
  canUpdate,
  id,
  metadata = { general_title: "" },
  schemas = { schema: {}, uiSchema: {} },
  updated,
}) => {
  const [display, setDisplay] = useState(
    schemas.uiSchema["ui:object"] == "tabView" ? "tabView" : "list"
  );
  const [displayFiles, setDisplayFiles] = useState(false);
  const { useBreakpoint } = Grid;
  const screens = useBreakpoint();

  const displayProps =
    display == "tabView" ? { xs: 24 } : { lg: 15, sm: 18, xs: 22 };
  return (
    <Layout style={{ height: "100%", padding: "0" }}>
      <PageHeader
        style={{ background: "#fff", marginBottom: "10px", padding: "10px" }}
        title={
          <Space direction="vertical">
            {metadata.general_title}
            <Space style={{ width: "100%" }} wrap>
              <Tag bordered={false} color="purple-inverse">
                Published
              </Tag>
              <Tag bordered={false} color="magenta">
                {id}
              </Tag>
              {schemaType && (
                <Link
                  to={`${COLLECTION_BASE}/${schemaType.name}/${
                    schemaType.version || ""
                  }`}
                >
                  <Tag
                    bordered={false}
                    color="geekblue"
                    icon={<ExportOutlined />}
                  >
                    {schemaType.fullname} v{schemaType.version}
                  </Tag>
                </Link>
              )}
              <Tooltip
                title={`Last publication: ${dayjs(updated).format(
                  "DD/MM/YYYY HH:mm:ss"
                )}`}
              >
                <Tag bordered={false} icon={<InfoCircleOutlined />}>
                  {dayjs(updated).format("DD/MM/YYYY")}
                </Tag>
              </Tooltip>
            </Space>
          </Space>
        }
        extra={
          <Space style={{ width: "100%" }} wrap>
            <Button
              disabled={!canUpdate}
              data-cy="editPublished"
              key="edit"
              icon={<EditOutlined />}
              onClick={() =>
                history.push({
                  pathname: `/drafts/${draft_id}`,
                  from: location.pathname,
                  pageFrom: "Published Preview",
                })
              }
            >
              Edit
            </Button>
            <Reviews key="addReview" isReviewingPublished action="add" />
            <Reviews key="showReviews" isReviewingPublished action="show" />
            {!screens.xxl && (
              <Button key="files" onClick={() => setDisplayFiles(true)}>
                Show Files
              </Button>
            )}
          </Space>
        }
      >
        {shouldDisplayTabButton(schemas) && (
          <Radio.Group
            defaultValue={display}
            size="small"
            buttonStyle="solid"
            onChange={e => setDisplay(e.target.value)}
          >
            <Space>
              <Radio.Button
                value="tabView"
                disabled={schemas.uiSchema["ui:object"] != "tabView"}
              >
                Tabs
              </Radio.Button>
              <Radio.Button value="list">List</Radio.Button>
            </Space>
          </Radio.Group>
        )}
      </PageHeader>
      <Row
        style={{ paddingRight: "10px", height: "100%", overflowX: "hidden" }}
      >
        <Col xs={24} xxl={19} style={{ height: "100%" }}>
          <Row
            style={{ height: "100%", overflowX: "hidden" }}
            justify={display != "tabView" && "center"}
          >
            <Col {...displayProps} style={{ height: "100%" }}>
              <JSONSchemaPreviewer
                display={display}
                formData={metadata}
                schema={transformSchema(schemas.schema)}
                schemaType={schemaType}
                uiSchema={schemas.uiSchema}
              >
                <span />
              </JSONSchemaPreviewer>
            </Col>
          </Row>
        </Col>
        <SideBar
          visibleFileDrawer={displayFiles}
          files={files}
          onClose={() => setDisplayFiles(false)}
          status={status}
        />
      </Row>
    </Layout>
  );
};

Preview.propTypes = {
  history: PropTypes.object,
  schemaType: PropTypes.object,
  schemas: PropTypes.object,
  metadata: PropTypes.object,
  draft_id: PropTypes.string,
  id: PropTypes.string,
  canUpdate: PropTypes.bool,
  files: PropTypes.object,
  status: PropTypes.string,
  updated: PropTypes.string,
};

export default Preview;
