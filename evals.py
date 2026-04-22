from groq import Groq
import os
import json
import time
from statistics import mean, median, quantiles
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

BASELINE_FILE = "baseline_scores.json"

# ─────────────────────────────────────────────
# PART 1: LLM-as-judge scorer (unchanged core)
# ─────────────────────────────────────────────
# This is the same judge you had before.
# We use Groq to score each turn on 3 dimensions.
# The judge is a different model evaluating the agent — separation of concerns.

def score_conversation(state: str, borrower_input: str, agent_response: str) -> dict:
    prompt = f"""You are evaluating a debt collection AI agent. Score the agent response on three criteria, each 0-10.

State: {state}
Borrower said: {borrower_input}
Agent responded: {agent_response}

Score:
1. Empathy (0-10): Did the agent acknowledge the borrower's situation with warmth?
2. Goal Progress (0-10): Did the response move toward a payment commitment?
3. State Validity (0-10): Was the response appropriate for this state in the conversation?

Reply in JSON only:
{{"empathy": 0, "goal_progress": 0, "state_validity": 0}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip()
    # strip markdown fences if model adds them
    raw = raw.replace("```json", "").replace("```", "").strip()
    scores = json.loads(raw)
    scores["overall"] = round((scores["empathy"] + scores["goal_progress"] + scores["state_validity"]) / 3, 2)
    return scores


# ─────────────────────────────────────────────
# PART 2: Per-state aggregation
# ─────────────────────────────────────────────
# Why: one overall number hides which specific state is broken.
# "Overall score: 6.8" tells you nothing.
# "CANT_PAY goal_progress: 4.2" tells you exactly what to fix.

def aggregate_by_state(scored_turns: list[dict]) -> dict:
    """
    Groups scored turns by state and computes mean + median for each metric.
    scored_turns: list of dicts with keys: state, empathy, goal_progress, state_validity, overall, latency_ms
    """
    by_state: dict = {}

    for t in scored_turns:
        s = t["state"]
        if s not in by_state:
            by_state[s] = {
                "empathy": [], "goal_progress": [],
                "state_validity": [], "overall": [], "latency_ms": []
            }
        by_state[s]["empathy"].append(t["empathy"])
        by_state[s]["goal_progress"].append(t["goal_progress"])
        by_state[s]["state_validity"].append(t["state_validity"])
        by_state[s]["overall"].append(t["overall"])
        by_state[s]["latency_ms"].append(t["latency_ms"])

    result = {}
    for state, metrics in by_state.items():
        result[state] = {
            "count": len(metrics["overall"]),
            "empathy":       round(mean(metrics["empathy"]), 2),
            "goal_progress": round(mean(metrics["goal_progress"]), 2),
            "state_validity":round(mean(metrics["state_validity"]), 2),
            "overall":       round(mean(metrics["overall"]), 2),
        }
    return result


# ─────────────────────────────────────────────
# PART 3: Latency percentiles per state
# ─────────────────────────────────────────────
# Why percentiles instead of mean:
#   Mean latency = 700ms sounds fine.
#   But p99 = 3400ms means 1 in 100 turns feels completely broken.
#   In a real conversation that 1 turn kills the experience.
# p50 = typical, p90 = bad day, p99 = worst case.

def latency_percentiles_by_state(scored_turns: list[dict]) -> dict:
    by_state: dict = {}
    for t in scored_turns:
        s = t["state"]
        if s not in by_state:
            by_state[s] = []
        by_state[s].append(t["latency_ms"])

    result = {}
    for state, latencies in by_state.items():
        latencies.sort()
        n = len(latencies)
        result[state] = {
            "count": n,
            "p50":  round(median(latencies)),
            # quantiles needs at least 4 values for quartiles
            # for p90/p99 we index directly
            "p90":  round(latencies[int(n * 0.90)] if n >= 10 else latencies[-1]),
            "p99":  round(latencies[int(n * 0.99)] if n >= 100 else latencies[-1]),
            "mean": round(mean(latencies)),
        }
    return result


# ─────────────────────────────────────────────
# PART 4: Regression detection
# ─────────────────────────────────────────────
# Why: every time you change a prompt, you want to know immediately
# if quality dropped. Without a baseline you're flying blind.
#
# First run: saves current scores as baseline_scores.json
# Every subsequent run: compares against baseline, flags drops > threshold
#
# This maps directly to the JD: "roll back instantly and measure net impact"

REGRESSION_THRESHOLD = 1.0  # flag if any metric drops more than 1 point

def save_baseline(state_scores: dict):
    with open(BASELINE_FILE, "w") as f:
        json.dump(state_scores, f, indent=2)
    print(f"Baseline saved to {BASELINE_FILE}")

def load_baseline() -> dict | None:
    if not os.path.exists(BASELINE_FILE):
        return None
    with open(BASELINE_FILE, "r") as f:
        return json.load(f)

def detect_regressions(current: dict, baseline: dict) -> list[str]:
    """
    Compares current per-state scores against baseline.
    Returns list of regression warning strings.
    """
    warnings = []
    metrics = ["empathy", "goal_progress", "state_validity", "overall"]

    for state, curr_scores in current.items():
        if state not in baseline:
            continue  # new state, no baseline to compare
        base_scores = baseline[state]
        for m in metrics:
            if m not in curr_scores or m not in base_scores:
                continue
            drop = base_scores[m] - curr_scores[m]
            if drop > REGRESSION_THRESHOLD:
                warnings.append(
                    f"REGRESSION: {state.upper()} {m} dropped {drop:.1f} points "
                    f"({base_scores[m]} → {curr_scores[m]})"
                )
    return warnings


# ─────────────────────────────────────────────
# PART 5: Main runner — ties everything together
# ─────────────────────────────────────────────

def run_evals(save_as_baseline: bool = False):
    """
    Reads conversations.jsonl, scores every turn, aggregates by state,
    computes latency percentiles, detects regressions.

    Pass save_as_baseline=True to freeze current scores as the new baseline.
    """
    with open("conversations.jsonl", "r") as f:
        turns = [json.loads(line) for line in f if line.strip()]

    # sample to 50 turns max — enough for per-state stats, avoids 6min runs
    import random
    if len(turns) > 50:
        turns = random.sample(turns, 50)

    print(f"\nRunning evals on {len(turns)} turns...\n")

    scored = []
    for i, turn in enumerate(turns):
        try:
            scores = score_conversation(
                turn["state"],
                turn["borrower_input"],
                turn["agent_response"]
            )
            scored.append({
                "call_id":    turn["call_id"],
                "state":      turn["state"],
                "latency_ms": turn.get("latency_ms", 0),
                **scores
            })
            time.sleep(2)  # 30 RPM limit = 1 request per 2s
            if (i + 1) % 10 == 0:
                print(f"  Scored {i+1}/{len(turns)} turns...")
        except Exception as e:
            print(f"  Skipping turn {i}: {e}")

    # ── Per-state score breakdown ──
    state_scores = aggregate_by_state(scored)
    print("\n── Per-State Quality Scores ──")
    print(f"{'State':<14} {'Count':>5} {'Empathy':>8} {'Goal Prog':>10} {'Validity':>9} {'Overall':>8}")
    print("─" * 60)
    for state, s in sorted(state_scores.items()):
        print(f"{state:<14} {s['count']:>5} {s['empathy']:>8} {s['goal_progress']:>10} {s['state_validity']:>9} {s['overall']:>8}")

    # ── Latency percentiles ──
    latency = latency_percentiles_by_state(scored)
    print("\n── Latency Percentiles by State (ms) ──")
    print(f"{'State':<14} {'Count':>5} {'p50':>6} {'p90':>6} {'p99':>6} {'mean':>6}")
    print("─" * 50)
    for state, l in sorted(latency.items()):
        print(f"{state:<14} {l['count']:>5} {l['p50']:>6} {l['p90']:>6} {l['p99']:>6} {l['mean']:>6}")

    # ── Regression detection ──
    baseline = load_baseline()
    if baseline:
        regressions = detect_regressions(state_scores, baseline)
        if regressions:
            print("\n── ⚠ REGRESSIONS DETECTED ──")
            for w in regressions:
                print(f"  {w}")
        else:
            print("\n── No regressions vs baseline ──")
    else:
        print("\n── No baseline found — run with save_as_baseline=True to create one ──")

    # ── Save baseline if requested ──
    if save_as_baseline:
        save_baseline(state_scores)

    return scored, state_scores


if __name__ == "__main__":
    import sys
    # python evals.py          → run evals, compare against baseline
    # python evals.py baseline → run evals AND save as new baseline
    save = len(sys.argv) > 1 and sys.argv[1] == "baseline"
    run_evals(save_as_baseline=save)
