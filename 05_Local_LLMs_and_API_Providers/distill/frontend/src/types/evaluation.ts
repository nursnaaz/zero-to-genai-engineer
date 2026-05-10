import type { AnswerKey, Difficulty } from "./assessment";

export interface MCQResult {
  // question_id and selected are NOT in the API response — track them locally
  // from the request payload, not here.
  is_correct: boolean;
  correct_answer: AnswerKey;
  explanation: string;
  next_difficulty: Difficulty;
  hint?: string;
}

export interface DimensionScore {
  key: string;
  label: string;
  score: number;   // 1–5
  weight: number;
}

export interface VoiceResult {
  // question_id and student_answer are NOT in the API response — they are
  // known from the request payload and should be tracked at the call site.
  dimension_scores: DimensionScore[];
  weighted_score: number;         // 1.0–5.0
  narrative_debrief: string;      // 3 paragraphs separated by \n\n
  verdict: string;
  verdict_type: "success" | "info" | "warning" | "error";
  follow_up_question?: string;
  study_recommendations: string[];
}

export interface TopicScore {
  correct: number;
  total: number;
  avg_voice?: number;
}

export interface SessionResults {
  mcq_results: MCQResult[];
  voice_results: VoiceResult[];
  topic_scores: Record<string, TopicScore>;
  overall_mcq_pct: number;
  overall_voice_score: number;
}
