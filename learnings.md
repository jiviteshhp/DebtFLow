# DebtFlow — Prompt Learnings

---

## 2026-04-23 — WILL_PAY warmth fix
**Before:** empathy=0.25, overall=2.33 | **After:** empathy=4.5, overall=7.5
**Learning:** Agent coldest when borrower agreed to pay. One warm sentence = 18x empathy gain.
**Regression:** END goal_progress -3.7, WONT_PAY validity -2.5
**Next:** Rewrite END to stay warm but outcome-focused.

---

## 2026-04-23 — classify_intent timeout
**Fix:** Added timeout=5s, defaults to unclear on failure.
**Learning:** No timeout = 9s p99 latency. Every external call needs a hard limit.
