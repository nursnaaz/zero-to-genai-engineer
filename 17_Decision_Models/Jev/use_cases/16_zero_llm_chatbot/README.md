# 16 A chatbot with zero LLM calls

**Advanced** | shapes used: `choice, then choice again (video, then chapter)`

Answer questions by POINTING at content you already have. No model writes a word, so it cannot invent an answer.

## Run it

```bash
cd 16_zero_llm_chatbot
python3 chat.py
```

## Data

`data/library.json` - 8 course videos with 3 chapters each.

## How it is tested

8 questions including one deliberately outside the library, which must be refused rather than answered.

## Result when I ran it

8/8 routed correctly, including correctly refusing 'what is the weather in Dubai tomorrow' at 0.98 confidence. Prose tokens generated: 0.

## Worth knowing

The strongest safety story in the set: hallucination is structurally impossible, not merely discouraged.

← [all use cases](../README.md)
