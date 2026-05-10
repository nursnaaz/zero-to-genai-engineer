import Badge from "@cloudscape-design/components/badge";
import type { Difficulty } from "../../types";

const COLOR_MAP: Record<Difficulty, "green" | "blue" | "red"> = {
  easy: "green",
  medium: "blue",
  hard: "red",
};

export default function DifficultyBadge({ difficulty }: { difficulty: Difficulty }) {
  return (
    <Badge color={COLOR_MAP[difficulty]}>
      {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
    </Badge>
  );
}
