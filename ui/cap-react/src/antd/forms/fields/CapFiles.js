import React, { useState } from "react";
import PropTypes from "prop-types";
import { Button, Modal, Space, Typography } from "antd";
import { connect } from "react-redux";
import { selectPath } from "../../../actions/files";
import Files from "../../partials/FileList/components/Files";
import { WarningOutlined } from "@ant-design/icons";

const CapFiles = ({ uiSchema, files, onChange, formData }) => {
  const [showModal, setShowModal] = useState(false);
  let keys = Object.keys(files.toJS());
  let missedFileError = !keys.includes(formData);
  return (
    <React.Fragment>
      <Modal
        visible={showModal}
        onCancel={() => setShowModal(false)}
        title="File Manager"
        width={800}
      >
        <Typography.Title level={5}>
          Select a file from the list
        </Typography.Title>
        <Files
          memoFiles={files}
          onFileClick={name => {
            onChange(name);
            setShowModal(false);
          }}
        />
      </Modal>
      {formData ? (
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
      ) : (
        <Button onClick={() => setShowModal(true)}>
          {(uiSchema && uiSchema.capFilesDescription) ||
            "Select a file or a repository from your list to link here"}
        </Button>
      )}
    </React.Fragment>
  );
};

CapFiles.propTypes = {};

const mapStateToProps = state => ({
  files: state.draftItem.get("bucket"),
  pathSelected: state.draftItem.get("pathSelected")
});

const mapDispatchToProps = dispatch => ({
  selectPath: (path, type) => dispatch(selectPath(path, type))
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(CapFiles);
