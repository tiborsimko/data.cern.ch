import PropTypes from "prop-types";
import { Descriptions } from "antd";

const Zenodo = ({ data }) => {
  return (
    <Descriptions bordered size="small" column={1}>
      <Descriptions.Item label="ID">{data.id}</Descriptions.Item>
      <Descriptions.Item label="Title">{data.metadata.title}</Descriptions.Item>
      <Descriptions.Item label="DOI">{data.metadata.doi}</Descriptions.Item>
      <Descriptions.Item label="URL">
        <a href={data.links.self}>{data.links.self}</a>
      </Descriptions.Item>
    </Descriptions>
  );
};

Zenodo.propTypes = {
  data: PropTypes.object,
};

export default Zenodo;
