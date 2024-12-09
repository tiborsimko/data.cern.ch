import HomeImage from "../img/home-image.svg?react";
import { Row, Col, Typography, Space, Grid } from "antd";
import {
  DatabaseOutlined,
  TeamOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { PRIMARY_COLOR } from "../../utils/theme";

const Intro = () => {
  const { useBreakpoint } = Grid;
  const screens = useBreakpoint();

  const boxes = [
    {
      title: "Capture",
      icon: <DatabaseOutlined style={{ fontSize: "2em" }} />,
      description:
        "Preserve elements needed to understand and rerun your analysis",
    },
    {
      title: "Collaborate",
      icon: <TeamOutlined style={{ fontSize: "2em" }} />,
      description:
        "Share your analysis with other users, your collaboration or group",
    },
    {
      title: "Reuse",
      icon: <ReloadOutlined style={{ fontSize: "2em" }} />,
      description:
        "Run containerized workflows and easily reuse analysis components",
    },
  ];
  return (
    <Col xs={22} xxl={18} style={{ padding: "30px" }} id="home">
      <Space
        direction="vertical"
        style={{ width: "100%", marginTop: screens.md ? "50px" : "10px" }}
        size={[0, 100]}
      >
        <Row justify="center" align="middle" gutter={[80, 80]}>
          <Col>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Typography.Title
                style={{ fontSize: "40pt", marginBottom: "15px" }}
              >
                CERN
                <br />
                <span style={{ color: PRIMARY_COLOR, fontWeight: "lighter" }}>
                  Analysis Preservation
                </span>
              </Typography.Title>
              <Typography.Title level={3} italic>
                Capture, preserve and reuse physics analyses
              </Typography.Title>
            </Space>
          </Col>
          <Col flex="auto" xs={18} xl={12}>
            <HomeImage style={{ width: "100%" }} />
          </Col>
        </Row>
        <Row justify="space-around" gutter={[50, 50]}>
          {boxes.map(item => (
            <Col
              md={6}
              xs={18}
              key={item.title}
              style={{ textAlign: "center" }}
            >
              <Space direction="vertical" size="large">
                {item.icon}
                <Typography.Title level={3}>{item.title}</Typography.Title>
                <Typography.Paragraph style={{ fontSize: "1.1rem" }}>
                  {item.description}
                </Typography.Paragraph>
              </Space>
            </Col>
          ))}
        </Row>
      </Space>
    </Col>
  );
};

Intro.propTypes = {};

export default Intro;
