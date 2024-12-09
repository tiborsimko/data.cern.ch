import PropTypes from "prop-types";
import { Button, Col, Popconfirm, Row } from "antd";
import { PageHeader } from "@ant-design/pro-layout";
import { schema, uiSchema } from "../utils";
import { DeleteOutlined } from "@ant-design/icons";
import { FormuleForm } from "react-formule";
const NotificationEdit = ({
  schemaConfig,
  removeNotification,
  updateNotificationData,
  category,
  index,
  onBack,
}) => {
  const formData =
    schemaConfig &&
    schemaConfig.get(category).get(index) &&
    schemaConfig.get(category).get(index).toJS();

  return (
    <>
      <PageHeader
        title={`Notification #${index + 1}`}
        onBack={onBack}
        extra={
          <Popconfirm
            title="Delete notification"
            okType="danger"
            okText="Delete"
            cancelText="Cancel"
            placement="left"
            onConfirm={() => {
              removeNotification(index, category);
              onBack();
            }}
          >
            <Button danger icon={<DeleteOutlined />}>
              Delete
            </Button>
          </Popconfirm>
        }
      />
      <Row justify="center">
        <Col span={12}>
          <FormuleForm
            schema={schema}
            uiSchema={uiSchema}
            onChange={({ formData }) =>
              updateNotificationData(formData, index, category)
            }
            formData={formData}
          />
        </Col>
      </Row>
    </>
  );
};

NotificationEdit.propTypes = {
  schemaConfig: PropTypes.object,
  removeNotification: PropTypes.func,
  updateNotificationData: PropTypes.func,
  category: PropTypes.string,
  index: PropTypes.number,
  onBack: PropTypes.func,
};

export default NotificationEdit;
