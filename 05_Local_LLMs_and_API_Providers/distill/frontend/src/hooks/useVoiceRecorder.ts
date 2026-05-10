import { useState, useRef, useCallback } from "react";

export type RecorderState = "idle" | "recording" | "transcribing" | "review" | "submitted";

export function useVoiceRecorder() {
  const [state, setState] = useState<RecorderState>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      // Request mono 16kHz audio — Whisper's preferred format
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, sampleRate: 16000 },
      });

      // Use webm/opus if supported, fall back to whatever is available
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      chunksRef.current = [];
      const recorder = new MediaRecorder(stream, { mimeType });

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        // Stop all tracks to release microphone
        stream.getTracks().forEach((t) => t.stop());
      };

      mediaRecorderRef.current = recorder;
      recorder.start(250);   // capture in 250ms chunks for smooth waveform
      setState("recording");
    } catch (err) {
      const msg =
        err instanceof Error && err.name === "NotAllowedError"
          ? "Microphone access denied. Enable microphone permissions and try again."
          : "Could not access microphone.";
      setError(msg);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
      setState("transcribing");
    }
  }, []);

  const setReview = useCallback(() => setState("review"), []);
  const setSubmitted = useCallback(() => setState("submitted"), []);

  const reset = useCallback(() => {
    // Stop the recorder before nulling the ref so the onstop handler fires and
    // releases microphone tracks. Safe to call even if already stopped.
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    setAudioBlob(null);
    setError(null);
    setState("idle");
  }, []);

  return {
    state,
    audioBlob,
    error,
    startRecording,
    stopRecording,
    setReview,
    setSubmitted,
    reset,
  };
}
