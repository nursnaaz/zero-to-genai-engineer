export type Difficulty = "easy" | "medium" | "hard";
export type BloomLevel = "remember" | "understand" | "apply" | "analyze" | "evaluate";
export type QuestionType = "mcq" | "teach_it_back";
export type AnswerKey = "A" | "B" | "C" | "D";

export interface MCQOption {
  key: AnswerKey;
  text: string;
}

export interface Question {
  id: number;
  type: QuestionType;
  topic: string;
  difficulty: Difficulty;
  bloom_level?: BloomLevel;
  question: string;
  options?: MCQOption[];          // MCQ only
  correct_answer?: AnswerKey;     // MCQ only
  explanation?: string;           // MCQ only
  evaluation_rubric?: string;     // teach_it_back only
}

export interface KeyConcept {
  concept: string;
  explanation: string;
  topic: string;
}

export interface ConfusionZone {
  topic: string;
  signal_type: "student_question" | "teacher_repeated" | "explicit_check" | "silence";
  description: string;
  timestamp_approx?: string;
}

export interface SummaryData {
  session_title: string;
  topics_covered: string[];
  key_concepts: KeyConcept[];
  learning_objectives: string[];
  teacher_insight: string;
  confusion_zones: ConfusionZone[];
}

export interface ConceptMap {
  mermaid_syntax: string;
  nodes: string[];
  edges: Array<{ from: string; to: string; label: string }>;
}

export interface AnalyzeResult {
  session_id: string;
  summary: SummaryData;
  questions: Question[];
  concept_map: ConceptMap;
}
