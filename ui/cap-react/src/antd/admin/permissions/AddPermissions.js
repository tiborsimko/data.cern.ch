import { useState } from "react";
import PropTypes from "prop-types";
import { Form, Input, Space, Radio, Typography } from "antd";
import axios from "../../../axios";
import { debounce } from "lodash-es";
import CollectionPermissions from "../../collection/CollectionPermissions";

const Permissions = ({ handlePermissions, permissions }) => {
  const [ldapData, setLdapData] = useState([]);
  const [tableLoading, setTableLoading] = useState(false);
  const [searchFor, setSearchFor] = useState("user");
  const [form] = Form.useForm();

  const fetchLDAPdata = debounce(async ({ searchInput }) => {
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
        permission: [],
      }))
    );
    setTableLoading(false);
  }, 500);

  return (
    <>
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
        <Form.Item name="searchInput">
          <Input
            placeholder="Search..."
            addonAfter={
              <Space>
                <Typography.Text>Search for:</Typography.Text>
                <Radio.Group
                  size="small"
                  value={searchFor}
                  buttonStyle="solid"
                  onChange={e => setSearchFor(e.target.value)}
                >
                  <Radio.Button value="user">Users</Radio.Button>
                  <Radio.Button value="egroup">E groups</Radio.Button>
                </Radio.Group>
              </Space>
            }
          />
        </Form.Item>
      </Form>
      <CollectionPermissions
        loading={tableLoading}
        handlePermissions={handlePermissions}
        defaultPermissions={permissions}
        permissions={ldapData.map(i => {
          i["permissions"] = [];
          return i;
        })}
        editable
        dont
      />
    </>
  );
};

Permissions.propTypes = {
  draft_id: PropTypes.string,
  handlePermissions: PropTypes.func,
  permissions: PropTypes.object,
  canAdmin: PropTypes.bool,
  created_by: PropTypes.object,
};

export default Permissions;
