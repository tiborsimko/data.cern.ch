import { FormuleForm } from "react-formule";
import PropTypes from "prop-types";

const JSONSchemaPreviewer = ({
  schema,
  uiSchema,
  children,
  display = "tabView",
  onChange,
  onSubmit,
  formData,
}) => {
  return (
    schema && (
      <FormuleForm
        schema={schema}
        showErrorList={false}
        uiSchema={{
          "ui:readonly": true,
          ...uiSchema,
          "ui:object": display,
        }}
        liveValidate={false}
        noValidate={true}
        onError={() => {}}
        formData={formData}
        onBlur={() => {}}
        onChange={onChange}
        onSubmit={onSubmit}
        isPublished
      >
        {children}
      </FormuleForm>
    )
  );
};

JSONSchemaPreviewer.propTypes = {
  display: PropTypes.string,
  children: PropTypes.node,
  isPublished: PropTypes.bool,
  schema: PropTypes.object,
  uiSchema: PropTypes.object,
  onChange: PropTypes.func,
  onSubmit: PropTypes.func,
};

export default JSONSchemaPreviewer;
