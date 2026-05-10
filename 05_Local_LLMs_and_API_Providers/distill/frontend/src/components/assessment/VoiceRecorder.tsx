import { useState, useEffect, useRef } from "react";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Spinner from "@cloudscape-design/components/spinner";
import Alert from "@cloudscape-design/components/alert";
import Textarea from "@cloudscape-design/components/textarea";
import Box from "@cloudscape-design/components/box";
import { useVoiceRecorder } from "../../hooks/useVoiceRecorder";
import { transcribeAudio } from "../../api/transcribe";

interface Props {
  onTranscriptReady: (transcript: string) => void;
  onError: (message: string) => void;
  maxSeconds: number;
}

export default function VoiceRecorder({ onTranscriptReady, onError, maxSeconds }: Props) {
  const recorder = useVoiceRecorder();
  const [transcript, setTranscript] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Start/stop the countdown timer in sync with recorder state
  useEffect(() => {
    if (recorder.state === "recording") {
      timerRef.current = setInterval(() => {
        setElapsed((n) => {
          if (n + 1 >= maxSeconds) {
            recorder.stopRecording();
            return n + 1;
          }
          return n + 1;
        });
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setElapsed(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [recorder.state]);

  // When the blob is ready (state = "transcribing"), call the STT API.
  // onError and onTranscriptReady are included in deps so we never call a stale
  // closure if the parent re-renders and changes these callback references.
  useEffect(() => {
    if (recorder.state === "transcribing" && recorder.audioBlob) {
      transcribeAudio(recorder.audioBlob)
        .then((result) => {
          setTranscript(result.transcript);
          recorder.setReview();
        })
        .catch((err) => {
          onError(err instanceof Error ? err.message : "Transcription failed");
          recorder.reset();
        });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.state, recorder.audioBlob, onError, onTranscriptReady, recorder.setReview, recorder.reset]);

  const formatTime = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60)
      .toString()
      .padStart(2, "0")}`;

  if (recorder.error) {
    return (
      <Alert type="error" header="Microphone unavailable">
        {recorder.error} You can type your answer below instead.
      </Alert>
    );
  }

  return (
    <SpaceBetween size="m">
      {/* Idle state — show record button */}
      {recorder.state === "idle" && (
        <Button iconName="microphone" onClick={recorder.startRecording} variant="primary">
          Start Recording
        </Button>
      )}

      {/* Recording state — animated waveform + timer */}
      {recorder.state === "recording" && (
        <SpaceBetween size="s">
          <Box>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                height: "40px",
              }}
            >
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    width: "6px",
                    borderRadius: "3px",
                    background: "#0972d3",
                    animationName: "waveform",
                    animationDuration: `${0.5 + (i % 4) * 0.15}s`,
                    animationTimingFunction: "ease-in-out",
                    animationIterationCount: "infinite",
                    animationDirection: "alternate",
                    height: `${20 + (i % 5) * 8}px`,
                  }}
                />
              ))}
              <style>{`
                @keyframes waveform {
                  from { transform: scaleY(0.4); }
                  to   { transform: scaleY(1); }
                }
              `}</style>
            </div>
          </Box>
          <SpaceBetween direction="horizontal" size="m" alignItems="center">
            <Box color="text-status-error">
              ● REC {formatTime(elapsed)} / {formatTime(maxSeconds)}
            </Box>
            <Button onClick={recorder.stopRecording} iconName="status-stopped">
              Stop Recording
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      )}

      {/* Transcribing state — spinner */}
      {recorder.state === "transcribing" && (
        <SpaceBetween direction="horizontal" size="xs" alignItems="center">
          <Spinner />
          <Box color="text-body-secondary">Transcribing with Whisper...</Box>
        </SpaceBetween>
      )}

      {/* Review state — editable transcript */}
      {recorder.state === "review" && (
        <SpaceBetween size="s">
          <Alert type="info" header="Review your transcript">
            Edit any transcription errors before submitting.
          </Alert>
          <Textarea
            value={transcript}
            onChange={({ detail }) => setTranscript(detail.value)}
            rows={6}
          />
          <SpaceBetween direction="horizontal" size="s">
            <Button onClick={recorder.reset} iconName="redo">
              Re-record
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                recorder.setSubmitted();
                onTranscriptReady(transcript);
              }}
              disabled={transcript.trim().length < 10}
            >
              Confirm &amp; Submit
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
}
