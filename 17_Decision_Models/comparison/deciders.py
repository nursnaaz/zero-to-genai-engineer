"""
Three ways to make the same typed decision, behind one interface.

  jev      TypeSafe Jev, hosted decision model, direct API
  strands  Strands Decider 2B, open source, running locally on this machine
  luna     OpenAI Decisions API, POST /v1/decisions, model gpt-6-luna

All three are purpose-built typed-decision interfaces, so this is a like for
like comparison: same state, same options, same gold labels.
"""
from __future__ import annotations
import json, pathlib, time
from dataclasses import dataclass, field

import requests

REPO = pathlib.Path(__file__).resolve().parents[2]


def _env(path: str, name: str) -> str | None:
    p = REPO / path
    if not p.exists():
        return None
    for line in p.read_text().splitlines():
        line = line.strip()
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


@dataclass
class Answer:
    pick: str | None          # chosen option (choice) or None
    prob: float | None        # probability of yes (noul)
    confidence: float         # 0..1, comparable across backends
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    raw: dict = field(default_factory=dict)


class Decider:
    name = "base"
    def choice(self, state, instructions, options: dict[str, str]) -> Answer: ...
    def noul(self, state, instructions, criteria=None) -> Answer: ...


# ---------------------------------------------------------------- Jev
class JevDecider(Decider):
    name = "jev"
    URL = "https://api.typesafe.ai/v1/systemone"

    def __init__(self):
        self.key = _env("17_Decision_Models/Jev/.env", "JEV_KEY")
        self.s = requests.Session()

    def _ask(self, state, questions):
        t0 = time.perf_counter()
        r = self.s.post(self.URL,
                        headers={"Authorization": f"Bearer {self.key}",
                                 "Content-Type": "application/json"},
                        data=json.dumps({"state": state, "model": "jev-latest",
                                         "questions": questions}), timeout=60)
        ms = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        b = r.json()
        return b["answers"], b.get("usage", {}), ms

    def choice(self, state, instructions, options):
        a, u, ms = self._ask(state, {"q": {"type": "choice",
                                           "instructions": instructions,
                                           "criteria": options}})
        q = a["q"]
        return Answer(q["choice"], None, q["confidence"], ms,
                      u.get("input_tokens", 0), u.get("output_tokens", 0), q)

    def noul(self, state, instructions, criteria=None):
        q_ = {"type": "noul", "instructions": instructions}
        if criteria: q_["criteria"] = criteria
        a, u, ms = self._ask(state, {"q": q_})
        p = a["q"]["noul"]
        return Answer(None, p, abs(2 * p - 1), ms,
                      u.get("input_tokens", 0), u.get("output_tokens", 0), a["q"])


# ------------------------------------------------- Strands Decider 2B (local)
class StrandsDecider(Decider):
    name = "strands"
    URL = "http://127.0.0.1:8077/v1/systemone"

    def _ask(self, state, questions):
        t0 = time.perf_counter()
        r = requests.post(self.URL, json={"state": state, "questions": questions}, timeout=180)
        ms = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        b = r.json()
        return b["answers"], b.get("usage", {}), ms

    def choice(self, state, instructions, options):
        a, u, ms = self._ask(state, {"q": {"type": "choice",
                                           "instructions": instructions,
                                           "criteria": options}})
        q = a["q"]
        return Answer(q["choice"], None, q["confidence"], ms,
                      u.get("input_tokens", 0), u.get("output_tokens", 0), q)

    def noul(self, state, instructions, criteria=None):
        q_ = {"type": "noul", "instructions": instructions}
        if criteria: q_["criteria"] = criteria
        a, u, ms = self._ask(state, {"q": q_})
        p = a["q"]["noul"]
        return Answer(None, p, abs(2 * p - 1), ms,
                      u.get("input_tokens", 0), u.get("output_tokens", 0), a["q"])


# --------------------------------------------- OpenAI Decisions API (gpt-6-luna)
class LunaDecider(Decider):
    """POST /v1/decisions. Note the vocabulary differs from Jev/Strands:
    `input` not `state`, `questions` is a LIST not a dict, and a yes/no
    question is a `predicate` rather than a `noul`."""
    name = "luna"
    URL = "https://api.openai.com/v1/decisions"
    PRICE_IN = 0.10 / 1_000_000        # $0.10 per 1M input tokens, output is free

    def __init__(self, model="gpt-6-luna"):
        self.key = _env("17_Decision_Models/.env", "OPENAI_API_KEY")
        self.model = model
        self.s = requests.Session()

    def _ask(self, input_, questions):
        t0 = time.perf_counter()
        r = self.s.post(self.URL,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
            data=json.dumps({"model": self.model, "input": input_, "questions": questions}),
            timeout=120)
        ms = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
        b = r.json()
        return {a["name"]: a for a in b["answers"]}, b.get("usage", {}), ms

    @staticmethod
    def _as_text(state):
        return state if isinstance(state, str) else json.dumps(state)

    def choice(self, state, instructions, options):
        q = [{"type": "choice", "name": "q", "instructions": instructions,
              "choices": [{"value": k, "description": v} for k, v in options.items()]}]
        a, u, ms = self._ask(self._as_text(state), q)
        ans = a["q"]
        if ans["type"] == "refusal":
            return Answer(None, None, 0.0, ms, u.get("input_tokens", 0), 0, ans)
        return Answer(ans["choice"], None, ans.get("confidence", 0.0), ms,
                      u.get("input_tokens", 0), u.get("output_tokens", 0), ans)

    def noul(self, state, instructions, criteria=None):
        instr = instructions
        if criteria:
            instr += (f"\nAnswer yes if: {criteria.get('true','')}"
                      f"\nAnswer no if: {criteria.get('false','')}")
        q = [{"type": "predicate", "name": "q", "instructions": instr}]
        a, u, ms = self._ask(self._as_text(state), q)
        ans = a["q"]
        if ans["type"] == "refusal":
            return Answer(None, None, 0.0, ms, u.get("input_tokens", 0), 0, ans)
        p = ans["probability"]
        return Answer(None, p, abs(2 * p - 1), ms,
                      u.get("input_tokens", 0), u.get("output_tokens", 0), ans)

    def cost(self, in_tok, out_tok):
        return in_tok * self.PRICE_IN        # output tokens are not billed
