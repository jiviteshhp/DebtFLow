# DebtFlow — AI Voice Debt Collection Agent

A voice agent that conducts empathetic debt recovery conversations in real time. Built to understand Riverline's stack and engineering philosophy.

**Stack:** Python · Deepgram Nova-2 STT · Groq Llama 3.1 8B · ElevenLabs TTS · Silero VAD · FastAPI · React

---

## What It Does

Priya — an AI loan recovery agent — calls borrowers, understands their situation, and negotiates a payment plan. The conversation is fully voice-driven: speak naturally, get a response in under 800ms.

```
Priya:  "Hello, this is Priya from the bank's loan recovery team. Is this a good time?"
You:    "Yes, but I recently lost my job due to layoffs."
Priya:  "I'm sorry to hear that. What amount could you manage per month, even a small amount?"
You:    "Maybe 2,000 rupees."
Priya:  "That works. When can you make the first payment?"
You:    "20th of this month."
Priya:  "Got it. I'll send you a confirmation shortly. Thank you for working with us."
```

---

## Architecture

### Why a State Machine Over an Agentic Loop

Debt collection conversations follow predictable patterns — greeting, assess, negotiate, close. A deterministic state machine makes every transition explicit, auditable, and traceable. An agentic loop would introduce unpredictability at exactly the moments where consistency matters most (promising a payment date, closing a commitment).

This matches Riverline's philosophy: single agents with clear state over multi-agent swarms unless justified.

```
GREETING → ASSESS → CANT_PAY → NEGOTIATE → WILL_PAY → END
                  → WONT_PAY → OBJECTION → WILL_PAY → END
```

Each state has its own system prompt. The LLM never sees the full conversation logic — it only knows what to do in its current state. Conversation history (last 5 turns) is passed as context so Priya remembers what was said without re-asking.

### Voice Pipeline

```
Mic → PyAudio (device auto-detection) → Deepgram Nova-2 (STT, en-IN, endpointing=500ms)
    → Groq Llama 3.1 8B (LLM, <500ms TTFT)
    → ElevenLabs Anika (TTS, Indian female voice)
    → mpg123 playback
```

**Key decisions:**
- Deepgram `interim_results=True` with `endpointing=500ms` — fast turn detection without cutting off mid-sentence
- Mic muted to Deepgram during TTS playback via `is_muted_fn` — prevents echo and stale transcripts
- Groq and ElevenLabs calls wrapped in `asyncio.to_thread` — blocking API calls never freeze the event loop
- `classify_intent` has a 5s hard timeout — prevents hangs from rate limiting

---

## Eval Infrastructure

The most important part of this project is not the voice agent — it's the measurement system around it.

### LLM-as-Judge

Every conversation turn is scored on three dimensions by a separate Groq call:

| Metric | What It Measures |
|--------|-----------------|
| Empathy | Did the agent acknowledge the borrower's situation? |
| Goal Progress | Did the response move toward a payment commitment? |
| State Validity | Was the response appropriate for this state? |

### Per-State Quality Scores

Scored across 50 simulated conversations:

| State | Count | Empathy | Goal Progress | Validity | Overall |
|-------|-------|---------|---------------|----------|---------|
| assess | 37 | 3.08 | 4.19 | 6.43 | 4.57 |
| cant_pay | 6 | 6.50 | 3.83 | 7.50 | 5.94 |
| negotiate | 2 | 1.00 | 4.50 | 4.00 | 3.17 |
| will_pay | 2 | 4.50 | 9.00 | 9.00 | 7.50 |
| wont_pay | 3 | 2.67 | 2.67 | 4.00 | 3.11 |
| end | 3 | 2.67 | 3.33 | 9.00 | 5.00 |

### Latency Percentiles

| State | p50 | p90 | p99 |
|-------|-----|-----|-----|
| assess | 555ms | 1684ms | 8772ms |
| will_pay | 1575ms | 2760ms | 2760ms |
| end | 416ms | 448ms | 448ms |

p99 assess latency (8772ms) traced to `classify_intent` hanging under rate limits. Fixed by adding a 5s hard timeout with graceful fallback to `unclear`.

### Regression Detection

Baseline scores are frozen in `baseline_scores.json`. Every eval run compares against baseline and flags drops above 1.0 point:

```
── ⚠ REGRESSIONS DETECTED ──
  REGRESSION: END goal_progress dropped 3.7 points (7.0 → 3.33)
  REGRESSION: WONT_PAY state_validity dropped 2.5 points (6.5 → 4.0)
```

This makes prompt changes safe to ship — you know immediately if something regressed.

---

## Key Finding

`will_pay` had empathy=0.25 in the baseline — the agent was coldest exactly when the borrower agreed to pay. That's the worst possible moment to be robotic.

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Empathy | 0.25 | 4.50 | +18x |
| Overall | 2.33 | 7.50 | +5.17 |

One prompt change. Measured, logged, documented. See `learnings.md`.

---

## Prompt Changelog

Every prompt change is logged in `learnings.md` with before/after scores and a learning. Inspired by Riverline's Shaastris system — knowledge that compounds instead of getting lost.

```markdown
## 2026-04-23 — WILL_PAY warmth fix
Before: empathy=0.25, overall=2.33 | After: empathy=4.5, overall=7.5
Learning: Agent coldest when borrower agreed to pay. One warm sentence = 18x empathy gain.
```

---

## Running It

```bash
# Install
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add GROQ_API_KEY, DEEPGRAM_API_KEY, ELEVENLABS_API_KEY

# Run voice agent
python3 voice_agent.py

# Generate simulated conversations
python3 simulate.py

# Run evals (first time — saves baseline)
python3 evals.py baseline

# Run evals (after prompt changes — detects regressions)
python3 evals.py

# Start API + dashboard
uvicorn main:app --reload
cd dashboard && npm start
```

---

## What I'd Build Next

- **Pipecat integration** — replace PyAudio with WebRTC for echo cancellation and SmartTurn for semantic turn detection. Current endpointing is silence-based; SmartTurn understands "I think... um... maybe next week" as incomplete.
- **Whisper fine-tuning** — fine-tune on Indian English debt collection vocabulary. "DPD", "EMI", "PTP" are consistently mistranscribed.
- **promptfoo red-teaming** — adversarial eval suite: borrowers who switch languages mid-call, claim fraud, go silent, or give contradictory answers.
- **SLM distillation** — use LLM-as-judge outputs as training data to distill a smaller, faster classifier. Reduce the classify_intent Groq call to a local model.
- **Cost tracking** — token counts and rupee cost per conversation are already logged. Build the cost-vs-quality scatter plot to find the optimal model size.

---

## Project Structure

```
DebtFlow/
├── voice_agent.py     # main loop — STT → state machine → LLM → TTS
├── state_machine.py   # 8-state FSM + classify_intent
├── agent.py           # per-state Groq prompts + conversation history
├── stt.py             # Deepgram live transcription with mute control
├── tts.py             # ElevenLabs TTS
├── vad.py             # Silero VAD for barge-in detection
├── evals.py           # LLM-as-judge + per-state scores + regression detection
├── simulate.py        # generates 30 test conversations via API
├── main.py            # FastAPI backend
├── logger.py          # conversation logging to JSONL
├── changelog.py       # prompt change tracking
├── learnings.md       # accumulated prompt insights
├── baseline_scores.json  # frozen eval baseline for regression detection
└── dashboard/         # React eval dashboard
```
