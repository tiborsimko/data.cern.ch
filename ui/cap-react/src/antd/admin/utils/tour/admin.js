export const steps = [
  {
    target: "body",
    placement: "center",
    disableBeacon: true,
    title: "Welcome to CAP Admin",
    content:
      "Press next to start the tour and learn how to create and edit forms with CAP's advanced form editor.",
  },
  {
    target: ".tour-field-types",
    title: "Field types",
    placement: "right",
    placementBeacon: "top",
    disableBeacon: true,
    content:
      "These are the different fields you can use in a form. They're divided into collections (fields that can contain other fields) normal fields and advanced fields with more specific functionality.",
  },
  {
    target: ".tour-object-field",
    placement: "right",
    content:
      "Object fields are useful to visually group fields of different types in the form.",
  },
  {
    target: ".tour-list-field",
    placement: "right",
    content:
      "List fields allow users to add several instances of the same field. In order to configure them, you need to drag the list field to the tree and afterwards drag a conventional field, say a text field, inside of it. This will allow users to add multiple (the amount can be configured) text fields.",
  },
  {
    target: ".tour-schema-preview",
    placement: "right",
    placementBeacon: "top",
    content:
      "Here you will see a tree with all the fields of your form, displaying the type, id and title (if any). You will be able to open their settings by clicking on them.",
  },
  {
    target: ".tour-form-preview",
    placement: "left",
    placementBeacon: "top",
    content:
      "This is the form preview. It will display the final form as the users are going to see it, allowing you to test if everything works as you desire.",
  },
  {
    target: ".tour-text-field",
    content:
      "You can add elements by dragging and dropping them into the schema tree. Try with a text field.",
  },
  {
    target: ".tour-schema-preview .__Form__ div div div div",
    content:
      "Click on a field to view and edit its properties. You will see two tabs: schema settings, which allow you to define the main settings and behavior of the field, and UI schema settings, which contain extra settings, generally related to how a field is displayed (e.g. its width or, in the case of text fields, whether the text should be automatically transformed to uppercase or not).",
  },
  {
    target: ".tour-root-settings",
    content:
      "Here you can customize the root of the form, changing its name and description (visible only from the admin page) but, more importantly, the width and alignment of all fields of the form from the UI settings tab.",
  },
  {
    target: ".tour-diff",
    content:
      "You can see the JSON schema representation of your form and a diff view of all the current unsaved changes here.",
  },
  {
    target: ".tour-notifications-tab",
    content:
      "The notifications tab allows you create notification templates and define patterns to send them to the appropriate users when an event takes place.",
  },
  {
    target: ".tour-settings-tab",
    content:
      "On a new schema, you will have to provide some settings like id, version, name or experiment before being able to save your changes. Here you can also define permissions for the schema.",
  },
  {
    target: "body",
    placement: "center",
    content: (
      <span>
        You have now learnt the basics of CAP Admin and you are ready to start
        creating your own forms! For more in-depth information, please check the{" "}
        <a href="https://analysispreservation.cern.ch/docs/general/">
          CAP Documentation
        </a>
        .
      </span>
    ),
  },
];
