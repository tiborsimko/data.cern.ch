export const stringToHslColor = (str, s, l) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let h = hash % 360;
  return "hsl(" + h + ", " + s + "%, " + l + "%)";
};

export const permissionsPerUser = permissions => {
  let access = {};
  let accessArray = [];
  let emailsArray = [];
  permissions &&
    Object.keys(permissions).map(action => {
      permissions[action].users.map(user => {
        if (!access[user.email])
          access[user.email] = {
            email: user.email,
            permissions: [],
            type: "user",
            key: `user-${user.email}`
          };
        access[user.email].permissions.push(action);

        if (access[user.email]) {
          accessArray = accessArray.filter(item => item.email != user.email);
        }
        accessArray.push(access[user.email]);
        emailsArray.push(user.email);
      });

      permissions[action].roles.map(role => {
        if (!access[role])
          access[role] = {
            email: role,
            permissions: [],
            type: "egroup",
            key: `egroup-${role}`
          };
        access[role].permissions.push(action);
        if (access[role]) {
          accessArray = accessArray.filter(item => item.email != role);
        }
        accessArray.push(access[role]);
        emailsArray.push(role);
      });
    });

  return {
    permissionsArray: accessArray.sort((a, b) => (a.email < b.email ? -1 : 1)),
    emailsArray,
  };
};
