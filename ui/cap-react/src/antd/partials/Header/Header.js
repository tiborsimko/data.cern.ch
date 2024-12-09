import PropTypes from "prop-types";
import CAPLogoLight from "../../../img/cap-logo-light.svg?react";
import { Row, Col, Grid } from "antd";

import { Link } from "react-router-dom";
import LoggedInMenu from "./LoggedInMenu";
import SimpleMenu from "./Menu";

import AntSearchBar from "../SearchBar";

const { useBreakpoint } = Grid;

const Header = ({ logout, permissions, isLoggedIn }) => {
  const screens = useBreakpoint();

  return (
    <Row justify={isLoggedIn && "space-between"}>
      <Col xs={12} md={8} lg={6} xl={5} xxl={3}>
        <Link to="/">
          <CAPLogoLight
            height="32px"
            style={{ verticalAlign: "middle", marginLeft: "16px" }}
          />
        </Link>
      </Col>
      {isLoggedIn ? (
        <>
          {screens.md && (
            <Col flex="auto">
              <AntSearchBar />
            </Col>
          )}
          <Col xs={12} md={8} lg={6} xl={5} xxl={3}>
            <LoggedInMenu logout={logout} permissions={permissions} />
          </Col>
        </>
      ) : (
        <Col
          xs={{ order: 2, span: 12 }}
          md={{ span: 16, offset: 4 }}
          lg={{ span: 20, offset: 0 }}
        >
          <SimpleMenu />
        </Col>
      )}
    </Row>
  );
};

Header.propTypes = {
  logout: PropTypes.func,
  permissions: PropTypes.object,
  isLoggedIn: PropTypes.bool,
};

export default Header;
