from __future__ import annotations
"""Central configuration loader for Distill.

Reads config.yaml from the project root. All settings are accessed through
the get_config() singleton — never read files or env vars directly elsewhere.
"""

import os
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()

# ── Nested config dataclasses ──────────────────────────────────────────────────

@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    keep_alive: str = "5m"

@dataclass
class LMStudioConfig:
    base_url: str = "http://localhost:1234/v1"
    api_key: str = "lm-studio"

@dataclass
class OpenAIConfig:
    base_url: str = "https://api.openai.com/v1"
    organization: str | None = None

@dataclass
class AnthropicConfig:
    base_url: str = "https://api.anthropic.com"
    api_version: str = "2023-06-01"

@dataclass
class GeminiConfig:
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"

@dataclass
class LangChainConfig:
    backend: str = "ollama"
    tracing_enabled: bool = False
    tracing_project: str = "distill"

@dataclass
class LLMConfig:
    provider: str = "ollama"
    model: str = "gemma3:9b"
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout_seconds: int = 120
    retry_attempts: int = 3
    retry_delay_seconds: int = 2
    chunk_size_chars: int = 20000    # each map-reduce chunk fed to the LLM
    chunk_overlap_chars: int = 500   # overlap between adjacent chunks to avoid losing context at boundaries
    api_key: str | None = None  # resolved from env vars
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    lmstudio: LMStudioConfig = field(default_factory=LMStudioConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    langchain: LangChainConfig = field(default_factory=LangChainConfig)

@dataclass
class WhisperLocalConfig:
    model_size: str = "medium"
    device: str = "cpu"
    compute_type: str = "float32"
    download_on_startup: bool = True

@dataclass
class OpenAIWhisperConfig:
    model: str = "whisper-1"

@dataclass
class AWSTranscribeConfig:
    region: str = "us-east-1"
    s3_bucket: str | None = None

@dataclass
class GoogleSTTConfig:
    credentials_path: str | None = None

@dataclass
class STTConfig:
    provider: str = "whisper_local"
    language: str = "en"
    whisper_local: WhisperLocalConfig = field(default_factory=WhisperLocalConfig)
    openai_whisper: OpenAIWhisperConfig = field(default_factory=OpenAIWhisperConfig)
    aws_transcribe: AWSTranscribeConfig = field(default_factory=AWSTranscribeConfig)
    google_stt: GoogleSTTConfig = field(default_factory=GoogleSTTConfig)

@dataclass
class MCQConfig:
    count: int = 5
    difficulty_distribution: dict[str, float] = field(
        default_factory=lambda: {"easy": 0.30, "medium": 0.50, "hard": 0.20}
    )
    show_hints: bool = True
    hint_levels: int = 3
    show_explanation_after_answer: bool = True
    time_limit_seconds: int | None = None

@dataclass
class TeachItBackConfig:
    count: int = 3
    min_answer_words: int = 20
    max_recording_seconds: int = 120
    allow_retake: bool = True
    voice_enabled: bool = True
    text_fallback: bool = True

@dataclass
class BloomConfig:
    enabled: bool = True
    distribution: dict[str, float] = field(
        default_factory=lambda: {
            "remember": 0.20, "understand": 0.30,
            "apply": 0.30, "analyze": 0.10, "evaluate": 0.10,
        }
    )

@dataclass
class AdaptiveEngineConfig:
    enabled: bool = True
    initial_difficulty: str = "medium"
    increase_after_consecutive_correct: int = 2
    decrease_after_consecutive_wrong: int = 1
    per_topic_tracking: bool = True

@dataclass
class AssessmentConfig:
    mcq: MCQConfig = field(default_factory=MCQConfig)
    teach_it_back: TeachItBackConfig = field(default_factory=TeachItBackConfig)
    bloom_taxonomy: BloomConfig = field(default_factory=BloomConfig)
    adaptive_engine: AdaptiveEngineConfig = field(default_factory=AdaptiveEngineConfig)

@dataclass
class InterviewerConfig:
    name: str = "Dr. Priya"
    persona: str = ""
    style: str = ""
    domain: str = ""

@dataclass
class ScoreDimensionConfig:
    key: str = ""
    label: str = ""
    weight: float = 0.0
    description: str = ""

@dataclass
class VerdictConfig:
    label: str = ""
    min_weighted_score: float = 0.0
    cloudscape_type: str = "info"

@dataclass
class EvalOutputConfig:
    debrief_paragraph_count: int = 3
    quote_student_answer: bool = True
    include_follow_up_question: bool = True
    include_study_recommendations: bool = True
    max_recommendations: int = 3

@dataclass
class EvaluationConfig:
    interviewer: InterviewerConfig = field(default_factory=InterviewerConfig)
    score_dimensions: list[ScoreDimensionConfig] = field(default_factory=list)
    verdicts: list[VerdictConfig] = field(default_factory=list)
    output: EvalOutputConfig = field(default_factory=EvalOutputConfig)

@dataclass
class ConceptMapConfig:
    renderer: str = "mermaid"
    direction: str = "TD"
    color_by_performance: bool = True
    show_dependencies: bool = True
    max_nodes: int = 20

@dataclass
class SessionConfig:
    storage: str = "memory"
    sqlite_path: str = "./data/sessions.db"
    database_url: str | None = None
    max_sessions_in_memory: int = 100

@dataclass
class PromptsConfig:
    directory: str = "./prompts"
    templates: dict[str, str] = field(
        default_factory=lambda: {
            "summary": "summary_system.j2",
            "questions": "questions_system.j2",
            "concept_map": "concept_map_system.j2",
            "evaluate_mcq": "evaluate_mcq_system.j2",
            "evaluate_voice": "evaluate_voice_system.j2",
            "confusion_map": "confusion_map_system.j2",
        }
    )

@dataclass
class WhatsAppExportConfig:
    enabled: bool = True
    include_score: bool = True
    include_verdict: bool = True
    include_weak_areas: bool = True
    include_study_tip: bool = True
    footer_text: str = "Generated by Distill · Inceptez"

@dataclass
class ExportConfig:
    whatsapp: WhatsAppExportConfig = field(default_factory=WhatsAppExportConfig)
    anki_enabled: bool = True
    pdf_enabled: bool = False

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    max_upload_size_mb: int = 50

@dataclass
class AppConfig:
    app_name: str = "Distill"
    version: str = "0.1.0"
    brand_name: str = "Distill"
    brand_tagline: str = "Pure knowledge, every class"
    debug: bool = False
    log_level: str = "INFO"
    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    speech_to_text: STTConfig = field(default_factory=STTConfig)
    assessment: AssessmentConfig = field(default_factory=AssessmentConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    concept_map: ConceptMapConfig = field(default_factory=ConceptMapConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    ui: dict[str, Any] = field(default_factory=dict)


# ── Loader ─────────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _resolve_api_key(config: AppConfig) -> None:
    """Resolve LLM API key from env vars (provider-specific key takes priority)."""
    provider = config.llm.provider.lower()
    key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
    }
    env_var = key_map.get(provider, "DISTILL_LLM_API_KEY")
    config.llm.api_key = (
        os.environ.get(env_var)
        or os.environ.get("DISTILL_LLM_API_KEY")
    )


def _build_config(raw: dict[str, Any]) -> AppConfig:
    """Map the raw YAML dict to the AppConfig dataclass hierarchy."""
    cfg = AppConfig()
    app = raw.get("app", {})
    cfg.app_name = app.get("name", cfg.app_name)
    cfg.version = app.get("version", cfg.version)
    cfg.brand_name = app.get("brand_name", cfg.brand_name)
    cfg.brand_tagline = app.get("brand_tagline", cfg.brand_tagline)
    cfg.debug = app.get("debug", cfg.debug)
    cfg.log_level = app.get("log_level", cfg.log_level)

    # Server
    srv = raw.get("server", {})
    cfg.server.host = srv.get("host", cfg.server.host)
    cfg.server.port = srv.get("port", cfg.server.port)
    cfg.server.cors_origins = srv.get("cors_origins", cfg.server.cors_origins)
    cfg.server.max_upload_size_mb = srv.get("max_upload_size_mb", cfg.server.max_upload_size_mb)

    # LLM
    llm = raw.get("llm", {})
    cfg.llm.provider = os.environ.get("DISTILL_LLM_PROVIDER", llm.get("provider", cfg.llm.provider))
    cfg.llm.model = llm.get("model", cfg.llm.model)
    cfg.llm.temperature = llm.get("temperature", cfg.llm.temperature)
    cfg.llm.max_tokens = llm.get("max_tokens", cfg.llm.max_tokens)
    cfg.llm.timeout_seconds = llm.get("timeout_seconds", cfg.llm.timeout_seconds)
    cfg.llm.retry_attempts = llm.get("retry_attempts", cfg.llm.retry_attempts)
    cfg.llm.retry_delay_seconds = llm.get("retry_delay_seconds", cfg.llm.retry_delay_seconds)
    cfg.llm.chunk_size_chars = llm.get("chunk_size_chars", cfg.llm.chunk_size_chars)
    cfg.llm.chunk_overlap_chars = llm.get("chunk_overlap_chars", cfg.llm.chunk_overlap_chars)

    if "ollama" in llm:
        ol = llm["ollama"]
        cfg.llm.ollama.base_url = ol.get("base_url", cfg.llm.ollama.base_url)
        cfg.llm.ollama.keep_alive = ol.get("keep_alive", cfg.llm.ollama.keep_alive)
    if "lmstudio" in llm:
        ls = llm["lmstudio"]
        cfg.llm.lmstudio.base_url = ls.get("base_url", cfg.llm.lmstudio.base_url)
        cfg.llm.lmstudio.api_key = ls.get("api_key", cfg.llm.lmstudio.api_key)
    if "openai" in llm:
        oa = llm["openai"]
        cfg.llm.openai.base_url = oa.get("base_url", cfg.llm.openai.base_url)
        cfg.llm.openai.organization = oa.get("organization")
    if "anthropic" in llm:
        an = llm["anthropic"]
        cfg.llm.anthropic.base_url = an.get("base_url", cfg.llm.anthropic.base_url)
        cfg.llm.anthropic.api_version = an.get("api_version", cfg.llm.anthropic.api_version)
    if "gemini" in llm:
        cfg.llm.gemini.base_url = llm["gemini"].get("base_url", cfg.llm.gemini.base_url)
    if "langchain" in llm:
        lc = llm["langchain"]
        cfg.llm.langchain.backend = lc.get("backend", cfg.llm.langchain.backend)
        cfg.llm.langchain.tracing_enabled = lc.get("tracing_enabled", cfg.llm.langchain.tracing_enabled)
        cfg.llm.langchain.tracing_project = lc.get("tracing_project", cfg.llm.langchain.tracing_project)

    # STT
    stt = raw.get("speech_to_text", {})
    cfg.speech_to_text.provider = stt.get("provider", cfg.speech_to_text.provider)
    cfg.speech_to_text.language = stt.get("language", cfg.speech_to_text.language)
    if "whisper_local" in stt:
        wl = stt["whisper_local"]
        cfg.speech_to_text.whisper_local.model_size = wl.get("model_size", "medium")
        cfg.speech_to_text.whisper_local.device = wl.get("device", "cpu")
        cfg.speech_to_text.whisper_local.compute_type = wl.get("compute_type", "float32")
        cfg.speech_to_text.whisper_local.download_on_startup = wl.get("download_on_startup", True)

    # Assessment
    asmt = raw.get("assessment", {})
    if "mcq" in asmt:
        m = asmt["mcq"]
        cfg.assessment.mcq.count = m.get("count", cfg.assessment.mcq.count)
        cfg.assessment.mcq.difficulty_distribution = m.get(
            "difficulty_distribution", cfg.assessment.mcq.difficulty_distribution
        )
        cfg.assessment.mcq.show_hints = m.get("show_hints", True)
        cfg.assessment.mcq.hint_levels = m.get("hint_levels", 3)
        cfg.assessment.mcq.show_explanation_after_answer = m.get("show_explanation_after_answer", True)
        cfg.assessment.mcq.time_limit_seconds = m.get("time_limit_seconds")
    if "teach_it_back" in asmt:
        t = asmt["teach_it_back"]
        cfg.assessment.teach_it_back.count = t.get("count", cfg.assessment.teach_it_back.count)
        cfg.assessment.teach_it_back.min_answer_words = t.get("min_answer_words", 20)
        cfg.assessment.teach_it_back.max_recording_seconds = t.get("max_recording_seconds", 120)
        cfg.assessment.teach_it_back.voice_enabled = t.get("voice_enabled", True)
        cfg.assessment.teach_it_back.text_fallback = t.get("text_fallback", True)
    if "bloom_taxonomy" in asmt:
        b = asmt["bloom_taxonomy"]
        cfg.assessment.bloom_taxonomy.enabled = b.get("enabled", True)
        cfg.assessment.bloom_taxonomy.distribution = b.get(
            "distribution", cfg.assessment.bloom_taxonomy.distribution
        )
    if "adaptive_engine" in asmt:
        ae = asmt["adaptive_engine"]
        cfg.assessment.adaptive_engine.enabled = ae.get("enabled", True)
        cfg.assessment.adaptive_engine.initial_difficulty = ae.get("initial_difficulty", "medium")
        cfg.assessment.adaptive_engine.increase_after_consecutive_correct = ae.get(
            "increase_after_consecutive_correct", 2
        )
        cfg.assessment.adaptive_engine.decrease_after_consecutive_wrong = ae.get(
            "decrease_after_consecutive_wrong", 1
        )

    # Evaluation
    ev = raw.get("evaluation", {})
    if "interviewer" in ev:
        i = ev["interviewer"]
        cfg.evaluation.interviewer.name = i.get("name", "Dr. Priya")
        cfg.evaluation.interviewer.persona = i.get("persona", "")
        cfg.evaluation.interviewer.style = i.get("style", "")
        cfg.evaluation.interviewer.domain = i.get("domain", "")
    if "score_dimensions" in ev:
        cfg.evaluation.score_dimensions = [
            ScoreDimensionConfig(**d) for d in ev["score_dimensions"]
        ]
    if "verdicts" in ev:
        cfg.evaluation.verdicts = [VerdictConfig(**v) for v in ev["verdicts"]]
    if "output" in ev:
        o = ev["output"]
        cfg.evaluation.output.debrief_paragraph_count = o.get("debrief_paragraph_count", 3)
        cfg.evaluation.output.quote_student_answer = o.get("quote_student_answer", True)
        cfg.evaluation.output.include_follow_up_question = o.get("include_follow_up_question", True)
        cfg.evaluation.output.include_study_recommendations = o.get("include_study_recommendations", True)
        cfg.evaluation.output.max_recommendations = o.get("max_recommendations", 3)

    # Concept map
    cm = raw.get("concept_map", {})
    cfg.concept_map.renderer = cm.get("renderer", "mermaid")
    cfg.concept_map.direction = cm.get("direction", "TD")
    cfg.concept_map.max_nodes = cm.get("max_nodes", 20)
    cfg.concept_map.color_by_performance = cm.get("color_by_performance", True)

    # Session
    sess = raw.get("session", {})
    cfg.session.storage = sess.get("storage", "memory")
    cfg.session.sqlite_path = sess.get("sqlite_path", "./data/sessions.db")
    cfg.session.max_sessions_in_memory = sess.get("max_sessions_in_memory", 100)

    # Prompts
    pr = raw.get("prompts", {})
    cfg.prompts.directory = pr.get("directory", "./prompts")
    cfg.prompts.templates = pr.get("templates", cfg.prompts.templates)

    # Export
    exp = raw.get("export", {})
    if "whatsapp" in exp:
        wa = exp["whatsapp"]
        cfg.export.whatsapp.enabled = wa.get("enabled", True)
        cfg.export.whatsapp.footer_text = wa.get("footer_text", cfg.export.whatsapp.footer_text)
    if "anki" in exp:
        cfg.export.anki_enabled = exp["anki"].get("enabled", True)
    if "pdf" in exp:
        cfg.export.pdf_enabled = exp["pdf"].get("enabled", False)

    # UI (store raw for frontend config endpoint)
    cfg.ui = raw.get("ui", {})

    _resolve_api_key(cfg)
    return cfg


# ── Singleton ──────────────────────────────────────────────────────────────────

_config: AppConfig | None = None


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load config from YAML file. Call once at startup."""
    global _config
    if config_path is None:
        # Walk up from this file to find config.yaml at project root
        here = Path(__file__).parent.parent.parent  # distill/
        config_path = here / "config.yaml"
    raw = _load_yaml(config_path) if config_path.exists() else {}
    _config = _build_config(raw)
    return _config


def get_config() -> AppConfig:
    """Return the loaded config singleton. Raises if load_config() not called."""
    if _config is None:
        return load_config()
    return _config
