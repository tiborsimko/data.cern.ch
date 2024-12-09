import { connect } from "react-redux";
import SelectContentType from "../components/SelectContentType";

function mapStateToProps(state) {
  return {
    contentTypes: state.auth.getIn(["currentUser", "depositGroups"]),
  };
}

export default connect(mapStateToProps)(SelectContentType);
