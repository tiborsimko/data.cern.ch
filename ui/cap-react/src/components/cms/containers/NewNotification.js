import { connect } from "react-redux";
import NewNotification from "../components/Notifications/NotificationWizard/NewNotification";
import { updateNotificationByIndex } from "../../../actions/schemaWizard";

const mapStateToProps = state => {
  const index = state.schemaWizard.get("selectedNotificationIndex");
  const category = state.schemaWizard.get("selectedNotificationCategory");

  const selectedNotification = state.schemaWizard.getIn([
    "schemaConfig",
    "notifications",
    "actions",
    category,
    index
  ]);
  return {
    schemaConfig: state.schemaWizard.get("schemaConfig"),
    selectedNotification: selectedNotification
  };
};

const mapDispatchToProps = dispatch => ({
  updateNotificationByIndex: (key, value) =>
    dispatch(updateNotificationByIndex(key, value))
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(NewNotification);
