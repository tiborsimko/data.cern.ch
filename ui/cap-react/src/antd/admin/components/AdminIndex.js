import { Card, Col, Row } from "antd";
import CreateForm from "../components/CreateForm";
import DropZoneForm from "../components/DropZoneForm";
import SelectContentType from "../containers/SelectContentType";

const AdminIndex = () => {
  return (
    <Row justify="center" style={{ height: "100%" }} align="middle">
      <Col xs={22} lg={16}>
        <Card title="Create your form dynamically">
          <Row gutter={[32, 32]}>
            <Col xs={22} md={12} xl={8}>
              <Card title="Create your own schema" style={{ height: "100%" }}>
                <CreateForm />
              </Card>
            </Col>
            <Col xs={22} md={12} xl={8}>
              <Card title="Import your own JSON" style={{ height: "100%" }}>
                <DropZoneForm />
              </Card>
            </Col>
            <Col xs={22} md={24} xl={8}>
              <Card
                title="Select a pre-defined schema"
                style={{ height: "100%" }}
              >
                <SelectContentType />
              </Card>
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  );
};

export default AdminIndex;
