import { useState } from "react";
import PropTypes from "prop-types";
import { Button, Modal, Row, Space, Typography } from "antd";
import { connect } from "react-redux";
import { selectPath } from "../../../actions/files";
import Files from "../../partials/FileList/components/Files";
import { DeleteOutlined, WarningOutlined } from "@ant-design/icons";

const CapFiles = ({ uiSchema, files, onChange, formData }) => {
  const [showModal, setShowModal] = useState(false);
  let keys = Object.keys(files.toJS());
  let missedFileError = !keys.includes(formData);

  //TODO: we should investigate whether the onChange should also accept directories
  return (
    <>
      <Modal
        open={showModal}
        onCancel={() => setShowModal(false)}
        title="File Manager"
        width={800}
        footer={null}
      >
        <Typography.Text strong>Select a file from the list</Typography.Text>
        <Files
          memoFiles={files}
          onFileClick={name => {
            onChange(name);
            setShowModal(false);
          }}
        />
      </Modal>
      {formData ? (
        <Row
          align="middle"
          justify="space-between"
          style={{
            borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
            padding: "5px",
          }}
        >
          <Space>
            <Typography.Text type={missedFileError && "secondary"}>
              {formData}
            </Typography.Text>
            {missedFileError && (
              <Space>
                <WarningOutlined />
                <Typography.Text type="danger">
                  This file is removed
                </Typography.Text>
              </Space>
            )}
          </Space>
          <Button
            icon={<DeleteOutlined />}
            type="danger"
            onClick={() => onChange(undefined)}
          />
        </Row>
      ) : (
        <Button
          onClick={() => setShowModal(true)}
          style={{ whiteSpace: "normal", height: "auto" }}
        >
          {(uiSchema && uiSchema.capFilesDescription) ||
            "Select a file or a repository from your list to link here"}
        </Button>
      )}
    </>
  );
};

CapFiles.propTypes = {
  uiSchema: PropTypes.object,
  files: PropTypes.object,
  onChange: PropTypes.object,
  formData: PropTypes.object,
};

const mapStateToProps = state => ({
  files: state.draftItem.get("bucket"),
  pathSelected: state.draftItem.get("pathSelected"),
});

const mapDispatchToProps = dispatch => ({
  selectPath: (path, type) => dispatch(selectPath(path, type)),
});

export default connect(mapStateToProps, mapDispatchToProps)(CapFiles);
