import { useState } from "react";
import PropTypes from "prop-types";
import { Button, Row, Space, Tag, Typography, Descriptions, Card } from "antd";
import { Link } from "react-router-dom";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons";
import DepositFilesList from "../../../partials/FileList";
import { canEdit } from "../../utils/permissions";
import { COLLECTION_BASE } from "../../../routes";
import Timeago from "react-timeago";
import FileManager from "../../containers/FileManager";

const SideBar = ({
  id,
  schema = { fullname: "", version: "" },
  status,
  created_by,
  recid,
  created,
  updated,
  canAdmin,
  canUpdate,
  files,
  links,
  getBucketById,
}) => {
  const contents = [
    {
      title: <Typography.Text>ID</Typography.Text>,
      content: (
        <Typography.Text
          style={{ maxWidth: "99%" }}
          ellipsis={{ tooltip: id }}
          copyable
        >
          {id}
        </Typography.Text>
      ),
    },
    {
      title: <Typography.Text>Collection</Typography.Text>,
      content: schema && (
        <Link to={`${COLLECTION_BASE}/${schema.name}/${schema.version}`}>
          <Tag>
            {schema.fullname} v{schema.version}
          </Tag>
        </Link>
      ),
    },
    {
      title: <Typography.Text>Status</Typography.Text>,
      content: (
        <Tag
          data-cy="sidebarStatus"
          color={status === "published" ? "purple" : "blue"}
        >
          {status}
        </Tag>
      ),
    },
    {
      title: <Typography.Text>Creator</Typography.Text>,
      content: created_by && created_by.email,
    },
    {
      title: <Typography.Text>Published URL</Typography.Text>,
      content: recid ? (
        <Link to={`/published/${recid}`}>
          <Tag color="purple">{recid}</Tag>
        </Link>
      ) : (
        <Typography.Text>Not published yet</Typography.Text>
      ),
    },
    {
      title: <Typography.Text>Created</Typography.Text>,
      content: created && <Timeago date={created} minPeriod="60" />,
    },
    {
      title: <Typography.Text>Last Updated</Typography.Text>,
      content: updated && <Timeago date={updated} minPeriod="60" />,
    },
  ];

  const [showModal, setShowModal] = useState(false);
  return (
    <Row style={{ height: "100%" }}>
      <Space direction="vertical" style={{ width: "100%", padding: "10px" }}>
        <Descriptions bordered size="small">
          {contents.map((content, idx) => (
            <Descriptions.Item label={content.title} key={idx} span={24}>
              {content.content}
            </Descriptions.Item>
          ))}
        </Descriptions>
        <FileManager open={showModal} onCancel={() => setShowModal(false)} />
        <Card
          size="small"
          title="Files | Data | Repos"
          extra={
            status != "published" && canEdit(canAdmin, canUpdate) && (
              <Space direction="horizontal" size="middle">
                <Button
                  size="small"
                  key="refresh"
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    let { bucket } = links;
                    let bucket_id = bucket.split("/").pop();
                    getBucketById(bucket_id);
                  }}
                />
                <Button
                  key="add"
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={() => setShowModal(true)}
                />
              </Space>
            )
          }
        >
          <DepositFilesList files={files} />
        </Card>
      </Space>
    </Row>
  );
};

SideBar.propTypes = {
  id: PropTypes.string,
  schema: PropTypes.object,
  status: PropTypes.string,
  created_by: PropTypes.object,
  recid: PropTypes.string,
  created: PropTypes.string,
  updated: PropTypes.string,
  canAdmin: PropTypes.bool,
  canUpdate: PropTypes.bool,
  files: PropTypes.object,
  links: PropTypes.object,
  getBucketById: PropTypes.func,
  toggleFilemanagerLayer: PropTypes.func,
};

export default SideBar;
