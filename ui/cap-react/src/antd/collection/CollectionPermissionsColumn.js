import { CloseOutlined } from "@ant-design/icons";
import { Space, Tag, Tooltip } from "antd";
import PropTypes from "prop-types";
import { useState } from "react";

const { CheckableTag } = Tag;

const CollectionPermissionsColumn = ({
  e,
  item,
  type,
  handlePermissions,
  editable = false,
}) => {
  const [draftIncluded, setDraftIncluded] = useState(
    e.includes(`deposit-schema-${type}`)
  );
  const [pubIncluded, setPubIncluded] = useState(
    e.includes(`record-schema-${type}`)
  );

  const requestPermissionUpdate = (rec_type, checked) => {
    handlePermissions(
      item.email,
      [`${rec_type}-schema-${type}`],
      item.type,
      checked ? "add" : "delete"
    );
    rec_type == "record" ? setPubIncluded(checked) : setDraftIncluded(checked);
  };

  let tags = [];

  if (editable) {
    tags = [
      <Tooltip key={`deposit-schema-${type}`} title="Drafts">
        <CheckableTag
          checked={draftIncluded}
          onChange={checked => requestPermissionUpdate("deposit", checked)}
          color="geekblue"
          style={{ border: "1px solid #ccc", marginRight: 0 }}
        >
          D
        </CheckableTag>
      </Tooltip>,
      <Tooltip key={`record-schema-${type}`} title="Published">
        <CheckableTag
          checked={pubIncluded}
          onChange={checked => requestPermissionUpdate("record", checked)}
          color="purple"
          style={{ border: "1px solid #ccc", marginRight: 0 }}
        >
          P
        </CheckableTag>
      </Tooltip>,
    ];
  } else {
    if (draftIncluded || editable) {
      tags.push(
        <Tooltip key={`deposit-schema-${type}`} title="Drafts">
          <Tag color="geekblue" style={{ marginRight: 0 }}>
            D
          </Tag>
        </Tooltip>
      );
    }
    if (pubIncluded || editable)
      tags.push(
        <Tooltip key={`record-schema-${type}`} title="Published">
          <Tag color={"purple"} style={{ marginRight: 0 }}>
            P
          </Tag>
        </Tooltip>
      );
  }

  return tags.length ? (
    <Space>{tags}</Space>
  ) : (
    <CloseOutlined style={{ color: "lightgray" }} />
  );
};

CollectionPermissionsColumn.propTypes = {
  permissions: PropTypes.object,
};

export default CollectionPermissionsColumn;
