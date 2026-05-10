import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import SpaceBetween from "@cloudscape-design/components/space-between";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Box from "@cloudscape-design/components/box";
import Button from "@cloudscape-design/components/button";
import Table from "@cloudscape-design/components/table";
import ProgressBar from "@cloudscape-design/components/progress-bar";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import { useAppState } from "../context/AppContext";
import InterviewDebrief from "../components/results/InterviewDebrief";
import WhatsAppExport from "../components/results/WhatsAppExport";

export default function ResultsPage() {
  const state = useAppState();
  const navigate = useNavigate();
  const result = state.analyzeResult;

  useEffect(() => {
    if (!result) navigate("/");
  }, [result, navigate]);

  if (!result) return null;

  // ── Aggregate scores ────────────────────────────────────────────────────────
  const voiceResults = Object.values(state.voiceResults);
  const mcqResults = Object.values(state.mcqResults);
  const totalMCQ = result.questions.filter((q) => q.type === "mcq").length;
  const correctMCQ = mcqResults.filter((r) => r.is_correct).length;
  const mcqPct = totalMCQ > 0 ? Math.round((correctMCQ / totalMCQ) * 100) : 0;
  const avgVoice =
    voiceResults.length > 0
      ? voiceResults.reduce((sum, r) => sum + r.weighted_score, 0) / voiceResults.length
      : 0;

  // ── Per-topic breakdown for the table ──────────────────────────────────────
  const topicMap: Record<string, { correct: number; total: number }> = {};
  result.questions.forEach((q) => {
    if (!topicMap[q.topic]) topicMap[q.topic] = { correct: 0, total: 0 };
    topicMap[q.topic].total += 1;
    if (q.type === "mcq") {
      const r = state.mcqResults[q.id];
      if (r?.is_correct) topicMap[q.topic].correct += 1;
    }
  });
  const topicRows = Object.entries(topicMap).map(([topic, scores]) => ({
    topic,
    correct: scores.correct,
    total: scores.total,
    pct: scores.total > 0 ? Math.round((scores.correct / scores.total) * 100) : 0,
  }));

  // ── Verdict label & colour ─────────────────────────────────────────────────
  const verdictType: "success" | "info" | "warning" | "error" =
    avgVoice >= 4.2 ? "success" : avgVoice >= 3.0 ? "info" : avgVoice >= 2.0 ? "warning" : "error";

  const verdictLabel =
    avgVoice >= 4.2
      ? "Interview ready"
      : avgVoice >= 3.0
      ? "Good — keep going"
      : avgVoice >= 2.0
      ? "Developing"
      : "Needs more practice";

  // ── MCQ colour helper ──────────────────────────────────────────────────────
  const mcqColor = (pct: number) =>
    pct >= 70 ? "text-status-success" : pct >= 50 ? "text-status-warning" : "text-status-error";

  const voiceColor = (score: number) =>
    score >= 3.5 ? "text-status-success" : score >= 2.5 ? "text-status-warning" : "text-status-error";

  return (
    <SpaceBetween size="l">
      {/* ── Score summary ─────────────────────────────────────────────────── */}
      <Container header={<Header variant="h1">Your Results</Header>}>
        <ColumnLayout columns={3} borders="vertical">
          {/* MCQ */}
          <Box textAlign="center">
            <Box variant="awsui-key-label">MCQ Score</Box>
            <Box fontSize="display-l" fontWeight="bold" color={mcqColor(mcqPct)}>
              {mcqPct}%
            </Box>
            <Box color="text-body-secondary">
              {correctMCQ} / {totalMCQ} correct
            </Box>
          </Box>

          {/* AI Interview */}
          <Box textAlign="center">
            <Box variant="awsui-key-label">AI Interview Score</Box>
            <Box fontSize="display-l" fontWeight="bold" color={voiceColor(avgVoice)}>
              {avgVoice.toFixed(1)} / 5.0
            </Box>
            <StatusIndicator type={verdictType}>{verdictLabel}</StatusIndicator>
          </Box>

          {/* Session meta */}
          <Box textAlign="center">
            <Box variant="awsui-key-label">Session</Box>
            <Box fontWeight="bold">{result.summary.session_title}</Box>
            <Box color="text-body-secondary">
              {result.summary.topics_covered.length} topics covered
            </Box>
          </Box>
        </ColumnLayout>
      </Container>

      {/* ── Topic breakdown table ─────────────────────────────────────────── */}
      <Table
        header={<Header variant="h2">Topic Breakdown</Header>}
        columnDefinitions={[
          {
            id: "topic",
            header: "Topic",
            cell: (r) => r.topic,
            width: 220,
          },
          {
            id: "score",
            header: "MCQ Score",
            cell: (r) => (
              <ProgressBar
                value={r.pct}
                label={`${r.correct}/${r.total}`}
                variant="standalone"
                status={r.pct >= 70 ? "success" : r.pct >= 50 ? "in-progress" : "error"}
              />
            ),
          },
          {
            id: "pct",
            header: "%",
            cell: (r) => `${r.pct}%`,
            width: 72,
          },
        ]}
        items={topicRows}
        variant="embedded"
        empty={
          <Box textAlign="center" color="text-body-secondary">
            No MCQ results yet.
          </Box>
        }
      />

      {/* ── AI Interview Debrief ──────────────────────────────────────────── */}
      {voiceResults.length > 0 && (
        <Container
          header={
            <Header
              variant="h2"
              description="Detailed feedback from Dr. Priya, your AI interviewer"
            >
              Interview Debrief
            </Header>
          }
        >
          <SpaceBetween size="m">
            {Object.entries(state.voiceResults).map(([qId, vr], i) => {
              const questionId = Number(qId);
              const question = result.questions.find((q) => q.id === questionId);
              return (
                <InterviewDebrief
                  key={questionId}
                  index={i + 1}
                  question={question?.question ?? ""}
                  result={vr}
                />
              );
            })}
          </SpaceBetween>
        </Container>
      )}

      {/* ── WhatsApp export ───────────────────────────────────────────────── */}
      <WhatsAppExport
        studentName={state.studentName}
        sessionTitle={result.summary.session_title}
        mcqPct={mcqPct}
        voiceScore={avgVoice}
        topics={result.summary.topics_covered}
      />

      {/* ── Action buttons ────────────────────────────────────────────────── */}
      <SpaceBetween direction="horizontal" size="s" alignItems="center">
        <Button onClick={() => navigate("/assessment")} iconName="redo">
          Retake Assessment
        </Button>
        <Button
          variant="primary"
          onClick={() => {
            navigate("/");
            window.location.reload();
          }}
          iconName="add-plus"
        >
          New Transcript
        </Button>
      </SpaceBetween>
    </SpaceBetween>
  );
}
