"""📄 Map-Reduce Summarizer — Streamlit demo.

Shows students exactly how long-document summarization works:
  1. SPLIT   — break the text into overlapping chunks
  2. MAP     — summarize each chunk independently (parallel)
  3. REDUCE  — merge the chunk summaries into one final summary

Works with Ollama (local, free) or LM Studio (local, free).

Run:
    streamlit run map_reduce_demo.py
"""

from __future__ import annotations

import time
import threading
import textwrap

import streamlit as st
from openai import OpenAI

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Map-Reduce Summarizer",
    page_icon="📄",
    layout="wide",
)

st.markdown("""
<style>
.chunk-card {
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 8px;
    font-size: 12px;
    line-height: 1.5;
    color: #cdd9e5;
    overflow: hidden;
    white-space: pre-wrap;
    word-break: break-word;
}
.step-header {
    font-size: 18px;
    font-weight: 700;
    margin: 20px 0 10px 0;
    padding: 8px 14px;
    border-radius: 6px;
    background: #21262d;
}
</style>
""", unsafe_allow_html=True)

# Distinct colors for up to 12 chunks
CHUNK_COLORS = [
    "#1a3a4a", "#2d1f3d", "#1a3d2a", "#3d2a1a",
    "#1a2a3d", "#3d1a2a", "#2a3d1a", "#3d3a1a",
    "#1a3d3d", "#3d1a3d", "#2a1a3d", "#3a3d1a",
]

SAMPLE_TEXTS = {
    "📰 AI Research Excerpt": """
Artificial intelligence has undergone a dramatic transformation over the past decade.
The introduction of the transformer architecture in 2017 by Vaswani et al. marked a
turning point that would reshape the entire field. Prior to transformers, recurrent
neural networks and long short-term memory networks dominated sequence modeling tasks.
These architectures processed sequences token by token, making parallelization during
training difficult and causing gradients to vanish over long sequences.

The transformer addressed these limitations through the self-attention mechanism, which
allows every token in a sequence to attend to every other token simultaneously. This
parallel computation enabled training on much larger datasets and resulted in
dramatically improved performance across natural language processing benchmarks.

The release of BERT in 2018 demonstrated that pre-training on large corpora followed
by task-specific fine-tuning could achieve state-of-the-art results across diverse NLP
tasks. GPT-2 in 2019 showed that autoregressive language models could generate
surprisingly coherent long-form text. These results hinted at an emergent capability
that would become central to modern AI: in-context learning.

GPT-3, released in 2020 with 175 billion parameters, shocked the research community
with its ability to perform tasks from just a few examples provided in the prompt,
without any weight updates. This few-shot learning capability suggested that scale
alone could unlock qualitatively new behaviors. Researchers began studying scaling
laws — mathematical relationships between model size, training data, compute, and
performance — to understand and predict these emergent capabilities.

The introduction of instruction tuning and reinforcement learning from human feedback
in InstructGPT and ChatGPT made these powerful models usable by non-experts. Rather
than requiring careful prompt engineering, users could simply ask questions in natural
language and receive helpful, coherent responses. This triggered the current wave of
AI application development, with organizations integrating large language models into
products ranging from code assistants to customer service systems.

Retrieval-augmented generation emerged as a practical solution to the knowledge
cutoff problem inherent in language models. By retrieving relevant documents at
inference time and providing them as context, RAG systems can answer questions about
events after training without requiring expensive retraining. Vector databases became
essential infrastructure for storing and efficiently retrieving document embeddings.

The field of AI agents represents the next frontier. Rather than answering a single
question, agents can decompose complex tasks, call external tools, and iteratively
refine their outputs. Frameworks like LangChain, LangGraph, and AutoGen provide
abstractions for building these systems. Multi-agent architectures, where specialized
agents collaborate on subtasks, are showing promise for tasks too complex for a single
model to handle.

Looking ahead, multimodal models that process text, images, audio, and video together
are expanding the scope of what AI can reason about. Models like GPT-4V and Gemini
can analyze charts, describe images, and answer questions about visual content.
The combination of multimodal perception, reasoning, tool use, and long-context
understanding is rapidly closing the gap between AI systems and human cognitive
capabilities.
""".strip(),

    "🎓 Lecture Transcript": """
Welcome, everyone. Today we're going to talk about something that I think is one of
the most exciting developments in AI in the last few years: Retrieval-Augmented
Generation, or RAG for short.

So let's start with the fundamental problem. You've probably used ChatGPT or Claude,
and you've noticed that sometimes they just make things up. We call this hallucination.
Why does it happen? The model was trained on data up to a certain point in time.
After that, it has no knowledge of what happened. And even for things within its
training data, it can sometimes get facts wrong because it's essentially pattern
matching rather than looking things up.

Now imagine you're building an AI assistant for a company. The company has thousands
of internal documents: policies, product manuals, meeting notes. The model doesn't
know any of this. How do you solve this? You could fine-tune the model on your data.
But fine-tuning is expensive, slow, and you'd have to redo it every time your data
changes. Not practical.

This is where RAG comes in. The idea is brilliant in its simplicity. Instead of
baking knowledge into the model's weights, you retrieve relevant information at
query time and give it to the model as context. So when a user asks "what is our
vacation policy?", the system first searches your document database for relevant
passages about vacation policy, then includes those passages in the prompt to the
model, then the model generates an answer grounded in those specific passages.

Let's walk through the pipeline. Step one is document processing. You take all your
documents — PDFs, Word files, web pages, whatever — and you split them into smaller
chunks. Why chunks? Because language models have a context window limit. You can't
just dump a 500-page manual into the prompt.

Step two is embedding. You take each chunk and run it through an embedding model,
which converts the text into a high-dimensional vector of numbers. Similar chunks
will have similar vectors. This is the semantic representation of the content.

Step three is storage. You store these vectors in a vector database. ChromaDB is
popular for local development. Pinecone, Weaviate, and Milvus are production options.

Step four is retrieval. When a user asks a question, you embed the question using
the same embedding model and search for the most similar chunk vectors. You get back
the top-k most relevant passages.

Step five is generation. You construct a prompt that includes the retrieved passages
and the user's question, and you send it to the language model. The model generates
an answer based on the provided context.

The beautiful thing about this approach is that it's dynamic. Your document database
can be updated in real time without touching the model. It's also more transparent
because the model can cite the sources it used to generate the answer.

Of course, basic RAG has limitations. If the user's question uses different words
than what's in the documents, the vector search might miss relevant content. This
is where hybrid search helps — combining vector search with traditional keyword
search like BM25 for better coverage.

There's also the problem of long-context loss. If you retrieve ten chunks and stuff
them all into the context, the model might not pay attention to chunks in the middle.
Reranking helps here — after retrieval, you use a cross-encoder model to rerank the
candidates and only keep the most relevant ones.

For your practical exercise today, I want you to build a simple RAG pipeline from
scratch. You'll use ChromaDB as your vector store, a sentence-transformer model for
embeddings, and either the Gemini API or a local Ollama model for generation.
The dataset I've prepared is a collection of AI research paper abstracts.
""".strip(),
}


# ── Core functions ────────────────────────────────────────────────────────────

def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[dict]:
    """Split text into overlapping chunks. Returns list of {index, text, start, end}."""
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Don't cut in the middle of a word
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({"index": idx, "text": chunk_text, "start": start, "end": end})
            idx += 1
        start = end - overlap if end < len(text) else len(text)
    return chunks


def summarize_chunk(chunk: str, client: OpenAI, model: str) -> str:
    """Summarize a single chunk. Called in parallel by worker threads."""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise summarizer. Extract the key ideas from the text below "
                    "into 2-4 bullet points. Be concise. Do NOT add anything not in the text."
                ),
            },
            {"role": "user", "content": f"Summarize this text:\n\n{chunk}"},
        ],
        max_tokens=300,
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""


def merge_summaries(summaries: list[str], client: OpenAI, model: str) -> str:
    """Merge all chunk summaries into a coherent final summary."""
    combined = "\n\n".join(
        f"--- Chunk {i+1} summary ---\n{s}" for i, s in enumerate(summaries)
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert synthesizer. Below are summaries of consecutive sections "
                    "of a longer document. Merge them into a single, coherent, well-structured summary. "
                    "Remove duplication. Preserve all key ideas. Use clear paragraphs."
                ),
            },
            {"role": "user", "content": f"Merge these summaries:\n\n{combined}"},
        ],
        max_tokens=800,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Configuration")

    provider = st.radio("LLM Provider", ["Ollama", "LM Studio"], horizontal=True)
    base_url = "http://localhost:11434/v1" if provider == "Ollama" else "http://localhost:1234/v1"
    api_key  = "ollama" if provider == "Ollama" else "lm-studio"

    model = st.text_input(
        "Model name",
        value="llama3.1:latest" if provider == "Ollama" else "qwen/qwen3-4b-2507",
    )

    st.divider()
    st.subheader("Chunking Parameters")

    chunk_size = st.slider(
        "Chunk size (chars)",
        min_value=500,
        max_value=10000,
        value=2000,
        step=100,
        help="How many characters per chunk. Smaller = more chunks = slower but more detailed.",
    )
    overlap = st.slider(
        "Overlap (chars)",
        min_value=0,
        max_value=500,
        value=200,
        step=50,
        help="How many characters to repeat between chunks to avoid losing context at boundaries.",
    )

    st.divider()
    st.subheader("📚 Sample Texts")
    for label in SAMPLE_TEXTS:
        if st.button(label, use_container_width=True):
            st.session_state["sample_text"] = SAMPLE_TEXTS[label]


# ── Main UI ───────────────────────────────────────────────────────────────────

st.title("📄 Map-Reduce Document Summarizer")
st.caption("See exactly how AI handles documents too long for a single prompt.")

tab_input, tab_how = st.tabs(["📥 Summarize", "🧠 How it works"])

with tab_how:
    st.markdown("""
### Why do we need Map-Reduce?

Language models have a **context window limit** — they can only read a fixed number
of tokens at once. GPT-4 supports ~128k tokens, but a book or long transcript can
be millions of characters. Map-Reduce is the solution.

### The 3 steps:

```
Original document (potentially 100,000+ characters)
         │
         ▼
┌────────────────────────────────────────────────┐
│  SPLIT — Break into overlapping chunks         │
│  Chunk 1  Chunk 2  Chunk 3 ... Chunk N         │
└────────────────────────────────────────────────┘
         │
         ▼ (parallel — all at once)
┌────────────────────────────────────────────────┐
│  MAP — Summarize each chunk independently      │
│  Sum 1   Sum 2   Sum 3  ...  Sum N             │
└────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│  REDUCE — Merge all summaries into one         │
│           Final coherent summary               │
└────────────────────────────────────────────────┘
```

### Why overlap?
If chunk 1 ends at word 200 and chunk 2 starts at word 200, the sentence spanning
the boundary gets split and loses meaning. Overlap (e.g. 200 chars) means the end
of chunk 1 is repeated at the start of chunk 2, so no context is lost.

### Real-world use cases
- Summarize a 100-page contract in seconds
- Extract key insights from a semester of lecture transcripts
- Digest a research paper you don't have time to read
- Summarize a day's worth of Slack messages
""")

with tab_input:
    col_text, col_upload = st.columns([3, 1])

    with col_upload:
        uploaded = st.file_uploader("Upload .txt file", type=["txt"])
        if uploaded:
            st.session_state["sample_text"] = uploaded.read().decode("utf-8", errors="ignore")

    with col_text:
        text_input = st.text_area(
            "Paste your text here",
            value=st.session_state.get("sample_text", ""),
            height=220,
            placeholder="Paste a long article, lecture transcript, or meeting notes…",
        )

    if text_input:
        char_count = len(text_input)
        word_count = len(text_input.split())
        chunks_preview = split_into_chunks(text_input, chunk_size, overlap)
        st.caption(f"📊 **{char_count:,}** characters · **{word_count:,}** words · will split into **{len(chunks_preview)}** chunks")

    run = st.button(
        "🚀 Summarize",
        type="primary",
        disabled=not text_input.strip(),
        use_container_width=False,
    )

    if run and text_input.strip():
        client = OpenAI(base_url=base_url, api_key=api_key, timeout=120)
        chunks = split_into_chunks(text_input, chunk_size, overlap)

        # ── STEP 1: Show chunks ──────────────────────────────────────────────
        st.markdown("<div class='step-header'>① SPLIT — Breaking text into chunks</div>", unsafe_allow_html=True)
        st.caption(f"{len(chunks)} chunks · {chunk_size:,} chars each · {overlap} char overlap")

        chunk_cols = st.columns(min(len(chunks), 4))
        for i, chunk in enumerate(chunks):
            color = CHUNK_COLORS[i % len(CHUNK_COLORS)]
            preview = textwrap.shorten(chunk["text"], width=180, placeholder="…")
            with chunk_cols[i % len(chunk_cols)]:
                st.markdown(
                    f"<div class='chunk-card' style='border-left: 3px solid {color}; background:{color}22'>"
                    f"<strong>Chunk {i+1}</strong> &nbsp;·&nbsp; {len(chunk['text']):,} chars<br><br>"
                    f"{preview}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # ── STEP 2: MAP — Summarize chunks in parallel ───────────────────────
        st.markdown("<div class='step-header'>② MAP — Summarizing each chunk (in parallel)</div>", unsafe_allow_html=True)

        summaries: list[str | None] = [None] * len(chunks)
        errors:    list[str | None] = [None] * len(chunks)
        lock = threading.Lock()
        done_count = [0]

        def _summarize_worker(i: int, chunk_text: str) -> None:
            try:
                s = summarize_chunk(chunk_text, client, model)
                with lock:
                    summaries[i] = s
                    done_count[0] += 1
            except Exception as e:
                with lock:
                    errors[i] = str(e)
                    done_count[0] += 1

        threads = [
            threading.Thread(target=_summarize_worker, args=(i, c["text"]), daemon=True)
            for i, c in enumerate(chunks)
        ]
        for t in threads:
            t.start()

        # Progress bar while workers run
        progress_bar = st.progress(0, text="Summarizing chunks…")
        chunk_placeholders = [st.empty() for _ in chunks]

        while done_count[0] < len(chunks):
            with lock:
                done = done_count[0]
                snap_summaries = list(summaries)
                snap_errors = list(errors)

            progress_bar.progress(done / len(chunks), text=f"Summarized {done}/{len(chunks)} chunks…")

            for i in range(len(chunks)):
                color = CHUNK_COLORS[i % len(CHUNK_COLORS)]
                if snap_errors[i]:
                    chunk_placeholders[i].error(f"Chunk {i+1}: {snap_errors[i]}")
                elif snap_summaries[i]:
                    chunk_placeholders[i].success(f"**Chunk {i+1} summary:**\n\n{snap_summaries[i]}")
                else:
                    chunk_placeholders[i].info(f"⏳ Chunk {i+1}: summarizing…")

            time.sleep(0.3)

        for t in threads:
            t.join(timeout=5)

        progress_bar.progress(1.0, text=f"All {len(chunks)} chunks summarized ✓")

        # Final render of all chunk summaries
        for i in range(len(chunks)):
            color = CHUNK_COLORS[i % len(CHUNK_COLORS)]
            if errors[i]:
                chunk_placeholders[i].error(f"Chunk {i+1} failed: {errors[i]}")
            elif summaries[i]:
                chunk_placeholders[i].success(f"**Chunk {i+1} summary:**\n\n{summaries[i]}")

        valid_summaries = [s for s in summaries if s]

        if not valid_summaries:
            st.error("All chunk summarizations failed. Check your provider connection.")
            st.stop()

        # ── STEP 3: REDUCE — Merge all summaries ────────────────────────────
        st.markdown("<div class='step-header'>③ REDUCE — Merging summaries into final output</div>", unsafe_allow_html=True)

        merge_placeholder = st.empty()
        merge_placeholder.info("⏳ Merging all chunk summaries into one coherent summary…")

        t0 = time.time()
        try:
            final_summary = merge_summaries(valid_summaries, client, model)
            elapsed = round(time.time() - t0, 1)
            merge_placeholder.empty()

            st.success("✅ Final Summary")
            st.markdown(final_summary)

            # Stats
            st.divider()
            stat_cols = st.columns(4)
            stat_cols[0].metric("Original", f"{len(text_input):,} chars")
            stat_cols[1].metric("Chunks", str(len(chunks)))
            stat_cols[2].metric("Final summary", f"{len(final_summary):,} chars")
            stat_cols[3].metric("Compression", f"{round((1 - len(final_summary)/len(text_input))*100)}%")

            with st.expander("📋 Copy final summary"):
                st.code(final_summary, language=None)

        except Exception as e:
            merge_placeholder.error(f"Merge failed: {e}")
