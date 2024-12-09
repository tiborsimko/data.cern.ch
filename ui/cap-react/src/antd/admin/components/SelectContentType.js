import PropTypes from "prop-types";
import { Button, Col, Row, Space } from "antd";
import CheckableTag from "antd/es/tag/CheckableTag";
import { useState } from "react";
import { EditOutlined, EyeOutlined } from "@ant-design/icons";
import { CMS_EDITOR, CMS_SCHEMA } from "../../routes";
import { withRouter } from "react-router";
import { PRIMARY_COLOR } from "../../utils/theme";
const SelectContentType = ({ contentTypes, history }) => {
  const [selectedTag, setSelectedTag] = useState();

  return (
    <>
      <Space size={[0, 8]} wrap>
        {contentTypes &&
          contentTypes.map(item => (
            <CheckableTag
              style={{ border: `1px solid ${PRIMARY_COLOR}` }}
              onChange={checked =>
                checked
                  ? setSelectedTag(item.get("deposit_group"))
                  : setSelectedTag(undefined)
              }
              checked={selectedTag === item.get("deposit_group")}
              key={item.get("deposit_group")}
              data-cy={"admin-predefined-content"}
            >
              {item.get("name")}
            </CheckableTag>
          ))}
      </Space>
      <Row justify="center" gutter={10} style={{ marginTop: "25px" }}>
        <Col>
          <Button
            disabled={!selectedTag}
            onClick={() => history.push(`${CMS_SCHEMA}/${selectedTag}`)}
            icon={<EyeOutlined />}
            data-cy="viewSchemaButton"
          >
            View
          </Button>
        </Col>
        <Col>
          <Button
            disabled={!selectedTag}
            onClick={() => history.push(`${CMS_EDITOR}/${selectedTag}`)}
            type="primary"
            icon={<EditOutlined />}
            data-cy="editSchemaButton"
          >
            Edit
          </Button>
        </Col>
      </Row>
    </>
  );
};

SelectContentType.propTypes = {
  contentTypes: PropTypes.object,
  select: PropTypes.func,
};

export default withRouter(SelectContentType);
