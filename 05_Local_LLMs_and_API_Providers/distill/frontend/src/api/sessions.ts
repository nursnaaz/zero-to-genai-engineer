import { apiClient } from "../config/api";
import type { SessionMeta, SessionResults } from "../types";

export async function listSessions(): Promise<SessionMeta[]> {
  const { data } = await apiClient.get<{ sessions: SessionMeta[] }>("/api/sessions");
  return data.sessions;
}

export interface SessionDetail {
  session: SessionMeta;
  results: SessionResults | null;
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const { data } = await apiClient.get<SessionDetail>(`/api/session/${sessionId}`);
  return data;
}

export interface UIConfigResponse {
  brand_name: string;
  brand_tagline: string;
  features: Record<string, boolean>;
  assessment_config: Record<string, unknown>;
}

export async function getUIConfig(): Promise<UIConfigResponse> {
  const { data } = await apiClient.get<UIConfigResponse>("/api/config/ui");
  return data;
}
