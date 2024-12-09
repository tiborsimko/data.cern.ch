import PropTypes from "prop-types";
import { Col, Drawer, Grid } from "antd";
import FileList from "../../partials/FileList";

const SideBar = ({ files, status, onClose, visibleFileDrawer }) => {
  const { useBreakpoint } = Grid;
  const screens = useBreakpoint();
  return !screens.xxl ? (
    <Drawer
      title="File Settings"
      placement="right"
      onClose={onClose}
      open={visibleFileDrawer}
      key="fileSettings"
      size="large"
      style={{ body: { padding: "5px" }}}
      contentWrapperStyle={{ width: !screens.lg ? "80%" : "40%" }}
    >
      <FileList files={files} status={status} />
    </Drawer>
  ) : (
    <Col
      xxl={5}
      style={{
        background: "#fff",
        padding: "10px 5px",
        height: "100%",
        overflowX: "hidden",
      }}
    >
      <FileList files={files} status={status} />
    </Col>
  );
};

SideBar.propTypes = {
  status: PropTypes.string,
  onClose: PropTypes.func,
  visibleFileDrawer: PropTypes.bool,
  files: PropTypes.object,
};

export default SideBar;
