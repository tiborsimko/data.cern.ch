import { commonFields, extraFields } from "react-formule";

import { CloudDownloadOutlined, FileOutlined } from "@ant-design/icons";
import CernUsers from "./customFields/CernUsers";
import CapFiles from "./customFields/CapFiles";
import IdFetcher from "./customFields/IdFetcher";
import ImportDataField from "./customFields/ImportDataField";
import SchemaPathSuggester from "./customFields/SchemaPathSuggester";

export const customFieldTypes = {
  advanced: {
    CapFiles: {
      title: "File upload",
      icon: <FileOutlined />,
      description: "Upload Files",
      child: {},
      optionsSchema: {
        type: "object",
        title: "File upload widget",
        properties: {
          ...commonFields.optionsSchema,
          readOnly: extraFields.optionsSchema.readOnly,
          isRequired: extraFields.optionsSchema.isRequired,
        },
      },
      optionsSchemaUiSchema: {
        readOnly: extraFields.optionsSchemaUiSchema.readOnly,
        isRequired: extraFields.optionsSchemaUiSchema.isRequired,
      },
      optionsUiSchema: {
        ...commonFields.optionsUiSchema,
      },
      optionsUiSchemaUiSchema: {
        ...commonFields.optionsUiSchemaUiSchema,
      },
      default: {
        schema: {
          type: "string",
        },
        uiSchema: {
          "ui:field": "CapFiles",
        },
      },
    },
    idFetcher: {
      title: "ID fetcher",
      icon: <CloudDownloadOutlined />,
      description: "Fetch data from ZENODO, ORCiD or ROR",
      child: {},
      optionsSchema: {
        type: "object",
        title: "ID Fetcher Field Schema",
        properties: {
          ...commonFields.optionsSchema,
          readOnly: extraFields.optionsSchema.readOnly,
          isRequired: extraFields.optionsSchema.isRequired,
        },
      },
      optionsSchemaUiSchema: {
        readOnly: extraFields.optionsSchemaUiSchema.readOnly,
        isRequired: extraFields.optionsSchemaUiSchema.isRequired,
      },
      optionsUiSchema: {
        type: "object",
        title: "UI Schema",
        properties: {
          ...commonFields.optionsUiSchema.properties,
          "ui:servicesList": {
            title: "Select the services you want to allow",
            type: "array",
            items: {
              type: "string",
              oneOf: [
                { const: "orcid", title: "ORCiD" },
                { const: "ror", title: "ROR" },
                { const: "zenodo", title: "Zenodo" },
                { const: "capRecords", title: "CAP Records" },
                { const: "capDeposits", title: "CAP Deposits" },
              ],
            },
            uniqueItems: "true",
          },
        },
      },
      optionsUiSchemaUiSchema: {
        ...commonFields.optionsUiSchemaUiSchema,
        "ui:servicesList": {
          "ui:widget": "checkbox",
        },
      },
      default: {
        schema: {
          type: "object",
          properties: {},
        },
        uiSchema: {
          "ui:servicesList": ["capDeposits"],
          "ui:field": "idFetcher",
        },
      },
    },
  },
  simple: {
    importData: {
      title: "Import Data",
      icon: <FileOutlined />,
      description: "Provided a URL or query",
      child: {},
      optionsSchema: {
        type: "object",
        title: "File upload widget",
        properties: {
          ...commonFields.optionsSchema,
          readOnly: extraFields.optionsSchema.readOnly,
          isRequired: extraFields.optionsSchema.isRequired,
        },
      },
      optionsSchemaUiSchema: {
        readOnly: extraFields.optionsSchemaUiSchema.readOnly,
        isRequired: extraFields.optionsSchemaUiSchema.isRequired,
      },
      optionsUiSchema: {
        ...commonFields.optionsUiSchema,
        properties: {
          ...commonFields.optionsUiSchema.properties,
          "x-cap-import-data": {
            type: "object",
            properties: {
              queryUrl: {
                title: "Query URL",
                description: "URL to query for and wait for response data",
                type: "string",
                placeholder: "/api/deposits",
              },
              queryParam: {
                type: "string",
                title: "Query Param",
                description: "URL to query for and wait for response data",
              },
              hitTitle: {
                type: "string",
                title: "Item Title",
                description:
                  "What to display as result item title? Should be path of the response data, e.g 'metadata.general_title'",
              },
              hitDescription: {
                type: "string",
                title: "Item Description",
                description:
                  "What to display as result item description? Should be path of the response data, e.g 'metadata.general_title'",
              },
              resultsPath: {
                type: "string",
                title: "Results path",
                description:
                  "If response data is not an array, provide the path in the data where the results array exists. E.g 'hits.hits'",
              },
              resultsTotalPath: {
                type: "string",
                title: "Results Total path",
                description:
                  "If results total is returned, specify the path in the response data. E.g 'hits.hits'",
              },
            },
          },
        },
      },
      optionsUiSchemaUiSchema: {
        ...commonFields.optionsUiSchemaUiSchema,
        "x-cap-import-data": {
          queryUrl: {
            "ui:placeholder": "/api/deposits",
          },
          queryParam: {
            "ui:placeholder": "q",
          },
          hitTitle: {
            "ui:placeholder": "metadata.general_title",
          },
          hitDescription: {
            "ui:placeholder": "created_by.email",
          },
          resultsPath: {
            "ui:placeholder": "hits.hits",
          },
        },
      },
      default: {
        schema: {
          type: "object",
        },
        uiSchema: {
          "ui:field": "importData",
        },
      },
    },
  },
};

export const customFields = {
  cernUsers: CernUsers,
  CapFiles: CapFiles,
  idFetcher: IdFetcher,
  importData: ImportDataField,
  schemaPathSuggester: SchemaPathSuggester,
};
