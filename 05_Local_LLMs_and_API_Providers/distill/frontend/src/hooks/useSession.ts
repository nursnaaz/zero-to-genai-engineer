import { useCallback } from "react";
import { useAppState, useAppDispatch } from "../context/AppContext";
import { analyzeTranscriptStream } from "../api/analyze";
import type { AnalyzePayload } from "../api/analyze";

export function useSession() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  const submitTranscript = useCallback(
    async (transcript: string, studentName: string, sessionLabel?: string) => {
      dispatch({ type: "CLEAR_PROGRESS" });
      dispatch({ type: "SET_ANALYZING", value: true });
      try {
        const payload: AnalyzePayload = {
          transcript,
          student_name: studentName,
          session_label: sessionLabel,
        };
        const result = await analyzeTranscriptStream(payload, (event) => {
          dispatch({ type: "ADD_PROGRESS_STEP", step: event });
        });
        dispatch({ type: "SET_ANALYZE_RESULT", result });
        dispatch({
          type: "ADD_FLASH",
          message: {
            id: crypto.randomUUID(),
            type: "success",
            content: `Session analyzed: "${result.summary.session_title}"`,
            dismissible: true,
            autoDismissMs: 5000,
          },
        });
        return result;
      } catch (err) {
        dispatch({
          type: "ADD_FLASH",
          message: {
            id: crypto.randomUUID(),
            type: "error",
            content:
              err instanceof Error ? err.message : "Analysis failed. Check the server.",
            dismissible: true,
          },
        });
        throw err;
      } finally {
        dispatch({ type: "SET_ANALYZING", value: false });
      }
    },
    [dispatch]
  );

  const resetSession = useCallback(() => {
    dispatch({ type: "RESET" });
  }, [dispatch]);

  return {
    sessionId: state.sessionId,
    analyzeResult: state.analyzeResult,
    studentName: state.studentName,
    isAnalyzing: state.ui.isAnalyzing,
    progressSteps: state.progressSteps,
    submitTranscript,
    resetSession,
  };
}
