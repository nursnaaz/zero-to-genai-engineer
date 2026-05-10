import ExpandableSection from "@cloudscape-design/components/expandable-section";
import SpaceBetween from "@cloudscape-design/components/space-between";
import ProgressBar from "@cloudscape-design/components/progress-bar";
import StatusIndicator from "@cloudscape-design/components/status-indicator";
import Alert from "@cloudscape-design/components/alert";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import type { VoiceResult } from "../../types";

interface Props {
  index: number;
  question: string;
  result: VoiceResult;
}

export default function InterviewDebrief({ index, question, result }: Props) {
  // Split the multi-paragraph narrative into individual paragraph elements
  const paragraphs = result.narrative_debrief.split("\n\n").filter(Boolean);

  return (
    <ExpandableSection
      headerText={`Q${index}: ${question.slice(0, 80)}${question.length > 80 ? "…" : ""}`}
      headerActions={
        <StatusIndicator
          type={result.verdict_type as "success" | "info" | "warning" | "error"}
        >
          {result.verdict}
        </StatusIndicator>
      }
    >
      <SpaceBetween size="m">
        {/* Per-dimension score bars in a two-column grid */}
        <ColumnLayout columns={2}>
          {result.dimension_scores.map((dim) => (
            <Box key={dim.key}>
              <Box fontSize="body-s" color="text-body-secondary">
                {dim.label}
              </Box>
              <ProgressBar
                value={(dim.score / 5) * 100}
                label={`${dim.score}/5`}
                variant="standalone"
                status={
                  dim.score >= 4
                    ? "success"
                    : dim.score >= 3
                    ? "in-progress"
                    : "error"
                }
              />
            </Box>
          ))}
        </ColumnLayout>

        {/* Weighted overall score */}
        <Box>
          <Box fontWeight="bold">
            Overall: {result.weighted_score.toFixed(1)} / 5.0
          </Box>
        </Box>

        {/* Dr. Priya narrative debrief — one Box per paragraph */}
        <SpaceBetween size="s">
          {paragraphs.map((para, i) => (
            <Box key={i} variant="p">
              {para}
            </Box>
          ))}
        </SpaceBetween>

        {/* Optional AI-generated follow-up question */}
        {result.follow_up_question && (
          <Alert type="info" header="Follow-up to think about">
            {result.follow_up_question}
          </Alert>
        )}

        {/* Ordered list of study recommendations */}
        {result.study_recommendations.length > 0 && (
          <Box>
            <Box fontWeight="bold" margin={{ bottom: "xs" }}>
              Study recommendations:
            </Box>
            <ol style={{ margin: 0, paddingLeft: "1.5rem" }}>
              {result.study_recommendations.map((rec, i) => (
                <li key={i}>
                  <Box variant="p">{rec}</Box>
                </li>
              ))}
            </ol>
          </Box>
        )}
      </SpaceBetween>
    </ExpandableSection>
  );
}
