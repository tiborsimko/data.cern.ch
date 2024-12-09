import { Row, Col, Space, Typography, Button, Grid } from "antd";
import {
  MailOutlined,
  TwitterOutlined,
  GithubOutlined,
} from "@ant-design/icons";

import AliceIcon from "../img/alice.svg?react";
import AtlasIcon from "../img/atlas.svg?react";
import CmsIcon from "../img/cms.svg?react";
import LHCbLogo from "../img/lhcb-logo.svg?react";

const { useBreakpoint } = Grid;

const Contact = () => {
  const screens = useBreakpoint();

  return (
    <Col span={24}>
      <Row justify="center" style={{ padding: "30px", background: "#fff" }}>
        <Col xs={24} lg={16}>
          <Row
            justify={!screens.sm ? "center" : "space-between"}
            gutter={[32, 32]}
          >
            <Col xs={24} md={12}>
              <Space direction="vertical">
                <Button
                  type="link"
                  href="mailto:analysis-preservation-support@cern.ch"
                  icon={<MailOutlined />}
                  size="large"
                >
                  analysis-preservation-support@cern.ch
                </Button>
                <Button
                  type="link"
                  href="https://twitter.com/analysispreserv"
                  target="_blank"
                  icon={<TwitterOutlined />}
                  size="large"
                >
                  @analysispreserv
                </Button>
                <Button
                  type="link"
                  href="https://github.com/cernanalysispreservation/analysispreservation.cern.ch"
                  target="_blank"
                  icon={<GithubOutlined />}
                  size="large"
                >
                  @cernanalysispreservation
                </Button>
              </Space>
            </Col>
            <Col xs={24} md={12} style={{ textAlign: "right" }}>
              <Space direction="vertical">
                <Typography.Title level={4} style={{ textAlign: "left" }}>
                  Supported by:
                </Typography.Title>
                <Space size="large">
                  <AliceIcon width="65px" />
                  <AtlasIcon width="65px" />
                  <CmsIcon width="65px" />
                  <LHCbLogo width="65px" />
                </Space>
              </Space>
            </Col>
          </Row>
        </Col>
      </Row>
    </Col>
  );
};

export default Contact;
