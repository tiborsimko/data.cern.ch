import { Button, Form, Input } from "antd";
import { CMS_NEW } from "../../routes";
import { withRouter } from "react-router";
import { initFormuleSchemaWithNotifications } from "../utils";

const CreateForm = ({ history }) => {
  const onFinish = content => {
    let { name, description } = content;
    initFormuleSchemaWithNotifications({ fullname: name }, name, description);
    history.push(CMS_NEW);
  };

  return (
    <Form name="basic" layout="vertical" onFinish={onFinish}>
      <Form.Item
        label="Name"
        name="name"
        rules={[{ required: true, message: "Please input schema name!" }]}
      >
        <Input data-cy="admin-form-name" />
      </Form.Item>

      <Form.Item
        label="Description"
        name="description"
        rules={[
          { required: true, message: "Please input schema description!" },
        ]}
      >
        <Input.TextArea data-cy="admin-form-description" />
      </Form.Item>

      <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
        <Button type="primary" htmlType="submit" data-cy="admin-form-submit">
          Submit
        </Button>
      </Form.Item>
    </Form>
  );
};

export default withRouter(CreateForm);
