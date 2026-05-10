import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import SpaceBetween from "@cloudscape-design/components/space-between";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Box from "@cloudscape-design/components/box";
import Badge from "@cloudscape-design/components/badge";
import Button from "@cloudscape-design/components/button";
import ExpandableSection from "@cloudscape-design/components/expandable-section";
import { useAppState } from "../context/AppContext";
import ConceptMap from "../components/summary/ConceptMap";
import ConfusionZones from "../components/summary/ConfusionZones";

export default function SummaryPage() {
  const state = useAppState();
  const navigate = useNavigate();
  const result = state.analyzeResult;

  // Guard: if no analysis result, redirect to input
  useEffect(() => {
    if (!result) navigate("/");
  }, [result, navigate]);

  if (!result) return null;

  const { summary, concept_map } = result;

  return (
    <SpaceBetween size="l">
      {/* Header stats */}
      <ColumnLayout columns={3} borders="vertical">
        <Box textAlign="center">
          <Box variant="awsui-key-label">Topics Covered</Box>
          <Box fontSize="display-l" fontWeight="bold" color="text-status-info">
            {summary.topics_covered.length}
          </Box>
        </Box>
        <Box textAlign="center">
          <Box variant="awsui-key-label">Key Concepts</Box>
          <Box fontSize="display-l" fontWeight="bold" color="text-status-success">
            {summary.key_concepts.length}
          </Box>
        </Box>
        <Box textAlign="center">
          <Box variant="awsui-key-label">Confusion Zones</Box>
          <Box
            fontSize="display-l"
            fontWeight="bold"
            color={summary.confusion_zones.length > 0 ? "text-status-warning" : "text-status-success"}
          >
            {summary.confusion_zones.length}
          </Box>
        </Box>
      </ColumnLayout>

      {/* Session title */}
      <Container
        header={<Header variant="h2">{summary.session_title}</Header>}
      >
        <SpaceBetween size="m">
          {/* Topics as badges */}
          <Box>
            <Box variant="awsui-key-label" margin={{ bottom: "xs" }}>Topics</Box>
            <SpaceBetween direction="horizontal" size="xs">
              {summary.topics_covered.map((topic) => (
                <Badge key={topic} color="blue">{topic}</Badge>
              ))}
            </SpaceBetween>
          </Box>

          {/* Teacher insight */}
          <Box>
            <Box variant="awsui-key-label" margin={{ bottom: "xs" }}>Teaching focus</Box>
            <Box color="text-body-secondary">{summary.teacher_insight}</Box>
          </Box>

          {/* Learning objectives */}
          <ExpandableSection headerText={`Learning objectives (${summary.learning_objectives.length})`}>
            <ul style={{ margin: 0, paddingLeft: "1.5rem" }}>
              {summary.learning_objectives.map((obj, i) => (
                <li key={i}><Box variant="p">{obj}</Box></li>
              ))}
            </ul>
          </ExpandableSection>

          {/* Key concepts */}
          <ExpandableSection
            headerText={`Key concepts (${summary.key_concepts.length})`}
            defaultExpanded
          >
            <ColumnLayout columns={2}>
              {summary.key_concepts.map((c) => (
                <Box key={c.concept} padding="s">
                  <Box fontWeight="bold">{c.concept}</Box>
                  <Box color="text-body-secondary" fontSize="body-s">{c.explanation}</Box>
                  <Badge color="grey">{c.topic}</Badge>
                </Box>
              ))}
            </ColumnLayout>
          </ExpandableSection>
        </SpaceBetween>
      </Container>

      {/* Concept Map */}
      <Container header={<Header variant="h2">Concept Map</Header>}>
        <ConceptMap mermaidSyntax={concept_map.mermaid_syntax} />
      </Container>

      {/* Confusion zones */}
      {summary.confusion_zones.length > 0 && (
        <ConfusionZones zones={summary.confusion_zones} />
      )}

      {/* Next step */}
      <Box textAlign="right">
        <Button
          variant="primary"
          onClick={() => navigate("/assessment")}
          iconAlign="right"
          iconName="angle-right"
        >
          Start Assessment
        </Button>
      </Box>
    </SpaceBetween>
  );
}
