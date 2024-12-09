import PropTypes from "prop-types";
import { Avatar, Col, Row, Typography } from "antd";
import { stringToHslColor } from "../../../utils";

const Orcid = ({ data }) => {
  return (
    <Row wrap={false} gutter={20} align="middle">
      <Col flex="none">
        <Avatar
          size={50}
          style={{
            backgroundColor: stringToHslColor(
              `${data.person.name["family-name"].value} ${data.person.name["family-name"].value}`,
              40,
              70
            ),
          }}
        >
          {data.person.name["given-names"].value[0]}
          {data.person.name["family-name"].value[0]}
        </Avatar>
      </Col>
      <Col flex="auto">
        <Typography.Title level={5} style={{ marginBottom: 0 }}>
          {data.person.name["given-names"].value}{" "}
          {data.person.name["family-name"].value}
        </Typography.Title>
        <Typography.Text>
          <a href={data["orcid-identifier"].uri}>
            {data["orcid-identifier"].uri}
          </a>
        </Typography.Text>
      </Col>
    </Row>
  );
};

Orcid.propTypes = {
  data: PropTypes.object,
};

export default Orcid;
