import { PluginComponent } from "react-markdown-editor-lite";
import { EditOutlined, EyeOutlined } from "@ant-design/icons";

export default class RichEditorPreviewPlugin extends PluginComponent {
  static pluginName = "cap-toggle";
  static align = "right";

  constructor(props) {
    super(props);
    this.handleClick = this.handleClick.bind(this);
    this.state = {
      isEditView: this.getConfig("isEditView"),
    };
  }

  handleClick() {
    if (this.state.isEditView.md) {
      this.editor.setView({ html: true, md: false });
      this.setState({ isEditView: { html: true, md: false } });
    } else {
      this.editor.setView({ html: false, md: true });
      this.setState({ isEditView: { html: false, md: true } });
    }
  }

  render() {
    return this.state.isEditView.md ? (
      <EyeOutlined onClick={this.handleClick} />
    ) : (
      <EditOutlined onClick={this.handleClick} />
    );
  }
}
