import { initFormuleSchema } from "react-formule";
import { merge } from "lodash-es";
import store from "../../../store/configureStore";
import {
  updateSchemaConfig,
  updateSchemaInitialConfig,
} from "../../../actions/builder";

export const SIZE_OPTIONS = {
  xsmall: 8,
  small: 12,
  medium: 16,
  large: 20,
  xlarge: 24,
};

const NOTIFICATIONS = {
  notifications: {
    actions: {
      review: [],
      publish: [],
    },
  },
};

export const initFormuleSchemaWithNotifications = (
  data = {},
  title,
  description
) => {
  data.config = merge(data.config || {}, NOTIFICATIONS);
  const { deposit_schema, deposit_options, ...configs } = data;
  initFormuleSchema(
    { schema: deposit_schema, uiSchema: deposit_options, id: configs.name },
    title,
    description
  );
  store.dispatch(updateSchemaConfig(configs));
  store.dispatch(updateSchemaInitialConfig(configs));
};
