from __future__ import annotations
"""Jinja2 prompt template manager.

Templates live in the directory specified by config.prompts.directory.
All evaluation config variables are automatically injected into every render call
so templates can reference interviewer.name, score_dimensions, etc. without
manual plumbing at each call site.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from core.config import AppConfig
from core.exceptions import ConfigError


class PromptManager:
    def __init__(self, config: AppConfig):
        self.config = config
        # Resolve template directory relative to config.yaml location
        base_dir = Path(__file__).parent.parent.parent  # distill/
        template_dir = base_dir / config.prompts.directory.lstrip("./")
        if not template_dir.exists():
            raise ConfigError(f"Prompt template directory not found: {template_dir}")

        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,  # no HTML escaping — prompts are plain text
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self._template_map = config.prompts.templates

        # Pre-build the evaluation context injected into every render
        self._eval_ctx = self._build_eval_context()

    def _build_eval_context(self) -> dict:
        """Build the evaluation config context automatically injected into templates."""
        ev = self.config.evaluation
        return {
            "interviewer_name": ev.interviewer.name,
            "interviewer_persona": ev.interviewer.persona,
            "interviewer_style": ev.interviewer.style,
            "interviewer_domain": ev.interviewer.domain,
            "score_dimensions": [
                {
                    "key": d.key,
                    "label": d.label,
                    "weight": d.weight,
                    "description": d.description,
                }
                for d in ev.score_dimensions
            ],
            "verdicts": [
                {"label": v.label, "min_weighted_score": v.min_weighted_score}
                for v in ev.verdicts
            ],
            # Concept map config
            "direction": self.config.concept_map.direction,
            "max_nodes": self.config.concept_map.max_nodes,
        }

    def render(self, template_key: str, **kwargs) -> str:
        """Render a prompt template by its config key (e.g. 'summary', 'evaluate_voice').

        Evaluation config is auto-injected. Any kwargs override injected values.
        """
        filename = self._template_map.get(template_key)
        if not filename:
            raise ConfigError(f"No template configured for key '{template_key}'")
        try:
            template = self._env.get_template(filename)
        except TemplateNotFound:
            raise ConfigError(f"Template file not found: {filename}")

        # Merge: auto-injected eval context + caller-supplied kwargs (caller wins)
        context = {**self._eval_ctx, **kwargs}
        return template.render(**context)

    def reload(self) -> None:
        """Hot-reload templates from disk (no restart needed after prompt edits).

        Swapping the loader instance invalidates Jinja2's template cache by
        reference — no need to call .cache.clear() (that attribute doesn't exist
        on jinja2.Environment anyway).
        """
        self._env.loader = FileSystemLoader(  # type: ignore[arg-type]
            str(Path(__file__).parent.parent.parent / self.config.prompts.directory.lstrip("./"))
        )
