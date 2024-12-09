import PropTypes from "prop-types";
import { Modal, Space, Table, Tag, Typography } from "antd";
import prettyBytes from "pretty-bytes";
import TimeAgo from "react-timeago";
import { CloudDownloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

const FileModal = ({ open, file, onCancel, versions }) => {
  if (!file) return null;
  let _versions = versions
    .filter(version => version.get("key") === file.data.key)
    .map(i => ({
      key: i.get("version_id"),
      checksum: i.get("checksum"),
      created: i.get("created"),
      head: i.get("is_head"),
      size: prettyBytes(i.get("size")).toUpperCase(),
      link: i.getIn(["links", "self"]),
    }))
    .toJS();

  const timeOptions = {
    day: "numeric",
    month: "long",
    year: "numeric",
  };

  const columns = [
    {
      dataIndex: "checksum",
      key: "checksum",
      render: text => <a>{text}</a>,
    },
    {
      dataIndex: "head",
      key: "head",
      render: is_head => is_head && <Tag color="green">latest</Tag>,
    },
    {
      dataIndex: "created",
      key: "created",
      render: created => {
        let nowTime = dayjs();
        let createdTime = dayjs(new Date(created));
        let createdPlusExtraTime = createdTime.add(3, "h");

        return createdPlusExtraTime.diff(nowTime) < 0 ? (
          new Date(created).toLocaleString("en-GB", timeOptions)
        ) : (
          <TimeAgo date={created} minPeriod="60" />
        );
      },
    },
    {
      dataIndex: "size",
      key: "size",
      width: "60px",
    },
    {
      dataIndex: "link",
      key: "link",
      width: "32px",
      render: link => (
        <a download href={link}>
          <CloudDownloadOutlined />
        </a>
      ),
    },
  ];
  return (
    <Modal
      open={open}
      width={640}
      onCancel={onCancel}
      okButtonProps={{
        onClick: onCancel,
      }}
      title="File Info"
    >
      <Typography.Title level={5}>{file.name}</Typography.Title>
      <Space style={{ margin: "10px 0 ", flexWrap: "wrap" }}>
        {Object.entries(file.data.tags).map(item => (
          <Tag key={item[0] + item[1]}>
            {item[0]}={item[1]}
          </Tag>
        ))}
      </Space>
      <Table
        showHeader={false}
        size="small"
        dataSource={_versions}
        columns={columns}
      />
    </Modal>
  );
};

FileModal.propTypes = {
  open: PropTypes.bool,
  file: PropTypes.object,
  onCancel: PropTypes.func,
  versions: PropTypes.object,
};

export default FileModal;
