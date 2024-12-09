import { connect } from "react-redux";
import Editor from "../components/Editor";

const mapStateToProps = state => ({
  schemas: state.draftItem.get("schemas"),
  formData: state.draftItem.get("formData"),
  extraErrors: state.draftItem.get("extraErrors"),
  schemaErrors: state.draftItem.get("schemaErrors"),
  canUpdate: state.draftItem.get("can_update"),
  canAdmin: state.draftItem.get("can_admin"),
});

export default connect(mapStateToProps)(Editor);
