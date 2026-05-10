import { apiClient } from "../config/api";

export interface TranscribeResult {
  transcript: string;
  duration_seconds?: number;
  language_detected?: string;
}

export async function transcribeAudio(audioBlob: Blob, filename = "recording.webm"): Promise<TranscribeResult> {
  const form = new FormData();
  form.append("audio", audioBlob, filename);

  const { data } = await apiClient.post<TranscribeResult>("/api/transcribe", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
