import { useState, useCallback } from "react";
import type { Difficulty } from "../types";

interface TopicDifficulties {
  [topic: string]: Difficulty;
}

const NEXT_DIFFICULTY: Record<Difficulty, Record<"correct" | "wrong", Difficulty>> = {
  easy:   { correct: "medium", wrong: "easy" },
  medium: { correct: "hard",   wrong: "easy" },
  hard:   { correct: "hard",   wrong: "medium" },
};

export function useAdaptiveDifficulty(initial: Difficulty = "medium") {
  const [overallDifficulty, setOverallDifficulty] = useState<Difficulty>(initial);
  const [topicDifficulties, setTopicDifficulties] = useState<TopicDifficulties>({});
  const [consecutiveCorrect, setConsecutiveCorrect] = useState(0);
  const [consecutiveWrong, setConsecutiveWrong] = useState(0);

  const currentDifficulty = useCallback(
    (topic: string): Difficulty => topicDifficulties[topic] ?? overallDifficulty,
    [topicDifficulties, overallDifficulty]
  );

  const updateAfterAnswer = useCallback(
    (topic: string, isCorrect: boolean, nextDifficultyFromAPI?: Difficulty) => {
      // Trust the server's adaptive decision if provided
      const next =
        nextDifficultyFromAPI ??
        NEXT_DIFFICULTY[overallDifficulty][isCorrect ? "correct" : "wrong"];

      setTopicDifficulties((prev) => ({ ...prev, [topic]: next }));
      setOverallDifficulty(next);

      if (isCorrect) {
        setConsecutiveCorrect((n) => n + 1);
        setConsecutiveWrong(0);
      } else {
        setConsecutiveWrong((n) => n + 1);
        setConsecutiveCorrect(0);
      }
    },
    [overallDifficulty]
  );

  return {
    overallDifficulty,
    topicDifficulties,
    currentDifficulty,
    updateAfterAnswer,
    consecutiveCorrect,
    consecutiveWrong,
  };
}
