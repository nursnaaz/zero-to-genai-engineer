import { useState } from "react";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import SpaceBetween from "@cloudscape-design/components/space-between";
import RadioGroup from "@cloudscape-design/components/radio-group";
import Button from "@cloudscape-design/components/button";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import Spinner from "@cloudscape-design/components/spinner";
import { evaluateMCQ } from "../../api/evaluate";
import type { Question, MCQResult, AnswerKey } from "../../types";
import DifficultyBadge from "./DifficultyBadge";

interface Props {
  question: Question;
  sessionId: string;
  onAnswered: (result: MCQResult) => void;
  onNext: () => void;
}

export default function MCQQuestion({ question, sessionId, onAnswered, onNext }: Props) {
  const [selected, setSelected] = useState<AnswerKey | null>(null);
  const [result, setResult] = useState<MCQResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hintLevel, setHintLevel] = useState(0);
  const [hintVisible, setHintVisible] = useState(false);

  const handleSubmit = async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      const r = await evaluateMCQ({
        session_id: sessionId,
        question_id: question.id,
        selected_answer: selected,
        hint_level_used: hintLevel,
      });
      setResult(r);
      onAnswered(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleHint = () => {
    setHintLevel((prev) => Math.min(prev + 1, 3));
    setHintVisible(true);
  };

  const options = (question.options ?? []).map((o) => ({
    value: o.key,
    label: `${o.key}. ${o.text}`,
  }));

  return (
    <Container
      header={
        <Header
          variant="h2"
          description={
            <SpaceBetween direction="horizontal" size="xs">
              <Box color="text-body-secondary">{question.topic}</Box>
              <DifficultyBadge difficulty={question.difficulty} />
            </SpaceBetween>
          }
        >
          {question.question}
        </Header>
      }
    >
      <SpaceBetween size="m">
        {error && <Alert type="error">{error}</Alert>}

        <RadioGroup
          value={selected ?? ""}
          onChange={({ detail }) => {
            if (!result) setSelected(detail.value as AnswerKey);
          }}
          items={options}
        />

        {/* Hint system — shown while answering, hidden after result */}
        {!result && hintVisible && (
          <Alert type="info" header={`Hint (level ${hintLevel}/3)`}>
            Think about{" "}
            {hintLevel === 1
              ? "the core definition"
              : hintLevel === 2
              ? "how it works in practice"
              : "a real-world example of this concept"}
            .
          </Alert>
        )}

        {/* Post-answer feedback */}
        {result && (
          <Alert
            type={result.is_correct ? "success" : "error"}
            header={
              result.is_correct
                ? "Correct!"
                : `Incorrect — the answer is ${result.correct_answer}`
            }
          >
            {result.explanation}
            {result.hint && !result.is_correct && (
              <Box margin={{ top: "xs" }} color="text-body-secondary">
                Hint: {result.hint}
              </Box>
            )}
          </Alert>
        )}

        <SpaceBetween direction="horizontal" size="s" alignItems="center">
          {!result && !loading && hintLevel < 3 && (
            <Button variant="link" onClick={handleHint} iconName="status-info">
              Need a hint? ({3 - hintLevel} remaining)
            </Button>
          )}
          <Box float="right">
            {!result ? (
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={!selected || loading}
                loading={loading}
              >
                {loading ? <Spinner /> : "Submit Answer"}
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={onNext}
                iconAlign="right"
                iconName="angle-right"
              >
                Next Question
              </Button>
            )}
          </Box>
        </SpaceBetween>
      </SpaceBetween>
    </Container>
  );
}
