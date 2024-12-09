import Toggler from "./RichEditorPreviewPlugin";
import "katex/dist/katex.min.css";
import MarkdownIt from "markdown-it";
import katex from "katex";
import tm from "markdown-it-texmath";
import "markdown-it-texmath/css/texmath.css";
import PropTypes from "prop-types";
import { useRef } from "react";
import MdEditor from "react-markdown-editor-lite";
import "react-markdown-editor-lite/lib/index.css";

const RichEditorWidget = props => {
  const mdParser = new MarkdownIt();
  mdParser.use(tm, {
    engine: katex,
    delimiters: "dollars",
    katexOptions: { macros: { "\\RR": "\\mathbb{R}" } },
  });
  let myEditor = useRef(null);

  const renderHTML = text => {
    return mdParser.render(text);
  };
  const handleEditorChange = values => {
    props.onChange(values.text);
  };

  MdEditor.use(Toggler, {
    isEditView: { html: false, md: true },
  });

  return (
    <MdEditor
      style={{
        height:
          props.height === 0
            ? undefined
            : props.height > 0
            ? props.height
            : "500px",
        border: props.noBorder ? "none" : undefined,
      }}
      config={{
        canView: {
          fullScreen: false,
          md: false,
          html: false,
          ...props.canViewProps,
          ...(props.readonly || props.disabled
            ? {
                md: false,
                html: true,
                fullScreen: true,
                menu: false,
                hideMenu: false,
              }
            : {}),
        },
        view: {
          fullScreen: false,
          md: true,
          html: false,
          ...props.viewProps,
          ...(props.readonly || props.disabled
            ? {
                md: false,
                html: true,
                fullScreen: true,
                menu: false,
                hideMenu: false,
              }
            : {}),
        },
      }}
      readOnly={props.readonly}
      renderHTML={renderHTML}
      onChange={handleEditorChange}
      value={props.value}
      ref={myEditor}
      key={props.noBorder}
    />
  );
};

RichEditorWidget.propTypes = {
  onChange: PropTypes.func,
  value: PropTypes.string,
  readonly: PropTypes.bool,
  displayedFromModal: PropTypes.bool,
  canViewProps: PropTypes.object,
  viewProps: PropTypes.object,
  noBorder: PropTypes.bool,
  height: PropTypes.number,
};

export default RichEditorWidget;
