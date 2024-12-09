import PropTypes from "prop-types";
import { Col, Row, Spin } from "antd";
import { FormPreview, SchemaPreview, SelectOrEdit } from "react-formule";

const SchemaWizard = ({ loading }) => {
  if (loading)
    return (
      <Row style={{ height: "100%" }} align="middle" justify="center">
        <Spin size="large" />
      </Row>
    );
  return (
    <Row style={{ height: "100%" }}>
      <Col
        xs={10}
        sm={5}
        style={{
          overflowX: "hidden",
          height: "100%",
          display: "flex",
        }}
        className="tour-field-types"
      >
        <SelectOrEdit />
      </Col>
      <Col
        xs={14}
        sm={5}
        style={{
          overflowX: "hidden",
          height: "100%",
          padding: "0px 15px",
          backgroundColor: "#F6F7F8",
        }}
        className="tour-schema-preview"
      >
        <SchemaPreview />
      </Col>
      <Col
        xs={24}
        sm={14}
        style={{ overflowX: "hidden", height: "100%", padding: "0px 15px" }}
        className="tour-form-preview"
      >
        <FormPreview />
      </Col>
    </Row>
  );
};

SchemaWizard.propTypes = {
  loader: PropTypes.bool,
  field: PropTypes.object,
};

export default SchemaWizard;
