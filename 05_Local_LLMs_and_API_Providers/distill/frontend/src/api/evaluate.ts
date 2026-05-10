import { apiClient } from "../config/api";
import type { MCQResult, VoiceResult, AnswerKey } from "../types";

export interface MCQEvaluatePayload {
  session_id: string;
  question_id: number;
  selected_answer: AnswerKey;
  time_taken_seconds?: number;
  hint_level_used?: number;
}

export interface VoiceEvaluatePayload {
  session_id: string;
  question_id: number;
  student_answer: string;
  answer_duration_seconds?: number;
  was_voice?: boolean;
}

export async function evaluateMCQ(payload: MCQEvaluatePayload): Promise<MCQResult> {
  const { data } = await apiClient.post<MCQResult>("/api/evaluate/mcq", payload);
  return data;
}

export async function evaluateVoice(payload: VoiceEvaluatePayload): Promise<VoiceResult> {
  const { data } = await apiClient.post<VoiceResult>("/api/evaluate/voice", payload);
  return data;
}
