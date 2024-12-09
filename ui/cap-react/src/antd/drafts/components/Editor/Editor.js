import { useState } from "react";
import PropTypes from "prop-types";
import { Col, Layout } from "antd";
import Error from "../../../partials/Error/";
import { transformSchema } from "../../../partials/Utils/schema";
import Header from "../../containers/EditorHeader";
import { canEdit } from "../../utils/permissions";
import { FormuleForm } from "react-formule";

import objectPath from "object-path";

const Editor = ({
  schemaErrors,
  schemas = { schema: {}, uiSchema: {} },
  formData,
  extraErrors,
  formRef,
  history,
  canAdmin,
  canUpdate,
}) => {
  const [mode, setMode] = useState(
    (history.location.state && history.location.state.mode) || "edit"
  );
  if (!schemas) return null;
  if (schemaErrors.length > 0) {
    return <Error error={schemaErrors[0]} />;
  }
  let _schema =
    schemas && schemas.schema ? transformSchema(schemas.schema) : null;

  // mainly this is used for the drafts forms
  // we want to allow forms to be saved even without required fields
  // if these fields are not filled in when publishing then an error will be shown
  const transformErrors = errors => {
    errors = errors
      .filter(item => item.name != "required")
      .map(error => {
        console.log(error);
        if (error.name == "required") return null;

        // Update messages for undefined fields when required,
        // from "should be string" ==> "Either edit or remove"
        if (error.message == "should be string") {
          let errorMessages = objectPath.get(formData, error.property);
          if (errorMessages == undefined)
            error.message = "Either edit or remove";
        }

        return error;
      });

    return errors;
  };

  return (
    <Col span={24} style={{ height: "100%", overflow: "auto" }}>
      <Layout style={{ height: "100%", padding: 0 }}>
        <Header formRef={formRef} mode={mode} updateMode={setMode} />
        <Layout.Content style={{ height: "100%", overflowX: "hidden" }}>
          <FormuleForm
            formData={formData || {}}
            formRef={formRef}
            schema={_schema}
            uiSchema={schemas.uiSchema || {}}
            extraErrors={extraErrors || {}}
            readonly={!canEdit(canAdmin, canUpdate)}
            isPublished={mode != "edit"}
            transformErrors={transformErrors}
          />
        </Layout.Content>
      </Layout>
    </Col>
  );
};

Editor.propTypes = {
  schemaErrors: PropTypes.array,
  schemas: PropTypes.object,
  formData: PropTypes.object,
  extraErrors: PropTypes.object,
  formRef: PropTypes.object,
  history: PropTypes.object,
  canAdmin: PropTypes.bool,
  canUpdate: PropTypes.bool,
};

export default Editor;
