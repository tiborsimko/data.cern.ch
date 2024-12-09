import { connect } from "react-redux";
import {
  createNewNotification,
  removeNotification,
  updateNotificationData,
} from "../../../../actions/builder";
import NotificationEdit from "../components/NotificationEdit";

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
  removeNotification: (index, category) => removeNotification(index, category),
  updateNotificationData: (data, index, category) =>
    updateNotificationData(data, index, category),
};

export default connect(mapStateToProps, mapDispatchToProps)(NotificationEdit);
