export interface SessionMeta {
  session_id: string;
  student_name: string;
  session_label?: string;
  created_at: string;     // ISO datetime string
  mcq_score_pct?: number;
  overall_verdict?: string;
  topics_covered: string[];
}
