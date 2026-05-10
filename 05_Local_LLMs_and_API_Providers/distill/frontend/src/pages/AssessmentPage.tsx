import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Container from "@cloudscape-design/components/container";
import SpaceBetween from "@cloudscape-design/components/space-between";
import ProgressBar from "@cloudscape-design/components/progress-bar";
import Badge from "@cloudscape-design/components/badge";
import { useAppState, useAppDispatch } from "../context/AppContext";
import { useAdaptiveDifficulty } from "../hooks/useAdaptiveDifficulty";
import MCQQuestion from "../components/assessment/MCQQuestion";
import TeachItBack from "../components/assessment/TeachItBack";

const DIFFICULTY_COLORS: Record<string, "blue" | "green" | "red"> = {
  easy: "green",
  medium: "blue",
  hard: "red",
};

export default function AssessmentPage() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  // useAdaptiveDifficulty is consumed for side-effects / future use; updateAfterAnswer
  // is kept in scope so the hook's internal state stays consistent across renders.
  const { updateAfterAnswer } = useAdaptiveDifficulty(state.currentDifficulty);
  const result = state.analyzeResult;

  useEffect(() => {
    if (!result) navigate("/");
  }, [result, navigate]);

  const questions = result?.questions ?? [];
  const currentIndex = state.currentQuestionIndex;
  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;
  // Show (index+1)/total so question 1 renders ~12% instead of an empty bar
  const progress = Math.round(((currentIndex + 1) / (questions.length || 1)) * 100);

  // Navigate to results when all questions are answered — must be in useEffect
  // to avoid calling a navigation side-effect during render (React Strict Mode violation).
  useEffect(() => {
    if (result && !currentQuestion) navigate("/results");
  }, [result, currentQuestion, navigate]);

  if (!result || !currentQuestion) return null;

  const handleAdvance = () => {
    if (isLastQuestion) {
      navigate("/results");
    } else {
      dispatch({ type: "ADVANCE_QUESTION" });
    }
  };

  return (
    <SpaceBetween size="l">
      {/* Progress indicator */}
      <Container>
        <SpaceBetween size="s">
          <ProgressBar
            value={progress}
            label={`Question ${currentIndex + 1} of ${questions.length}`}
            description={`${questions.length - currentIndex - 1} remaining`}
          />
          <SpaceBetween direction="horizontal" size="xs">
            <Badge color={currentQuestion.type === "mcq" ? "blue" : "green"}>
              {currentQuestion.type === "mcq" ? "Multiple Choice" : "Teach It Back"}
            </Badge>
            <Badge color={DIFFICULTY_COLORS[currentQuestion.difficulty] ?? "blue"}>
              {currentQuestion.difficulty.charAt(0).toUpperCase() + currentQuestion.difficulty.slice(1)}
            </Badge>
            {currentQuestion.bloom_level && (
              <Badge color="grey">
                Bloom: {currentQuestion.bloom_level}
              </Badge>
            )}
          </SpaceBetween>
        </SpaceBetween>
      </Container>

      {/* Question content — branch on type */}
      {currentQuestion.type === "mcq" ? (
        <MCQQuestion
          key={currentQuestion.id}
          question={currentQuestion}
          sessionId={state.sessionId!}
          onAnswered={(mcqResult) => {
            dispatch({ type: "SET_MCQ_RESULT", questionId: currentQuestion.id, result: mcqResult });
            // Pass topic + correctness so the adaptive difficulty hook updates accurately
            dispatch({ type: "SET_DIFFICULTY", difficulty: mcqResult.next_difficulty as "easy" | "medium" | "hard" });
            updateAfterAnswer(currentQuestion.topic, mcqResult.is_correct, mcqResult.next_difficulty as "easy" | "medium" | "hard");
          }}
          onNext={handleAdvance}
        />
      ) : (
        <TeachItBack
          key={currentQuestion.id}
          question={currentQuestion}
          sessionId={state.sessionId!}
          onAnswered={(result) => {
            dispatch({ type: "SET_VOICE_RESULT", questionId: currentQuestion.id, result });
          }}
          onNext={handleAdvance}
        />
      )}
    </SpaceBetween>
  );
}
