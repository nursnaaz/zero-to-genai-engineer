import { apiClient } from "../config/api";
import type { AnalyzeResult } from "../types";

export interface AnalyzePayload {
  transcript: string;
  student_name: string;
  session_label?: string;
}

export interface ProgressEvent {
  stage: string;
  message: string;
  detail?: string;
  chunk?: number;
  total_chunks?: number;
}

export async function analyzeTranscript(payload: AnalyzePayload): Promise<AnalyzeResult> {
  const { data } = await apiClient.post<AnalyzeResult>("/api/analyze", payload);
  return data;
}

/**
 * Streams progress events from /api/analyze/stream using fetch + ReadableStream.
 * Calls onProgress for each stage event, resolves with the final AnalyzeResult.
 */
export async function analyzeTranscriptStream(
  payload: AnalyzePayload,
  onProgress: (event: ProgressEvent) => void,
): Promise<AnalyzeResult> {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000";
  const response = await fetch(`${baseUrl}/api/analyze/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Server error ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      for (const line of part.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        const event = JSON.parse(line.slice(6)) as ProgressEvent & { result?: AnalyzeResult };
        if (event.stage === "done" && event.result) return event.result;
        if (event.stage === "error") throw new Error(event.message);
        onProgress(event);
      }
    }
  }

  throw new Error("Stream ended without a result.");
}
