import React, { createContext, useContext, useReducer, type ReactNode } from "react";
import type { AnalyzeResult, Difficulty, MCQResult, VoiceResult, FlashMessage } from "../types";
import type { ProgressEvent } from "../api/analyze";

export interface ProgressStep extends ProgressEvent {
  completedAt?: number; // epoch ms when the NEXT step arrived (marks this one done)
  startedAt: number;    // epoch ms when this step was received
}

// ── State shape ────────────────────────────────────────────────────────────────

export interface AppState {
  sessionId: string | null;
  studentName: string;
  analyzeResult: AnalyzeResult | null;
  currentQuestionIndex: number;
  currentDifficulty: Difficulty;
  mcqResults: Record<number, MCQResult>;
  voiceResults: Record<number, VoiceResult>;
  progressSteps: ProgressStep[];
  ui: {
    isAnalyzing: boolean;
    isTranscribing: boolean;
    isEvaluating: boolean;
    flashMessages: FlashMessage[];
  };
}

const initialState: AppState = {
  sessionId: null,
  studentName: "Student",
  analyzeResult: null,
  currentQuestionIndex: 0,
  currentDifficulty: "medium",
  mcqResults: {},
  voiceResults: {},
  progressSteps: [],
  ui: {
    isAnalyzing: false,
    isTranscribing: false,
    isEvaluating: false,
    flashMessages: [],
  },
};

// ── Actions ────────────────────────────────────────────────────────────────────

export type AppAction =
  | { type: "SET_STUDENT_NAME"; name: string }
  | { type: "SET_ANALYZING"; value: boolean }
  | { type: "SET_TRANSCRIBING"; value: boolean }
  | { type: "SET_EVALUATING"; value: boolean }
  | { type: "SET_ANALYZE_RESULT"; result: AnalyzeResult }
  | { type: "SET_MCQ_RESULT"; questionId: number; result: MCQResult }
  | { type: "SET_VOICE_RESULT"; questionId: number; result: VoiceResult }
  | { type: "ADVANCE_QUESTION" }
  | { type: "SET_DIFFICULTY"; difficulty: Difficulty }
  | { type: "ADD_FLASH"; message: FlashMessage }
  | { type: "DISMISS_FLASH"; id: string }
  | { type: "ADD_PROGRESS_STEP"; step: ProgressEvent }
  | { type: "CLEAR_PROGRESS" }
  | { type: "RESET" };

// ── Reducer ────────────────────────────────────────────────────────────────────

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_STUDENT_NAME":
      return { ...state, studentName: action.name };

    case "SET_ANALYZING":
      return { ...state, ui: { ...state.ui, isAnalyzing: action.value } };

    case "SET_TRANSCRIBING":
      return { ...state, ui: { ...state.ui, isTranscribing: action.value } };

    case "SET_EVALUATING":
      return { ...state, ui: { ...state.ui, isEvaluating: action.value } };

    case "SET_ANALYZE_RESULT":
      return {
        ...state,
        sessionId: action.result.session_id,
        analyzeResult: action.result,
        currentQuestionIndex: 0,
        currentDifficulty: "medium",
        mcqResults: {},
        voiceResults: {},
      };

    case "SET_MCQ_RESULT":
      return {
        ...state,
        mcqResults: { ...state.mcqResults, [action.questionId]: action.result },
      };

    case "SET_VOICE_RESULT":
      return {
        ...state,
        voiceResults: { ...state.voiceResults, [action.questionId]: action.result },
      };

    case "ADVANCE_QUESTION":
      return { ...state, currentQuestionIndex: state.currentQuestionIndex + 1 };

    case "SET_DIFFICULTY":
      return { ...state, currentDifficulty: action.difficulty };

    case "ADD_FLASH":
      return {
        ...state,
        ui: {
          ...state.ui,
          flashMessages: [...state.ui.flashMessages, action.message],
        },
      };

    case "DISMISS_FLASH":
      return {
        ...state,
        ui: {
          ...state.ui,
          flashMessages: state.ui.flashMessages.filter((m) => m.id !== action.id),
        },
      };

    case "ADD_PROGRESS_STEP": {
      const now = Date.now();
      // Mark the previous step as completed
      const prev = state.progressSteps.map((s, i) =>
        i === state.progressSteps.length - 1 ? { ...s, completedAt: now } : s
      );
      return {
        ...state,
        progressSteps: [...prev, { ...action.step, startedAt: now }],
      };
    }

    case "CLEAR_PROGRESS":
      return { ...state, progressSteps: [] };

    case "RESET":
      return structuredClone(initialState);

    default:
      return state;
  }
}

// ── Context ────────────────────────────────────────────────────────────────────

const StateContext = createContext<AppState | null>(null);
const DispatchContext = createContext<React.Dispatch<AppAction> | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  return (
    <StateContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>{children}</DispatchContext.Provider>
    </StateContext.Provider>
  );
}

export function useAppState(): AppState {
  const ctx = useContext(StateContext);
  if (!ctx) throw new Error("useAppState must be used within AppProvider");
  return ctx;
}

export function useAppDispatch(): React.Dispatch<AppAction> {
  const ctx = useContext(DispatchContext);
  if (!ctx) throw new Error("useAppDispatch must be used within AppProvider");
  return ctx;
}
