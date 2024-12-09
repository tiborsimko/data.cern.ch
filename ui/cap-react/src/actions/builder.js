import axios from "../axios";
import { isEqual } from "lodash-es";
import { fromJS } from "immutable";
import { push } from "connected-react-router";
import { notification } from "antd";
import { CMS, CMS_NEW } from "../antd/routes";
import { initFormuleSchemaWithNotifications } from "../antd/admin/utils";
import { updateDepositGroups } from "./auth";
import { getFormuleState } from "react-formule";

export const SYNCHRONIZE_FORMULE_STATE = "SYNCHRONIZE_FORMULE_STATE";

export const SET_SCHEMA_LOADING = "SET_SCHEMA_LOADING";
export const UPDATE_SCHEMA_CONFIG = "UPDATE_SCHEMA_CONFIG";
export const UPDATE_SCHEMA_INITIAL_CONFIG = "UPDATE_SCHEMA_INITIAL_CONFIG";

export const UPDATE_NOTIFICATION_BY_INDEX = "UPDATE_NOTIFICATION_BY_INDEX";
export const UPDATE_NOTIFICATIONS = "UPDATE_NOTIFICATIONS";
export const REMOVE_NOTIFICATION = "REMOVE_NOTIFICATION";
export const CREATE_NOTIFICATION_GROUP = "CREATE_NOTIFICATION_GROUP";

export const SET_SCHEMA_PERMISSIONS = "SET_SCHEMA_PERMISSIONS";

export const synchronizeFormuleState = value => ({
  type: SYNCHRONIZE_FORMULE_STATE,
  value,
});

export const setSchemaLoading = value => ({
  type: SET_SCHEMA_LOADING,
  value,
});

export const updateSchemaConfig = config => ({
  type: UPDATE_SCHEMA_CONFIG,
  config,
});

export const updateSchemaInitialConfig = config => ({
  type: UPDATE_SCHEMA_INITIAL_CONFIG,
  config,
});

export const updateNotificationByIndex = data => ({
  type: UPDATE_NOTIFICATION_BY_INDEX,
  payload: data,
});

export const updateNotifications = item => ({
  type: UPDATE_NOTIFICATIONS,
  payload: item,
});

export const deleteNotification = notification => ({
  type: REMOVE_NOTIFICATION,
  payload: notification,
});

export const createNotificationCategory = category => ({
  type: CREATE_NOTIFICATION_GROUP,
  path: ["config", "config", "notifications", "actions", category],
});

export const createNewNotification = category => (dispatch, getState) => {
  const valuesPath = ["config", "config", "notifications", "actions", category];

  let notifications = fromJS(getState().builder.getIn(valuesPath, []));
  notifications = notifications.push(fromJS({}));

  dispatch(
    updateNotifications({
      path: valuesPath,
      value: notifications,
      category,
      index: notifications.size - 1,
    })
  );

  return notifications.size - 1;
};

export const removeNotification = (index, category) => (dispatch, getState) => {
  const path = ["config", "config", "notifications", "actions", category];
  let notification = getState().builder.getIn(path);
  let newNotification = notification.delete(index);
  dispatch(deleteNotification({ path, notification: newNotification }));
};

export const updateNotificationData = (data, index, category) => {
  return dispatch => {
    const valuesPath = [
      "config",
      "config",
      "notifications",
      "actions",
      category,
      index,
    ];

    dispatch(
      updateNotificationByIndex({ path: valuesPath, value: fromJS(data) })
    );
  };
};

export const getSchema = (name, version = null) => {
  const schemaLink = version
    ? `/api/jsonschemas/${name}/${version}?resolve=1&config=1`
    : `/api/jsonschemas/${name}?resolve=1&config=1`;

  return dispatch => {
    dispatch(setSchemaLoading(true));
    axios
      .get(schemaLink)
      .then(resp => {
        let schema = resp.data;
        let { deposit_schema, deposit_options } = schema;

        if (deposit_schema && deposit_options) {
          // The schemas are sent to be managed by formule but the config is kept in CAP (see function body)
          initFormuleSchemaWithNotifications(schema);
          dispatch(setSchemaLoading(false));
        }
      })
      .catch(() => {
        dispatch(push(CMS));
        notification.error({
          message: "Schema fetch failed",
          description: "Make sure that schema name and version are correct ",
        });
      });
  };
};

export const saveSchemaChanges = () => (dispatch, getState) => {
  const state = getState();
  const config = state.builder.get("config");
  const formuleState = getFormuleState();
  const pathname = state.router.location.pathname;
  const sendData = {
    deposit_schema: formuleState.current.schema,
    deposit_options: formuleState.current.uiSchema,
    ...config.toJS(),
  };

  // check if there is no name or version
  // these fields are required for the schema to be created or updated
  if (
    !config.get("name") ||
    !config.get("version") ||
    !config.get("fullname")
  ) {
    notification.warning({
      description: "Schema name, fullname and version are required",
      message: "Missing information",
    });
    return;
  }

  // check whether there are changes to the deposit schema
  const isSchemaUpdated = !isEqual(
    formuleState.current.schema,
    formuleState.initial.schema
  );
  // check whether there are changes to the config object
  const isConfigVersionUpdated =
    config.get("version") != state.builder.getIn(["initialConfig", "version"]);

  if (isSchemaUpdated && !isConfigVersionUpdated) {
    notification.warning({
      message: "These changes require new version",
      description: "please make sure to update the version of the schema",
    });
    return;
  }

  if (pathname.startsWith(CMS_NEW) || isSchemaUpdated) {
    return axios
      .post("/api/jsonschemas", sendData)
      .then(res => {
        initFormuleSchemaWithNotifications(res.data);
        notification.success({
          message: "New schema created",
          description: "schema successfully created",
        });
        dispatch(updateDepositGroups());
        dispatch(
          push(`/admin/editor/${config.get("name")}/${config.get("version")}`)
        );
      })
      .catch(err => {
        let errorHeading, errorMessage;
        if (typeof err.response.data.message === "object") {
          let errMsg = Object.entries(err.response.data.message);
          errorHeading = errMsg[0][0];
          errorMessage = errMsg[0][1][0];
        } else {
          errorHeading = "Schema Creation";
          errorMessage =
            err.response.data.message ||
            "Error while creating, please try again";
        }
        notification.error({
          message: errorHeading,
          description: errorMessage,
        });
      });
  }

  return axios
    .put(
      `/api/jsonschemas/${config.get("name")}/${config.get("version")}`,
      sendData
    )
    .then(() =>
      notification.success({
        message: "Schema Updated",
        description: "changes successfully applied",
      })
    )
    .catch(() =>
      notification.error({
        message: "Schema Updates",
        description: "Error while saving, please try again",
      })
    );
};

export const setSchemaPermissions = permissions => ({
  type: SET_SCHEMA_PERMISSIONS,
  permissions,
});

export const getSchemaPermissions = (name, version = null) => {
  let schemaPermissionLink;

  if (version)
    schemaPermissionLink = `/api/jsonschemas/${name}/${version}/permissions`;
  else schemaPermissionLink = `/api/jsonschemas/${name}/permissions`;
  return function (dispatch) {
    axios
      .get(schemaPermissionLink)
      .then(resp => {
        dispatch(setSchemaPermissions(resp.data));
      })
      .catch(() => {
        notification.error({
          message: "Fetching permissions failed",
          description: "There was an error fetching the schema permissions",
        });
      });
  };
};

export const postSchemaPermissions = (name, version = null, permissions) => {
  let schemaPermissionLink;

  if (version)
    schemaPermissionLink = `/api/jsonschemas/${name}/${version}/permissions`;
  else schemaPermissionLink = `/api/jsonschemas/${name}/permissions`;
  return function (dispatch) {
    axios
      .post(schemaPermissionLink, permissions)
      .then(() => {
        dispatch(getSchemaPermissions(name, version));
      })
      .catch(() => {
        notification.error({
          message: "Updating schema permissions failed",
          description: "There was an error updating the schema permissions",
        });
      });
  };
};

export const deleteSchemaPermissions = (name, version = null, permissions) => {
  let schemaPermissionLink;

  if (version)
    schemaPermissionLink = `/api/jsonschemas/${name}/${version}/permissions`;
  else schemaPermissionLink = `/api/jsonschemas/${name}/permissions`;
  return function (dispatch) {
    axios
      .delete(schemaPermissionLink, { data: permissions })
      .then(() => {
        dispatch(getSchemaPermissions(name, version));
      })
      .catch(() => {
        notification.error({
          message: "Deleting schema permissions failed",
          description: "There was an error deleting the schema permissions",
        });
      });
  };
};
