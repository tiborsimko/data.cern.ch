import { Map, fromJS } from "immutable";

import {
  UPDATE_SCHEMA_CONFIG,
  UPDATE_SCHEMA_INITIAL_CONFIG,
  UPDATE_NOTIFICATION_BY_INDEX,
  UPDATE_NOTIFICATIONS,
  REMOVE_NOTIFICATION,
  CREATE_NOTIFICATION_GROUP,
  SET_SCHEMA_LOADING,
  SYNCHRONIZE_FORMULE_STATE,
  SET_SCHEMA_PERMISSIONS,
} from "../actions/builder";

const initialState = Map({
  initialConfig: {},
  config: Map({}),
  loading: false,
  permissions: null,
});

export default function schemaReducer(state = initialState, action) {
  switch (action.type) {
    case SYNCHRONIZE_FORMULE_STATE:
      return state.set("formuleState", action.value);
    case SET_SCHEMA_LOADING:
      return state.set("loading", action.value);
    case UPDATE_SCHEMA_CONFIG:
      return state.set("config", fromJS(action.config));
    case UPDATE_SCHEMA_INITIAL_CONFIG:
      return state.set("initialConfig", fromJS(action.config));
    case UPDATE_NOTIFICATION_BY_INDEX:
      return state.setIn(action.payload.path, action.payload.value);
    case UPDATE_NOTIFICATIONS:
      return state.setIn(action.payload.path, action.payload.value);
    case REMOVE_NOTIFICATION:
      return state.setIn(action.payload.path, action.payload.notification);
    case CREATE_NOTIFICATION_GROUP:
      return state.setIn(action.path, []);
    case SET_SCHEMA_PERMISSIONS:
      return state.set("permissions", action.permissions);
    default:
      return state;
  }
}
