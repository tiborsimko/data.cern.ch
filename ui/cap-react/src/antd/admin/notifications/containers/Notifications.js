import { connect } from "react-redux";
import { Map } from "immutable";
import Notifications from "../components/Notifications";
import { createNotificationCategory } from "../../../../actions/builder";

const mapStateToProps = state => ({
  schemaConfig: state.builder.getIn(
    ["config", "config", "notifications", "actions"],
    Map({})
  ),
  pathname: state.router.location.pathname,
});

const mapDispatchToProps = dispatch => ({
  createNotificationCategory: category =>
    dispatch(createNotificationCategory(category)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Notifications);
