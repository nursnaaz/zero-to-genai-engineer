import { useEffect, useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import AppLayout from "@cloudscape-design/components/app-layout";
import TopNavigation from "@cloudscape-design/components/top-navigation";
import SideNavigation from "@cloudscape-design/components/side-navigation";
import Flashbar from "@cloudscape-design/components/flashbar";
import { useAppState, useAppDispatch } from "../../context/AppContext";
import { getUIConfig } from "../../api/sessions";
import type { UIConfig } from "../../types";

export default function AppShell() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const [uiConfig, setUiConfig] = useState<UIConfig | null>(null);
  const [navigationOpen, setNavigationOpen] = useState(false);

  useEffect(() => {
    getUIConfig()
      .then(setUiConfig)
      .catch(() => {
        // Non-fatal: fall back to defaults if backend is unreachable
      });
  }, []);

  const brandName = uiConfig?.brand_name ?? "Distill";
  const brandTagline = uiConfig?.brand_tagline ?? "Pure knowledge, every class";

  // Build Flashbar items from global state, wiring each dismiss to the reducer
  const flashItems = state.ui.flashMessages.map((msg) => ({
    type: msg.type as "success" | "error" | "warning" | "info",
    content: msg.content,
    dismissible: msg.dismissible,
    id: msg.id,
    onDismiss: () => dispatch({ type: "DISMISS_FLASH", id: msg.id }),
  }));

  // Four wizard steps — matches the router children in order
  const navItems = [
    {
      type: "section" as const,
      text: "Session",
      items: [
        { type: "link" as const, text: "1 — Upload Transcript", href: "/" },
        { type: "link" as const, text: "2 — Session Summary", href: "/summary" },
        { type: "link" as const, text: "3 — Assessment", href: "/assessment" },
        { type: "link" as const, text: "4 — Results", href: "/results" },
      ],
    },
    {
      type: "divider" as const,
    },
    {
      type: "section" as const,
      text: "Actions",
      items: [
        {
          type: "link" as const,
          text: "Start new session",
          href: "/",
        },
      ],
    },
  ];

  return (
    <>
      {/*
       * TopNavigation is rendered outside AppLayout so CloudScape can
       * position it at z-index 1000 above the side navigation drawer.
       */}
      <TopNavigation
        identity={{
          href: "/",
          title: brandName,
          logo: undefined,
        }}
        utilities={[
          {
            type: "button",
            text: brandTagline,
            disableUtilityCollapse: false,
          },
        ]}
        i18nStrings={{
          overflowMenuTriggerText: "More",
          overflowMenuTitleText: "All",
        }}
      />

      <AppLayout
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        navigation={
          <SideNavigation
            activeHref={location.pathname}
            header={{ href: "/", text: brandName }}
            items={navItems}
            onFollow={(e) => {
              e.preventDefault();
              navigate(e.detail.href);
            }}
          />
        }
        notifications={<Flashbar items={flashItems} stackItems />}
        content={<Outlet />}
        toolsHide
        contentType="default"
      />
    </>
  );
}
