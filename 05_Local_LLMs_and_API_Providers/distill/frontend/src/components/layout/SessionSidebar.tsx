import SideNavigation from "@cloudscape-design/components/side-navigation";
import Badge from "@cloudscape-design/components/badge";
import { useEffect, useState } from "react";
import { listSessions } from "../../api/sessions";
import type { SessionMeta } from "../../types";

interface Props {
  activeHref: string;
  onNavigate: (href: string) => void;
}

export default function SessionSidebar({ activeHref, onNavigate }: Props) {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setSessions([])); // Silently degrade — sidebar is non-critical
  }, []);

  // Cap at 20 entries to keep the sidebar scannable
  const sessionItems = sessions.slice(0, 20).map((s) => ({
    type: "link" as const,
    text: s.session_label ?? s.student_name,
    href: `/session/${s.session_id}`,
    info:
      s.mcq_score_pct != null ? (
        <Badge
          color={
            s.mcq_score_pct >= 70
              ? "green"
              : s.mcq_score_pct >= 50
              ? "blue"
              : "red"
          }
        >
          {Math.round(s.mcq_score_pct)}%
        </Badge>
      ) : undefined,
  }));

  return (
    <SideNavigation
      activeHref={activeHref}
      header={{ href: "/", text: "Distill" }}
      items={[
        {
          type: "section",
          text: "Recent Sessions",
          items:
            sessionItems.length > 0
              ? sessionItems
              : [{ type: "link", text: "No sessions yet", href: "#" }],
        },
      ]}
      onFollow={(e) => {
        e.preventDefault();
        onNavigate(e.detail.href);
      }}
    />
  );
}
