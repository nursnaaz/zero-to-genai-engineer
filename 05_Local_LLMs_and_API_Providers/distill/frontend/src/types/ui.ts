export type FlashType = "success" | "error" | "warning" | "info";

export interface FlashMessage {
  id: string;           // unique key for React list rendering
  type: FlashType;
  content: string;
  dismissible: boolean;
  autoDismissMs?: number;
}

export interface UIConfig {
  brand_name: string;
  brand_tagline: string;
  features: Record<string, boolean>;
  assessment_config: Record<string, unknown>;
}
