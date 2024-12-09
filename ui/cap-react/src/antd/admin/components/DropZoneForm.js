import { notification, Upload } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { initFormuleSchemaWithNotifications } from "../utils";
import { CMS_NEW } from "../../routes";
import { withRouter } from "react-router";

const isfileJson = filename => {
  const extension = filename.substr(filename.lastIndexOf(".") + 1);
  if (!/(json)$/gi.test(extension)) {
    return false;
  } else {
    return extension;
  }
};

const DropZoneForm = ({ history }) => {
  return (
    <Upload.Dragger
      name="adminJsonFiles"
      multiple={false}
      onChange={e => {
        const { file, fileList } = e;
        if (fileList && fileList.length > 0) {
          const { name } = file;
          if (isfileJson(name)) {
            let reader = new FileReader();
            reader.onload = function (event) {
              const newSchema = JSON.parse(event.target.result);
              if (newSchema["deposit_schema"] && newSchema["deposit_options"]) {
                initFormuleSchemaWithNotifications(newSchema);
                history.push(CMS_NEW);
              } else {
                notification.error({
                  message: "Missing Keys",
                  key: "keys",
                  description:
                    "Your json should include a deposit_schema and a deposit_option key",
                });
              }
            };
            reader.readAsText(file.originFileObj);
          } else {
            notification.error({
              message: "File Format",
              key: "format",
              description: "Your file format should be json",
            });
          }
        }
      }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">Browse Files</p>
      <p>OR</p>
      <p className="ant-upload-text">Drop your JSON file here</p>
    </Upload.Dragger>
  );
};

export default withRouter(DropZoneForm);
