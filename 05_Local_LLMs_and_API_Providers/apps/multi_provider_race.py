"""🏁 LLM Provider Race — Streamlit app.

Send the same question to Ollama, LM Studio, OpenAI, Anthropic, Gemini,
and OpenRouter simultaneously. Watch responses stream in real time side by
side, then see who wins on speed, tokens, and quality.

Run:
    streamlit run multi_provider_race.py

Requires (sidebar):
    - Ollama running on :11434  (free, local)
    - LM Studio running on :1234  (free, local)
    - OPENAI_API_KEY    (for OpenAI panel)
    - ANTHROPIC_API_KEY (for Anthropic panel)
    - GOOGLE_API_KEY    (for Gemini panel)
    - OPENROUTER_API_KEY (for OpenRouter panel, free tier available)
"""

from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LLM Provider Race 🏁",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.provider-card {
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
    background: #0d1117;
    min-height: 220px;
    font-family: 'Segoe UI', sans-serif;
}
.provider-header {
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 8px;
}
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    background: #21262d;
    color: #8b949e;
    margin-left: 6px;
}
.medal { font-size: 22px; }
</style>
""", unsafe_allow_html=True)


# ── Provider registry ─────────────────────────────────────────────────────────

PROVIDERS: dict[str, dict] = {
    "ollama": {
        "name": "Ollama",
        "emoji": "🦙",
        "color": "#4A90D9",
        "type": "openai_compatible",
        "base_url": "http://localhost:11434/v1",
        "api_key_env": None,
        "default_key": "ollama",
        "default_model": "llama3.1:latest",
        "note": "Local · free · private",
    },
    "lmstudio": {
        "name": "LM Studio",
        "emoji": "🖥️",
        "color": "#7B68EE",
        "type": "openai_compatible",
        "base_url": "http://localhost:1234/v1",
        "api_key_env": None,
        "default_key": "lm-studio",
        "default_model": "qwen/qwen3-4b-2507",
        "note": "Local · GUI model manager",
        "strip_system": True,  # qwen3 in LM Studio errors on system role messages
    },
    "openai": {
        "name": "OpenAI",
        "emoji": "🤖",
        "color": "#10A37F",
        "type": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "default_key": "",
        "default_model": "gpt-4o-mini",
        "note": "Cloud · fast · reliable",
    },
    "anthropic": {
        "name": "Anthropic",
        "emoji": "🧠",
        "color": "#D4573C",
        "type": "anthropic",
        "base_url": None,
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_key": "",
        "default_model": "claude-haiku-4-5-20251001",
        "note": "Cloud · best reasoning",
    },
    "gemini": {
        "name": "Gemini",
        "emoji": "✨",
        "color": "#4285F4",
        "type": "gemini",
        "base_url": None,
        "api_key_env": "GOOGLE_API_KEY",
        "default_key": "",
        "default_model": "gemini-2.5-flash",
        "note": "Cloud · free tier available",
    },
    "openrouter": {
        "name": "OpenRouter",
        "emoji": "🔀",
        "color": "#FF6B35",
        "type": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_key": "",
        "default_model": "meta-llama/llama-3.1-8b-instruct",
        "note": "Cloud · 200+ models · free tier",
    },
}

PROVIDER_ORDER = ["ollama", "lmstudio", "openrouter", "openai", "anthropic", "gemini"]

SAMPLE_PROMPTS = [
    "Explain how transformers work in 3 sentences.",
    "What is the difference between RAG and fine-tuning? Give me a one-paragraph answer.",
    "Write a Python function that reverses a linked list.",
    "What are 3 real-world use cases for vector databases?",
    "Explain the attention mechanism like I'm 15 years old.",
    "What is quantization in LLMs and why does it matter for local deployment?",
]


# ── Shared result state ───────────────────────────────────────────────────────

@dataclass
class ProviderResult:
    text: str = ""
    latency: float = 0.0
    token_count: int = 0
    done: bool = False
    error: str | None = None
    finish_rank: int | None = None   # 1=first to finish, 2=second, ...


# ── Streaming workers ─────────────────────────────────────────────────────────

def _worker_openai_compatible(
    pid: str,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float,
    results: dict[str, ProviderResult],
    lock: threading.Lock,
    finish_counter: list[int],
) -> None:
    from openai import OpenAI, OpenAIError
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=60)
    start = time.time()
    text = ""
    tokens = 0
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text += chunk.choices[0].delta.content
                tokens += 1
                with lock:
                    results[pid].text = text
                    results[pid].latency = time.time() - start
                    results[pid].token_count = tokens
        with lock:
            finish_counter[0] += 1
            results[pid].done = True
            results[pid].latency = round(time.time() - start, 2)
            results[pid].finish_rank = finish_counter[0]
    except OpenAIError as e:
        with lock:
            results[pid].done = True
            results[pid].error = str(e)
            results[pid].latency = round(time.time() - start, 2)
    except Exception as e:
        with lock:
            results[pid].done = True
            results[pid].error = f"Unexpected error: {e}"
            results[pid].latency = round(time.time() - start, 2)


def _worker_anthropic(
    pid: str,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float,
    results: dict[str, ProviderResult],
    lock: threading.Lock,
    finish_counter: list[int],
) -> None:
    try:
        import anthropic as ant
    except ImportError:
        with lock:
            results[pid].done = True
            results[pid].error = "anthropic package not installed. Run: pip install anthropic"
        return

    client = ant.Anthropic(api_key=api_key)
    start = time.time()
    text = ""
    tokens = 0
    try:
        with client.messages.stream(
            model=model,
            max_tokens=1024,
            messages=messages,
        ) as stream:
            for chunk in stream.text_stream:
                text += chunk
                tokens += 1
                with lock:
                    results[pid].text = text
                    results[pid].latency = time.time() - start
                    results[pid].token_count = tokens
        with lock:
            finish_counter[0] += 1
            results[pid].done = True
            results[pid].latency = round(time.time() - start, 2)
            results[pid].finish_rank = finish_counter[0]
    except Exception as e:
        with lock:
            results[pid].done = True
            results[pid].error = str(e)
            results[pid].latency = round(time.time() - start, 2)


def _worker_gemini(
    pid: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    results: dict[str, ProviderResult],
    lock: threading.Lock,
    finish_counter: list[int],
) -> None:
    try:
        from google import genai
        from google.genai import types as gentypes
    except ImportError:
        with lock:
            results[pid].done = True
            results[pid].error = "google-genai not installed. Run: pip install google-genai"
        return

    client = genai.Client(api_key=api_key)
    start = time.time()
    text = ""
    tokens = 0
    try:
        config = gentypes.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=1024,
        )
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=config,
        ):
            if chunk.text:
                text += chunk.text
                tokens += len(chunk.text.split())
                with lock:
                    results[pid].text = text
                    results[pid].latency = time.time() - start
                    results[pid].token_count = tokens
        with lock:
            finish_counter[0] += 1
            results[pid].done = True
            results[pid].latency = round(time.time() - start, 2)
            results[pid].finish_rank = finish_counter[0]
    except Exception as e:
        with lock:
            results[pid].done = True
            results[pid].error = str(e)
            results[pid].latency = round(time.time() - start, 2)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Race Configuration")

    st.subheader("Active Providers")
    active: dict[str, bool] = {}
    models: dict[str, str] = {}
    api_keys: dict[str, str] = {}

    for pid in PROVIDER_ORDER:
        p = PROVIDERS[pid]
        active[pid] = st.checkbox(
            f"{p['emoji']} {p['name']}",
            value=True,
            key=f"active_{pid}",
        )
        if active[pid]:
            models[pid] = st.text_input(
                "Model",
                value=p["default_model"],
                key=f"model_{pid}",
                label_visibility="collapsed",
                placeholder=f"{p['name']} model name",
            )
            env_key = p.get("api_key_env")
            default_key = os.environ.get(env_key, "") if env_key else p["default_key"]
            if env_key:
                api_keys[pid] = st.text_input(
                    f"API Key",
                    value=default_key,
                    type="password",
                    key=f"key_{pid}",
                    label_visibility="collapsed",
                    placeholder=f"{p['name']} API key",
                )
            else:
                api_keys[pid] = p["default_key"]

    st.divider()

    st.subheader("Generation Settings")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    system_prompt = st.text_area(
        "System prompt (optional)",
        value="You are a helpful AI assistant. Be concise and clear.",
        height=80,
    )

    st.divider()
    st.subheader("💡 Sample Prompts")
    for sp in SAMPLE_PROMPTS:
        if st.button(sp[:55] + "…" if len(sp) > 55 else sp, use_container_width=True):
            st.session_state["prefill_prompt"] = sp


# ── Main UI ───────────────────────────────────────────────────────────────────

st.title("🏁 LLM Provider Race")
st.caption("Ask one question — get answers from every provider simultaneously. Watch them stream in real time.")

prompt = st.text_area(
    "Your question",
    value=st.session_state.get("prefill_prompt", ""),
    height=100,
    placeholder="Explain how transformers work in 3 sentences.",
    key="prompt_input",
)

col_run, col_clear = st.columns([1, 6])
with col_run:
    run = st.button("🏁 Start Race", type="primary", use_container_width=True, disabled=not prompt.strip())
with col_clear:
    if st.button("🗑️ Clear", use_container_width=False):
        st.session_state.pop("prefill_prompt", None)
        st.rerun()

st.divider()

# ── Race execution ────────────────────────────────────────────────────────────

if run and prompt.strip():
    active_providers = [pid for pid in PROVIDER_ORDER if active.get(pid)]
    if not active_providers:
        st.warning("Enable at least one provider in the sidebar.")
        st.stop()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    # Shared state — threads write here, main thread reads
    lock = threading.Lock()
    finish_counter = [0]  # mutable counter shared across threads
    results: dict[str, ProviderResult] = {pid: ProviderResult() for pid in active_providers}

    # ── Launch one thread per provider ───────────────────────────────────────
    threads: list[threading.Thread] = []

    for pid in active_providers:
        p = PROVIDERS[pid]
        ptype = p["type"]
        model = models[pid]
        key = api_keys.get(pid, "")

        if ptype == "openai_compatible":
            # Some local models error on system role — merge it into the first user message
            if p.get("strip_system") and messages and messages[0]["role"] == "system":
                sys_text = messages[0]["content"]
                user_text = messages[1]["content"] if len(messages) > 1 else ""
                provider_messages = [{"role": "user", "content": f"{sys_text}\n\n{user_text}"}]
            else:
                provider_messages = messages
            t = threading.Thread(
                target=_worker_openai_compatible,
                args=(pid, p["base_url"], key, model, provider_messages, temperature, results, lock, finish_counter),
                daemon=True,
            )
        elif ptype == "anthropic":
            t = threading.Thread(
                target=_worker_anthropic,
                args=(pid, key, model, messages[1:], temperature, results, lock, finish_counter),
                daemon=True,
            )
        elif ptype == "gemini":
            t = threading.Thread(
                target=_worker_gemini,
                args=(pid, key, model, prompt, temperature, results, lock, finish_counter),
                daemon=True,
            )
        else:
            continue

        threads.append(t)
        t.start()

    # ── Build placeholder grid (3 columns × 2 rows) ───────────────────────────
    n = len(active_providers)
    cols_per_row = min(3, n)
    rows = [active_providers[i:i+cols_per_row] for i in range(0, n, cols_per_row)]

    placeholders: dict[str, st.delta_generator.DeltaGenerator] = {}

    for row_providers in rows:
        cols = st.columns(len(row_providers))
        for col, pid in zip(cols, row_providers):
            p = PROVIDERS[pid]
            with col:
                st.markdown(
                    f"<div class='provider-header' style='color:{p['color']}'>"
                    f"{p['emoji']} {p['name']} &nbsp;"
                    f"<span class='badge'>{models[pid]}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                placeholders[pid] = st.empty()
                st.caption(p["note"])

    # ── Polling loop — update placeholders until all done ─────────────────────
    race_start = time.time()

    while True:
        with lock:
            snapshot = {pid: ProviderResult(
                text=results[pid].text,
                latency=results[pid].latency,
                token_count=results[pid].token_count,
                done=results[pid].done,
                error=results[pid].error,
                finish_rank=results[pid].finish_rank,
            ) for pid in active_providers}

        all_done = all(r.done for r in snapshot.values())

        for pid, r in snapshot.items():
            if r.error:
                placeholders[pid].error(f"⚠️ {r.error}")
            elif r.done:
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(r.finish_rank, "✅")
                placeholders[pid].markdown(
                    f"{r.text}\n\n"
                    f"---\n"
                    f"{medal} **{r.latency}s** · ~{r.token_count} tokens"
                )
            elif r.text:
                # streaming cursor
                placeholders[pid].markdown(r.text + " ▌")
            else:
                placeholders[pid].markdown("⏳ Waiting for first token…")

        if all_done:
            break

        time.sleep(0.1)

    # ── Join threads ──────────────────────────────────────────────────────────
    for t in threads:
        t.join(timeout=2)

    # ── Leaderboard ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🏆 Leaderboard")

    finished = [(pid, r) for pid, r in snapshot.items() if r.done and not r.error]
    errored  = [(pid, r) for pid, r in snapshot.items() if r.error]

    finished_sorted = sorted(finished, key=lambda x: x[1].latency)

    medals = ["🥇", "🥈", "🥉"]
    lb_cols = st.columns(len(finished_sorted)) if finished_sorted else []

    for i, (pid, r) in enumerate(finished_sorted):
        p = PROVIDERS[pid]
        tps = round(r.token_count / r.latency, 1) if r.latency > 0 else 0
        medal = medals[i] if i < 3 else f"#{i+1}"
        with lb_cols[i]:
            st.metric(
                label=f"{medal} {p['emoji']} {p['name']}",
                value=f"{r.latency}s",
                delta=f"~{tps} tok/s · {r.token_count} tokens",
                delta_color="off",
            )

    if errored:
        with st.expander(f"⚠️ {len(errored)} provider(s) failed"):
            for pid, r in errored:
                p = PROVIDERS[pid]
                st.error(f"**{p['emoji']} {p['name']}:** {r.error}")

    total_time = round(time.time() - race_start, 2)
    st.caption(f"Total wall-clock time: {total_time}s for {len(active_providers)} providers in parallel")
