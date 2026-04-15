"""
Exercise 5 — match/case
========================
Pattern  : structural pattern matching (Python 3.10+)
Target   : ai-project/agent/loop.py  →  agent_loop()
Time     : 15 min
Depends  : stdlib only — requires Python >= 3.10

PROBLEM
-------
The agent loop uses a single:
    if response.stop_reason != "tool_use":
        return
All non-tool-use stop reasons are handled identically — no differentiation
between normal completion, truncation, stop sequence, or unknown values.
Nothing is logged, and future API changes (new stop_reason values) are silent.

YOUR TASK
---------
1. Run this script — observe how each stop_reason is routed.
2. Open ai-project/agent/loop.py.
3. Replace the single if-check with the match/case block shown in APPLY_DIFF.

JAVA ANALOGY
------------
switch(stopReason) {
    case "tool_use":    break;
    case "end_turn":    return;
    case "max_tokens":  log.warn(...); return;
    default:            log.error(...); return;
}

Key differences from Java switch:
  - No fall-through — each case is independent (no 'break' needed)
  - 'case other:' binds the unmatched value to a variable (Java default: does not)
  - Works on strings, ints, types, dataclasses, and nested structures
  - Python 3.10+ only
"""

import sys
import logging

logging.basicConfig(level=logging.DEBUG, format="  [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Check Python version
if sys.version_info < (3, 10):
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} detected.")
    print("match/case requires Python 3.10+. Upgrade to continue.")
    sys.exit(1)


# ── Mock response object ──────────────────────────────────────────────────────

class MockResponse:
    def __init__(self, stop_reason: str):
        self.stop_reason = stop_reason
        self.content = []

    def __repr__(self):
        return f"Response(stop_reason={self.stop_reason!r})"


# ── Before: single if-check (the problem) ────────────────────────────────────

def handle_before(response: MockResponse) -> str:
    """Current ai-project code — all non-tool_use reasons treated identically."""
    if response.stop_reason != "tool_use":
        return "exit"
    return "continue"


# ── After: match/case ─────────────────────────────────────────────────────────

def handle_after(response: MockResponse, iteration: int = 1, session_id: str = "sess-1") -> str:
    """
    Improved version using match/case.

    Key syntax:
      case "literal":       match exact value
      case other:           catch-all — binds unmatched value to 'other'
      case "a" | "b":       OR — match either value
      case _ :              wildcard — matches anything, binds nothing

    'case other:' is preferred over 'case _:' when you want to log what was matched.
    """
    match response.stop_reason:
        case "tool_use":
            return "continue"       # no fall-through — just keep going

        case "end_turn":
            logger.debug("finished normally at iteration %d (session=%s)", iteration, session_id)
            return "exit:normal"

        case "max_tokens":
            logger.warning("hit max_tokens at iteration %d — response may be truncated", iteration)
            return "exit:truncated"

        case "stop_sequence":
            logger.debug("stop sequence triggered at iteration %d", iteration)
            return "exit:stop_seq"

        case other:
            # Defensive: new API versions may add stop_reason values we don't know yet
            logger.error("unexpected stop_reason=%r at iteration %d", other, iteration)
            return f"exit:unknown({other})"


# ── Demos ─────────────────────────────────────────────────────────────────────

def demo_comparison():
    print("\n--- Before vs After: handling each stop_reason ---")

    reasons = ["tool_use", "end_turn", "max_tokens", "stop_sequence", "future_reason"]
    print(f"\n  {'stop_reason':<20} {'before':>15}  {'after':>25}")
    print(f"  {'-'*20} {'-'*15}  {'-'*25}")

    for reason in reasons:
        r = MockResponse(reason)
        before = handle_before(r)
        after  = handle_after(r)
        print(f"  {reason:<20} {before:>15}  {after:>25}")


def demo_binding():
    print("\n--- 'case other:' binds the value (unlike Java default:) ---")

    def classify(stop_reason: str) -> str:
        match stop_reason:
            case "tool_use" | "end_turn":
                return "expected"
            case other:
                return f"unexpected value captured: {other!r}"

    for r in ["tool_use", "end_turn", "max_tokens", "xyz"]:
        print(f"  {r!r:<20} → {classify(r)}")


def demo_nested():
    print("\n--- match/case on dict/object structure (advanced — Month 2) ---")
    print("""
  # match/case can destructure dicts and dataclasses:
  match event:
      case {"type": "upload", "file_type": ft}:
          ingest(ft)
      case {"type": "query",  "message": msg}:
          answer(msg)
      case {"type": t}:
          log.warning("unknown event type: %s", t)
  """)


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/agent/loop.py
============================================

Inside agent_loop(), REPLACE:
    if response.stop_reason != "tool_use":
        return

WITH:
    match response.stop_reason:
        case "tool_use":
            pass    # continue — tool dispatch runs below

        case "end_turn":
            logger.debug(
                "agent_loop: finished normally at iteration %d (session=%s)",
                iteration, session_id,
            )
            return

        case "max_tokens":
            logger.warning(
                "agent_loop: hit max_tokens at iteration %d — response may be truncated",
                iteration,
            )
            messages.append({
                "role": "assistant",
                "content": (
                    "[Response truncated: max_tokens reached. "
                    "Please ask me to continue or break your task into smaller steps.]"
                ),
            })
            return

        case "stop_sequence":
            logger.debug("agent_loop: stop sequence triggered at iteration %d", iteration)
            return

        case other:
            logger.error(
                "agent_loop: unexpected stop_reason=%r at iteration %d",
                other, iteration,
            )
            return

NOTE: 'iteration' and 'session_id' are already local variables in agent_loop().
"""


if __name__ == "__main__":
    print(__doc__)
    demo_comparison()
    demo_binding()
    demo_nested()
    print(APPLY_DIFF)
