"""
Shared Jev client for every use case in this folder.

Jev is a System One model: it does not write sentences, it picks.
Three shapes only:
    noul   -> true/false, returns a probability 0..1
    choice -> one option from a menu, returns the pick + probabilities + confidence
    score  -> a position on an ordered scale, returns a weighted value + confidence

Everything here is plain `requests` so students can read it top to bottom.
"""
from __future__ import annotations

import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterable

import requests

API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"

# Jev pricing is not published per-token in the guide, so we do not invent a
# dollar figure. We count tokens and let the caller decide what to do with them.


# --------------------------------------------------------------------------
# Key loading
# --------------------------------------------------------------------------
def _load_key() -> str:
    """Find the API key. Env var wins, then the nearest .env walking upward."""
    for var in ("JEV_KEY", "TYPESAFE_API_KEY"):
        if os.environ.get(var):
            return os.environ[var].strip()

    here = Path(__file__).resolve()
    for parent in here.parents:
        env_file = parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() in ("JEV_KEY", "TYPESAFE_API_KEY"):
                    return value.strip().strip('"').strip("'")
    raise RuntimeError(
        "No Jev key found. Set JEV_KEY in the environment or in a .env file."
    )


# --------------------------------------------------------------------------
# Question builders -- these just produce the dicts the API expects
# --------------------------------------------------------------------------
def noul(instructions: str, true_means: str | None = None,
         false_means: str | None = None) -> dict:
    """A true/false question. The answer is a probability, not a hard yes/no."""
    q: dict[str, Any] = {"type": "noul", "instructions": instructions}
    if true_means or false_means:
        q["criteria"] = {"true": true_means or "", "false": false_means or ""}
    return q


def choice(instructions: str, options: dict[str, str]) -> dict:
    """Pick one option. `options` maps option name -> what it means (max 255)."""
    if not 2 <= len(options) <= 255:
        raise ValueError(f"choice needs 2..255 options, got {len(options)}")
    return {"type": "choice", "instructions": instructions, "criteria": options}


def score(instructions: str, levels: list[str]) -> dict:
    """Rate on an ordered scale. `levels` must be 2..10 descriptions, low to high."""
    if not 2 <= len(levels) <= 10:
        raise ValueError(f"score needs 2..10 levels, got {len(levels)}")
    return {"type": "score", "instructions": instructions, "criteria": levels}


# --------------------------------------------------------------------------
# Client
# --------------------------------------------------------------------------
class Jev:
    """Thin wrapper over the System One endpoint with retries and tallies."""

    def __init__(self, model: str = DEFAULT_MODEL, max_retries: int = 4,
                 timeout: float = 60.0):
        self._key = _load_key()
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        # running tallies so every use case can report cost and speed honestly
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.seconds = 0.0

    def ask(self, state: Any, questions: dict[str, dict]) -> dict:
        """Send one state plus any number of questions. Returns the answers dict."""
        payload = {"state": state, "model": self.model, "questions": questions}
        delay = 0.5
        last_error = None

        for attempt in range(self.max_retries):
            started = time.perf_counter()
            try:
                r = self.session.post(
                    API_URL,
                    headers={"Authorization": f"Bearer {self._key}",
                             "Content-Type": "application/json"},
                    data=json.dumps(payload),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:      # network blip
                last_error = exc
                time.sleep(delay + random.random() * 0.2)
                delay *= 2
                continue
            finally:
                self.seconds += time.perf_counter() - started

            if r.status_code == 200:
                body = r.json()
                self.calls += 1
                usage = body.get("usage", {})
                self.input_tokens += usage.get("input_tokens", 0)
                self.output_tokens += usage.get("output_tokens", 0)
                return body["answers"]

            # 429 rate limited, 529 overloaded -> back off and retry
            if r.status_code in (429, 529):
                last_error = f"HTTP {r.status_code}"
                time.sleep(delay + random.random() * 0.2)
                delay *= 2
                continue

            # 401 bad key, 422 bad request -> no point retrying
            raise RuntimeError(f"Jev HTTP {r.status_code}: {r.text[:400]}")

        raise RuntimeError(f"Jev failed after {self.max_retries} attempts: {last_error}")

    def ask_many(self, items: Iterable[tuple[Any, dict]], workers: int = 8) -> list[dict]:
        """Run many (state, questions) pairs in parallel. Order is preserved."""
        items = list(items)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(lambda pair: self.ask(*pair), items))

    # ---- small helpers so use cases read cleanly ----
    @staticmethod
    def confidence_of(answer: dict) -> float:
        """Confidence for choice/score. Nouls have none, so derive |2p-1|."""
        if answer["type"] == "noul":
            return abs(2 * answer["noul"] - 1)
        return answer.get("confidence", 0.0)

    def stats(self) -> dict:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "seconds": round(self.seconds, 2),
            "avg_ms_per_call": round(1000 * self.seconds / self.calls, 1) if self.calls else 0,
        }

    def report(self, label: str = "") -> str:
        s = self.stats()
        return (f"{label}{' | ' if label else ''}"
                f"{s['calls']} calls, {s['seconds']}s total, "
                f"{s['avg_ms_per_call']}ms avg, "
                f"{s['input_tokens']} in / {s['output_tokens']} out tokens")
