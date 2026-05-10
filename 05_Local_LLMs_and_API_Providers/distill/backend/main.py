from __future__ import annotations
"""Distill FastAPI application entry point.

Startup sequence:
1. Load config.yaml
2. Setup structured logging
3. Initialize LLM provider, STT provider, session store
4. Initialize services (analyzer, assessor, evaluator)
5. Register routers
6. Add CORS + exception handlers
7. Log readiness
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import load_config, get_config
from core.logging import setup_logging, get_logger
from core.exceptions import DistillError, distill_exception_handler, generic_exception_handler
from core.prompt_manager import PromptManager
from providers.llm.factory import create_llm_provider
from providers.stt.factory import create_stt_provider
from services.analyzer import TranscriptAnalyzer
from services.assessor import QuestionGenerator
from services.evaluator import AnswerEvaluator
from storage.factory import create_session_store
from routers import analyze, analyze_stream, transcribe, evaluate, sessions, system

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all singletons at startup; release at shutdown."""
    config = load_config()
    setup_logging(config.log_level)

    logger.info(
        "Distill starting",
        version=config.version,
        llm_provider=config.llm.provider,
        llm_model=config.llm.model,
        stt_provider=config.speech_to_text.provider,
    )

    # Wire up all dependencies
    prompt_mgr = PromptManager(config)
    llm = create_llm_provider(config)
    stt = create_stt_provider(config)
    store = create_session_store(config)

    # Store singletons on app.state so routers can access via request.app.state
    app.state.config = config
    app.state.llm = llm
    app.state.stt = stt
    app.state.store = store
    app.state.analyzer = TranscriptAnalyzer(llm, prompt_mgr, config)
    app.state.assessor = QuestionGenerator(llm, prompt_mgr, config)
    app.state.evaluator = AnswerEvaluator(llm, prompt_mgr, config)

    logger.info(
        "Distill ready",
        host=config.server.host,
        port=config.server.port,
        provider=llm.get_provider_name(),
        model=llm.get_model_name(),
    )
    yield

    logger.info("Distill shutting down")


def create_app() -> FastAPI:
    # lifespan() already calls load_config() first; use get_config() here to
    # avoid double-parsing the YAML and prevent any config-divergence window.
    config = get_config() or load_config()

    app = FastAPI(
        title="Distill API",
        version=config.version,
        description="Pure knowledge, every class — AI classroom assessment",
        lifespan=lifespan,
    )

    # CORS — origins from config.yaml server.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Structured error handlers — never expose raw tracebacks
    app.add_exception_handler(DistillError, distill_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)

    # Register all routers under /api prefix
    app.include_router(system.router, prefix="/api", tags=["System"])
    app.include_router(analyze.router, prefix="/api", tags=["Analysis"])
    app.include_router(analyze_stream.router, prefix="/api", tags=["Analysis"])
    app.include_router(transcribe.router, prefix="/api", tags=["Transcription"])
    app.include_router(evaluate.router, prefix="/api", tags=["Evaluation"])
    app.include_router(sessions.router, prefix="/api", tags=["Sessions"])

    return app


app = create_app()
