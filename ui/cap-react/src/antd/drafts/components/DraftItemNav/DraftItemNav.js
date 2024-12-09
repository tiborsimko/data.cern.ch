import PropTypes from "prop-types";
import { Layout, Grid, Drawer } from "antd";
import NavMenu from "./NavMenu";

const DraftItemNav = ({
  match,
  history,
  visibleMenuDrawer,
  onClose,
  formErrors,
}) => {
  const { useBreakpoint } = Grid;
  const screens = useBreakpoint();

  return !screens.lg ? (
    <Drawer
      title="Draft Navigation Menu"
      placement="left"
      onClose={onClose}
      open={visibleMenuDrawer}
      style={{ body: { padding: 0 }}}
      key="menu"
    >
      <NavMenu match={match} history={history} formErrors={formErrors} />
    </Drawer>
  ) : (
    <Layout.Sider
      trigger={null}
      style={{ height: "100%" }}
      collapsible
      collapsed={!screens.xxl}
    >
      <NavMenu match={match} history={history} formErrors={formErrors} />
    </Layout.Sider>
  );
};

DraftItemNav.propTypes = {
  match: PropTypes.object,
  history: PropTypes.object,
  formErrors: PropTypes.oneOfType([PropTypes.object, PropTypes.array]),
  onClose: PropTypes.func,
  visibleMenuDrawer: PropTypes.bool,
};

export default DraftItemNav;
