"""
Domain 1.2–1.3 — Hub-and-Spoke Multi-Agent Architecture
=========================================================
Build a coordinator that delegates to two specialised subagents.

EXAM FOCUS:
- Hub-and-spoke beats flat multi-agent for complex tasks because:
    * coordinator controls context passed to each subagent (isolation)
    * subagents don't need to know about each other
    * coordinator merges results before the next step
- The Task tool requires 'Task' in allowedTools
- Subagents receive only the context they need — do NOT dump the full
  conversation into every subagent prompt (anti-pattern)

ARCHITECTURE:
  Coordinator
    ├─ ResearchAgent  — given a topic, returns 3 key facts
    └─ SummaryAgent   — given facts, returns a 2-sentence summary

TASK:
  1. Implement run_subagent() — a minimal single-turn agent call
  2. Implement run_coordinator() — calls research then summary, passing
     only the necessary output between them
  3. The coordinator must NOT pass its full message history to subagents
"""

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"


# --- Subagent runner ----------------------------------------------------------

def run_subagent(system_prompt: str, user_message: str) -> str:
    """
    Single-turn subagent. Returns the text response.
    Each subagent gets its own fresh context — no shared history.

    TODO: call client.messages.create with the given system + user message.
    Return the text content of the response.
    """
    # TODO: implement
    raise NotImplementedError


# --- Coordinator --------------------------------------------------------------

def run_coordinator(topic: str) -> str:
    """
    Orchestrates research → summary pipeline.

    Step 1: Call ResearchAgent with only the topic.
    Step 2: Call SummaryAgent with only the research output (not the topic or history).
    Step 3: Return the summary.

    ANTI-PATTERN — do NOT do this:
        history = [all previous messages]
        subagent_response = run_subagent("...", str(history))  # leaking full context
    """
    research_system = (
        "You are a research assistant. Given a topic, return exactly 3 concise facts "
        "as a numbered list. No preamble."
    )
    summary_system = (
        "You are an editor. Given a list of facts, write a 2-sentence summary "
        "suitable for a general audience. No bullet points."
    )

    # TODO: Step 1 — call ResearchAgent with topic only
    facts = ...

    # TODO: Step 2 — call SummaryAgent with facts only (not topic, not history)
    summary = ...

    return summary


# --- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    result = run_coordinator("quantum computing")
    print(result)
