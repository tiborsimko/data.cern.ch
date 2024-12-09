import { connect } from "react-redux";
import { saveSchemaChanges } from "../../../actions/builder";
import { pushPath } from "../../../actions/support";
import Header from "../components/Header";

function mapStateToProps(state) {
  return {
    config: state.builder.get("config"),
    pathname: state.router.location.pathname,
    formuleState: state.builder.get("formuleState"),
  };
}

function mapDispatchToProps(dispatch) {
  return {
    saveSchemaChanges: () => dispatch(saveSchemaChanges()),
    pushPath: path => dispatch(pushPath(path)),
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Header);
