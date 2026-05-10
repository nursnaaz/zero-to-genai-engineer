import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import FormField from "@cloudscape-design/components/form-field";
import Textarea from "@cloudscape-design/components/textarea";
import Input from "@cloudscape-design/components/input";
import Button from "@cloudscape-design/components/button";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Alert from "@cloudscape-design/components/alert";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Box from "@cloudscape-design/components/box";
import { useSession } from "../hooks/useSession";
import { useAppDispatch } from "../context/AppContext";
import type { ProgressStep } from "../context/AppContext";

// ── Stage metadata ─────────────────────────────────────────────────────────────

const STAGE_META: Record<string, { icon: string; label: string }> = {
  reading:     { icon: "📄", label: "Reading" },
  splitting:   { icon: "✂️",  label: "Splitting" },
  chunk:       { icon: "🔍", label: "Summarizing" },
  merging:     { icon: "🔗", label: "Merging" },
  summary:     { icon: "📝", label: "Topics & Concepts" },
  concept_map: { icon: "🗺️",  label: "Concept Map" },
  questions:   { icon: "🎯", label: "Quiz Questions" },
  saving:      { icon: "💾", label: "Saving" },
};

function elapsed(ms: number): string {
  const s = Math.floor(ms / 1000);
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
}

// ── Live progress panel ────────────────────────────────────────────────────────

function AnalysisProgress({ steps, startedAt }: { steps: ProgressStep[]; startedAt: number }) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const totalElapsed = Date.now() - startedAt;

  return (
    <div style={{
      background: "#0d1117",
      border: "1px solid #30363d",
      borderRadius: 8,
      padding: "20px 24px",
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      fontSize: 13,
      lineHeight: 1.6,
    }}>
      {/* Header */}
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ color: "#58a6ff", fontWeight: 600, fontSize: 14 }}>
          🧠 Distill is processing your transcript
        </span>
        <span style={{ color: "#8b949e", fontSize: 12 }}>
          {elapsed(totalElapsed)} elapsed
        </span>
      </div>

      {/* Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {steps.map((step, i) => {
          const meta = STAGE_META[step.stage] ?? { icon: "⚙️", label: step.stage };
          const isDone = step.completedAt !== undefined;
          const isActive = !isDone && i === steps.length - 1;
          const stepElapsed = isDone
            ? step.completedAt! - step.startedAt
            : Date.now() - step.startedAt;

          return (
            <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
              {/* Status icon */}
              <div style={{ width: 20, flexShrink: 0, textAlign: "center", marginTop: 1 }}>
                {isDone ? (
                  <span style={{ color: "#3fb950" }}>✓</span>
                ) : (
                  <span style={{
                    display: "inline-block",
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: "#58a6ff",
                    boxShadow: "0 0 8px #58a6ff",
                    animation: "pulse 1.4s ease-in-out infinite",
                    marginTop: 4,
                  }} />
                )}
              </div>

              {/* Content */}
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                  <span style={{
                    color: isDone ? "#8b949e" : isActive ? "#e6edf3" : "#8b949e",
                    fontWeight: isActive ? 600 : 400,
                  }}>
                    {meta.icon} {step.message}
                  </span>
                  <span style={{ color: "#484f58", fontSize: 11, marginLeft: 12, flexShrink: 0 }}>
                    {elapsed(stepElapsed)}
                  </span>
                </div>
                {step.detail && (
                  <div style={{ color: "#484f58", fontSize: 11, marginTop: 1 }}>
                    {step.detail}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Blinking cursor at the end */}
        {steps.length > 0 && (
          <div style={{ color: "#58a6ff", marginTop: 4 }}>
            <span style={{
              display: "inline-block",
              width: 8,
              height: 14,
              background: "#58a6ff",
              animation: "blink 1s step-end infinite",
              verticalAlign: "middle",
            }} />
          </div>
        )}
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.8); }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function InputPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { submitTranscript, isAnalyzing, progressSteps } = useSession();
  const [analysisStartedAt, setAnalysisStartedAt] = useState<number>(Date.now());

  const [transcript, setTranscript] = useState("");
  const [studentName, setStudentName] = useState("Student");
  const [sessionLabel, setSessionLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split(".").pop()?.toLowerCase();

    if (ext === "doc") {
      setError(".doc format is not supported. Open the file in Word and save it as .docx, then upload again.");
      e.target.value = "";
      return;
    }

    if (ext === "docx") {
      try {
        const mammoth = (await import("mammoth")).default;
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        if (result.messages.length > 0) {
          // Non-fatal warnings (e.g. unsupported formatting) — log, don't block
          console.warn("mammoth warnings:", result.messages);
        }
        setTranscript(result.value.trim());
      } catch {
        setError("Could not read the .docx file. Make sure it is a valid Word document.");
      }
      e.target.value = "";
      return;
    }

    // Plain text fallback: .txt, .vtt, .srt
    const reader = new FileReader();
    reader.onload = (evt) => {
      setTranscript((evt.target?.result as string).trim());
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const handleAnalyze = async () => {
    if (transcript.trim().length < 100) {
      setError("Transcript must be at least 100 characters. Paste a real meeting transcript.");
      return;
    }
    setError(null);
    setAnalysisStartedAt(Date.now());
    dispatch({ type: "SET_STUDENT_NAME", name: studentName });

    try {
      await submitTranscript(transcript, studentName, sessionLabel || undefined);
      navigate("/summary");
    } catch {
      setError("Analysis failed. Check that LM Studio server is running and the model is loaded.");
    }
  };

  return (
    <SpaceBetween size="l">
      <Container
        header={
          <Header
            variant="h1"
            description="Paste a transcript or upload a file (.txt, .vtt, .docx). Distill extracts key concepts, builds a concept map, and generates an adaptive assessment."
          >
            Upload your class transcript
          </Header>
        }
      >
        <SpaceBetween size="m">
          {error && (
            <Alert type="error" dismissible onDismiss={() => setError(null)}>
              {error}
            </Alert>
          )}

          <ColumnLayout columns={2}>
            <FormField label="Your name" description="Used to personalise your assessment report">
              <Input
                value={studentName}
                onChange={({ detail }) => setStudentName(detail.value)}
                placeholder="e.g. Priya Sharma"
                disabled={isAnalyzing}
              />
            </FormField>

            <FormField label="Session label" description="Optional — helps identify this session later">
              <Input
                value={sessionLabel}
                onChange={({ detail }) => setSessionLabel(detail.value)}
                placeholder="e.g. Module 5 — RAG Basics"
                disabled={isAnalyzing}
              />
            </FormField>
          </ColumnLayout>

          <FormField
            label="Transcript"
            description="Minimum 100 characters. Supports Teams, Zoom, Google Meet, and manual transcripts."
            stretch
          >
            <Textarea
              value={transcript}
              onChange={({ detail }) => setTranscript(detail.value)}
              placeholder="[00:00] Teacher: Today we're going to cover Retrieval Augmented Generation, or RAG..."
              rows={16}
              disabled={isAnalyzing}
            />
          </FormField>

          <SpaceBetween direction="horizontal" size="xs" alignItems="center">
            <Button
              variant="normal"
              onClick={() => fileInputRef.current?.click()}
              disabled={isAnalyzing}
              iconName="upload"
            >
              Upload file (.txt, .vtt, .docx)
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.vtt,.srt,.docx,.doc"
              style={{ display: "none" }}
              onChange={handleFileUpload}
            />
            <Box color="text-body-secondary" fontSize="body-s">
              {transcript.length > 0 ? `${transcript.length} characters` : "No file selected"}
            </Box>
          </SpaceBetween>
        </SpaceBetween>
      </Container>

      {/* Live progress feed — visible only while analyzing */}
      {isAnalyzing && progressSteps.length > 0 && (
        <AnalysisProgress steps={progressSteps} startedAt={analysisStartedAt} />
      )}

      <Box textAlign="right">
        <Button
          variant="primary"
          onClick={handleAnalyze}
          disabled={isAnalyzing || transcript.trim().length < 100}
          loading={isAnalyzing && progressSteps.length === 0}
          loadingText="Connecting…"
          iconAlign="right"
          iconName="angle-right"
        >
          {isAnalyzing ? "Analyzing…" : "Analyze Transcript"}
        </Button>
      </Box>
    </SpaceBetween>
  );
}
