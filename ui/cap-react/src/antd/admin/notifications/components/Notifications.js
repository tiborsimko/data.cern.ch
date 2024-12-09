import { useState } from "react";
import PropTypes from "prop-types";
import {
  Button,
  Form,
  Layout,
  Menu,
  Typography,
  Modal,
  Input,
  Row,
  Col,
  Empty,
} from "antd";
import NotificationList from "../containers/NotificationList";

import { NotificationOutlined, PlusOutlined } from "@ant-design/icons";

const Notifications = ({ schemaConfig, createNotificationCategory }) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState();
  const [form] = Form.useForm();

  const submitModalForm = () => {
    form.validateFields().then(values => {
      form.resetFields();
      setModalVisible(false);
      createNotificationCategory(values.title);
    });
  };

  return (
    <Layout style={{ height: "100%", padding: 0 }}>
      <Modal
        destroyOnClose
        open={modalVisible}
        title="Create a new collection"
        okText="Create"
        cancelText="Cancel"
        onCancel={() => {
          form.resetFields();
          setModalVisible(false);
        }}
        onOk={submitModalForm}
      >
        <Form form={form} layout="vertical" name="form_in_modal">
          <Form.Item
            name="title"
            label="Category title"
            rules={[
              {
                required: true,
                message: "Please input the title of the collection",
              },
            ]}
          >
            <Input
              autoFocus
              onKeyDown={e => {
                if (e.key === "Enter") {
                  submitModalForm();
                }
              }}
            />
          </Form.Item>
        </Form>
      </Modal>
      <Layout.Sider theme="light" breakpoint="sm" collapsedWidth={0}>
        <Row align="middle" wrap={false} style={{ margin: "20px" }}>
          <Col flex="auto">
            <Typography.Title level={5}>
              Notification categories
            </Typography.Title>
          </Col>
          <Col flex="none">
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setModalVisible(true)}
            />
          </Col>
        </Row>

        <Menu
          selectable
          items={
            schemaConfig &&
            schemaConfig.entrySeq().map(item => ({
              key: item[0],
              label: item[0],
              onClick: () => setSelectedCategory(item[0]),
            }))
          }
        />
      </Layout.Sider>
      <Layout.Content style={{ overflowY: "scroll" }}>
        {selectedCategory ? (
          <NotificationList category={selectedCategory} />
        ) : (
          <Row align="middle" justify="center" style={{ height: "100%" }}>
            <Col>
              <Empty
                image={<NotificationOutlined />}
                imageStyle={{ fontSize: "50px" }}
                description="Please select or create a category at the left"
              />
            </Col>
          </Row>
        )}
      </Layout.Content>
    </Layout>
  );
};

Notifications.propTypes = {
  schemaConfig: PropTypes.object,
  createNotificationCategory: PropTypes.func,
};

export default Notifications;
