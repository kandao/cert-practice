"""
Domain 4.1–4.2 — Few-Shot Prompting + tool_choice
===================================================
Measure the impact of examples on ambiguous classification,
then compare tool_choice: auto vs any vs forced.

EXAM FOCUS:
- Few-shot: 2–4 examples for ambiguous cases; more than 5 has diminishing returns
- Placement: examples belong in the system prompt (consistent framing), not user turn
- tool_choice options:
    "auto"   → model decides whether to call a tool (may respond in text instead)
    "any"    → model MUST call one of the available tools
    {"type": "tool", "name": "X"} → model MUST call tool X specifically
- JSON schema tool_use gives guaranteed structural compliance, not semantic correctness

TASK:
  Part A: implement zero_shot_classify() and few_shot_classify()
          Compare results on the ambiguous cases below.
  Part B: implement three versions of ask_for_data() using each tool_choice mode.
          Observe when the model responds in text vs calls the tool.
"""

import anthropic
import json

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

# --- Part A: Few-shot classification ------------------------------------------

CATEGORIES = ["urgent", "normal", "low_priority"]

# Ambiguous tickets that are hard to classify without examples
AMBIGUOUS_TICKETS = [
    "Hi, just checking in on my ticket from last week",  # polite but might be urgent
    "The system is running a bit slow today",            # performance issue — urgent or normal?
    "FYI the export button doesn't work in Safari",     # bug, but vague severity
]

EXAMPLES = [
    # (ticket_text, correct_category)
    ("Production database is down, no one can log in", "urgent"),
    ("Could you update my email address when you get a chance?", "low_priority"),
    ("Users are reporting 500 errors on checkout — happening now", "urgent"),
    ("Feature request: add dark mode", "low_priority"),
]


def zero_shot_classify(ticket: str) -> str:
    """
    Classify without examples. Use tool_use to enforce structured output.
    tool_choice = {"type": "tool", "name": "classify"} to force the call.

    TODO: define a "classify" tool with a "category" enum field,
    call the API with tool_choice forced to "classify", return the category string.
    """
    tool = {
        "name": "classify",
        "description": "Classify a support ticket into a priority category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": CATEGORIES},
                "reasoning": {"type": "string"},
            },
            "required": ["category", "reasoning"],
        },
    }
    # TODO: implement
    raise NotImplementedError


def few_shot_classify(ticket: str) -> str:
    """
    Classify WITH examples in the system prompt.
    Same tool, same tool_choice — only the system prompt changes.

    TODO: build a system prompt that includes the EXAMPLES above,
    formatted as: "Input: <ticket>\nOutput: <category>"
    """
    # TODO: build system_prompt from EXAMPLES
    # TODO: call zero_shot_classify logic but with the system_prompt injected
    raise NotImplementedError


# --- Part B: tool_choice modes ------------------------------------------------

DATA_TOOL = {
    "name": "get_user_data",
    "description": "Retrieves user profile data by user ID.",
    "input_schema": {
        "type": "object",
        "properties": {"user_id": {"type": "string"}},
        "required": ["user_id"],
    },
}


def ask_auto(prompt: str) -> str:
    """tool_choice='auto' — model decides. May answer in text without calling tool."""
    # TODO: implement. Return "TOOL_CALLED" if tool_use in response, else the text response.
    raise NotImplementedError


def ask_any(prompt: str) -> str:
    """tool_choice='any' — model must call one of the available tools."""
    # TODO: implement
    raise NotImplementedError


def ask_forced(prompt: str) -> str:
    """tool_choice forces get_user_data specifically."""
    # TODO: implement with tool_choice={"type": "tool", "name": "get_user_data"}
    raise NotImplementedError


# --- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Part A: Few-Shot Impact ===")
    for ticket in AMBIGUOUS_TICKETS:
        z = zero_shot_classify(ticket)
        f = few_shot_classify(ticket)
        match = "✓" if z == f else "DIFF"
        print(f"[{match}] zero={z:15s} few={f:15s} | {ticket[:60]}")

    print("\n=== Part B: tool_choice Modes ===")
    # This prompt is ambiguous — the model might answer from memory instead of calling the tool
    vague = "Tell me about user 42"
    print(f"auto:   {ask_auto(vague)}")
    print(f"any:    {ask_any(vague)}")
    print(f"forced: {ask_forced(vague)}")
