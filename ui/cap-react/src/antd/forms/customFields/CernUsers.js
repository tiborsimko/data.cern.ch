import { useState } from "react";
import PropTypes from "prop-types";
import {
  Button,
  Form,
  Input,
  Modal,
  Radio,
  Row,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import axios from "../../../axios";
import { debounce } from "lodash-es";
import DeleteOutlined from "@ant-design/icons/DeleteOutlined";
import { SearchOutlined } from "@ant-design/icons";

// Example 'cernUsers' field uiSchema
//
//
// "analysis_contacts": {
//   "ui:array": "StringArrayField",
//   "ui:options": {
//     "email": true
//   },
//   "items": {
//     "ui:field": "cernUsers",
//     "ui:options": {
//       "autoOpenModal": true,
//       "searchType": ["user", "egroup"]
//     }
//   }
// },
// "people_involved": {
//   "ui:array": "StringArrayField",
//   "ui:options": {
//     "email": true
//   },
//   "items": {
//     "ui:field": "cernUsers",
//     "ui:options": {
//       "autoOpenModal": true
//     }
//   }
// }

const CernUsers = ({ onChange, formData, uiSchema, readonly }) => {
  const autoOpenModal =
    uiSchema["ui:options"] && uiSchema["ui:options"].autoOpenModal;

  let searchType = uiSchema["ui:options"] && uiSchema["ui:options"].searchType;
  searchType = searchType ? searchType : ["user"];

  const [showModal, setShowModal] = useState(
    autoOpenModal
      ? !formData || (formData && Object.keys(formData).length == 0)
      : false
  );
  const [ldapData, setLdapData] = useState([]);
  const [tableLoading, setTableLoading] = useState(false);
  const [form] = Form.useForm();

  const modalColumns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Email",
      dataIndex: "email",
      key: "email",
    },
    {
      title: "Department",
      dataIndex: "department",
      key: "department",
      render: tag => <Tag color="geekblue">{tag}</Tag>,
    },
    {
      title: "Action",
      key: "action",
      render: item => (
        <Button
          type="primary"
          onClick={() => {
            setShowModal(false);
            form.resetFields();
            setLdapData([]);
            onChange({
              name: item.name,
              email: item.email,
              department: item.department,
            });
          }}
        >
          Add
        </Button>
      ),
    },
  ];

  const fetchLDAPdata = debounce(
    async ({ searchFor = searchType[0], searchInput }) => {
      setTableLoading(true);
      const response = await axios.get(
        `/api/services/ldap/${searchFor}/mail?query=${searchInput}`
      );

      setLdapData(
        response.data.map(item => ({
          target: searchFor,
          key: item.email ? item.email : item,
          email: item.email ? item.email : item,
          department: item.email ? item.profile.department : "egroup",
          name: item.email
            ? item.profile.display_name
            : item.split("@cern.ch")[0],
        }))
      );
      setTableLoading(false);
    },
    500
  );

  return (
    <>
      <Modal
        open={showModal}
        onCancel={() => {
          setShowModal(false);
          form.resetFields();
          setLdapData([]);
        }}
        width={1000}
      >
        <Form
          form={form}
          initialValues={{ searchFor: "user" }}
          layout="vertical"
          onValuesChange={(_, values) =>
            values.searchInput && values.searchInput.length > 0
              ? fetchLDAPdata(values)
              : setLdapData([]) && setTableLoading(false)
          }
        >
          {searchType.length > 1 && (
            <Form.Item label="Search For" name="searchFor">
              <Radio.Group buttonStyle="solid">
                {searchType.map(type => (
                  <Radio.Button key={type} value={type}>
                    {type}
                  </Radio.Button>
                ))}
              </Radio.Group>
            </Form.Item>
          )}
          <Form.Item name="searchInput">
            <Input
              placeholder={
                searchType.length == 1
                  ? `Search for ${searchType[0]} emails...`
                  : "Search for emails..."
              }
            />
          </Form.Item>
        </Form>
        <Table
          loading={tableLoading}
          dataSource={ldapData}
          columns={modalColumns}
          fixedHeader
          pagination={false}
        />
      </Modal>

      {formData && Object.keys(formData).length > 0 ? (
        <Row
          justify="space-between"
          style={{
            padding: "5px",
            background: "#f5f5f5",
            ...(!autoOpenModal && { background: "#ccc", padding: "10px" }),
          }}
        >
          <Space size={"small"} direction={"horizontal"}>
            <Typography.Text>{formData.name}</Typography.Text>
            <a href={`mailto:${formData.email}`}>
              <Tag color="geekblue">{formData.email}</Tag>
            </a>
            <Tag color="blue">{formData.department}</Tag>
          </Space>
          {!autoOpenModal && !readonly && (
            <Button
              type="danger"
              icon={<DeleteOutlined />}
              onClick={() => onChange(undefined)}
            />
          )}
        </Row>
      ) : (
        <Row
          justify="end"
          style={{
            background: "#f5f5f5",
            ...(!autoOpenModal && { background: "#ccc", padding: "10px" }),
          }}
        >
          <Button
            type="primary"
            onClick={() => setShowModal(true)}
            icon={<SearchOutlined />}
          />
        </Row>
      )}
    </>
  );
};

CernUsers.propTypes = {
  formData: PropTypes.object,
  uiSchema: PropTypes.object,
  onChange: PropTypes.func,
};

export default CernUsers;
