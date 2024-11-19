import PropTypes from "prop-types";
import { Menu, Dropdown, Button } from "antd";
import { WELCOME } from "../../../routes";
import OauthPopup from "../../OAuthPopUp";
import { LoginOutlined } from "@ant-design/icons";
import LoginForm from "../LoginForm";
import { useState } from "react";

const SimpleMenu = ({
  initCurrentUser,
  loginLocalUser,
  location = { state: { next: "/" } },
}) => {
  if (location.pathname != WELCOME) return null;

  const [dropdownOpen, setDropdownOpen] = useState(false);

  let oauthLink =
    process.env.NODE_ENV === "development"
      ? `/oauth/login/cern_openid?next=/`
      : `/api/oauth/login/cern_openid?next=/`;

  const menuItems = [
    { key: "home", label: <a href="#home">Home</a> },
    { key: "discover", label: <a href="#discover">What is Cap</a> },
    { key: "explain", label: <a href="#explain">Get Started</a> },
    { key: "integrations", label: <a href="#integrations">Integrations</a> },
    { key: "documentation", label: <a href="#documentation">Documentation</a> },
    {
      key: "login",
      label: <Button type="primary" href={oauthLink}>Login</Button>
    },
  ];

  (process.env.NODE_ENV == "development" || process.env.ENABLE_E2E) &&
    menuItems.unshift({
      key: "localLogin",
      label: (
        <Dropdown
          menu={{
            items: [
              {
                label: <LoginForm loginLocalUser={loginLocalUser} />,
                key: "localLoginForm",
              },
            ],
          }}
          open={dropdownOpen}
          onOpenChange={x => setDropdownOpen(x)}
        >
          <div>
            <LoginOutlined /> Local login
          </div>
        </Dropdown>
      ),
      "data-cy": "localLogin",
    });

  return (
    <Menu theme="dark" selectable={false} mode="horizontal" items={menuItems} />
  );
};

SimpleMenu.propTypes = {
  location: PropTypes.object,
  initCurrentUser: PropTypes.func,
  loginLocalUser: PropTypes.func,
};

export default SimpleMenu;
