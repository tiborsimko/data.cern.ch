import PropTypes from "prop-types";
import { Descriptions, Space, Tag, Typography } from "antd";

const Ror = ({ data }) => {
  return (
    <Descriptions bordered size="small" column={1}>
      <Descriptions.Item label="Name">
        <Space>
          <Typography.Title level={5} style={{ marginBottom: 0 }}>
            {data.name}
          </Typography.Title>
          {data.acronyms && data.acronyms.length > 0 && (
            <Tag color="blue">{data.acronyms}</Tag>
          )}
        </Space>
      </Descriptions.Item>
      <Descriptions.Item label="Country">
        {data.country.country_name} ({data.country.country_code})
      </Descriptions.Item>
      <Descriptions.Item label="Type">
        {data.types && data.types.map(type => <Tag key={type}>{type}</Tag>)}
      </Descriptions.Item>
      <Descriptions.Item label="URL">
        <a href={data.links}>{data.links}</a>
      </Descriptions.Item>
    </Descriptions>
  );
};

Ror.propTypes = {
  data: PropTypes.object,
};

export default Ror;
