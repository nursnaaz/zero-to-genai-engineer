import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Alert from "@cloudscape-design/components/alert";
import Badge from "@cloudscape-design/components/badge";
import Box from "@cloudscape-design/components/box";
import type { ConfusionZone } from "../../types";

// Human-readable labels for each signal type that Distill can detect
const SIGNAL_LABELS: Record<string, string> = {
  student_question: "Students asked",
  teacher_repeated: "Teacher repeated",
  explicit_check: "Comprehension check",
  silence: "Silence/hesitation",
};

export default function ConfusionZones({ zones }: { zones: ConfusionZone[] }) {
  return (
    <Container
      header={
        <Header
          variant="h2"
          description="These moments in the transcript suggested students needed more time or clarification."
        >
          Confusion Zones ({zones.length})
        </Header>
      }
    >
      <SpaceBetween size="s">
        {zones.map((zone, i) => (
          <Alert key={i} type="warning" header={zone.topic}>
            <SpaceBetween size="xs">
              <Box>{zone.description}</Box>
              <SpaceBetween direction="horizontal" size="xs">
                <Badge color="grey">
                  {SIGNAL_LABELS[zone.signal_type] ?? zone.signal_type}
                </Badge>
                {zone.timestamp_approx && (
                  <Badge color="blue">~{zone.timestamp_approx}</Badge>
                )}
              </SpaceBetween>
            </SpaceBetween>
          </Alert>
        ))}
      </SpaceBetween>
    </Container>
  );
}
