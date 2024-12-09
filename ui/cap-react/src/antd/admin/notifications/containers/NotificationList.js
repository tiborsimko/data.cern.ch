import { connect } from "react-redux";
import { createNewNotification } from "../../../../actions/builder";
import NotificationList from "../components/NotificationList";

const mapStateToProps = state => ({
  schemaConfig: state.builder.getIn([
    "config",
    "config",
    "notifications",
    "actions",
  ]),
  pathname: state.router.location.pathname,
});

const mapDispatchToProps = {
  createNewNotification: category => createNewNotification(category),
};

export default connect(mapStateToProps, mapDispatchToProps)(NotificationList);
