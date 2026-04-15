"""
Domain 5.1–5.2 — Context Blocks + Escalation Logic
=====================================================
Structure long conversations so the model reliably accesses key facts,
and route escalation based on complexity rather than sentiment.

EXAM FOCUS:
- 'case facts' block: a dedicated section at the top of the system prompt that
  holds stable facts the model must not lose track of (account details, policies)
- Trim verbose tool outputs before adding to context — the model doesn't need
  raw JSON dumps of 500 fields; extract only what matters
- Position-aware ordering: critical info near the top (primacy) or bottom (recency)
  of the context window — NOT buried in the middle ("lost in the middle" effect)
- Escalation rule: escalate on COMPLEXITY (multi-policy, legal, high-value),
  NOT on sentiment (angry customer ≠ complex issue)
- Structured errors give the model enough context to choose the right recovery path

TASK:
  Part A: implement build_system_prompt_with_case_facts()
          The case facts block must appear at the very top.
  Part B: implement should_escalate() using complexity signals, not sentiment.
  Part C: implement trim_tool_output() to keep context tight.
"""

import anthropic
import json

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"


# --- Part A: Case Facts Block -------------------------------------------------

def build_system_prompt_with_case_facts(
    case_facts: dict,
    base_instructions: str,
) -> str:
    """
    Build a system prompt where case_facts appears FIRST, before base_instructions.

    EXAM RULE: put stable, critical facts at the top (primacy effect).
    Burying them after long instructions risks "lost in the middle" degradation.

    case_facts keys: account_id, plan, outstanding_balance, open_tickets, flags

    TODO: format case_facts as a clearly labelled block at the top,
    then append base_instructions below it.

    Example structure:
    ---
    ## Case Facts
    Account: ...
    Plan: ...
    ...
    ---
    <base_instructions>
    """
    # TODO: implement
    raise NotImplementedError


# --- Part B: Escalation Logic -------------------------------------------------

ESCALATION_SIGNALS = {
    "complexity": [
        "multiple_policies_involved",
        "legal_mention",
        "high_value_transaction",   # > $1000
        "data_breach_concern",
        "regulatory_compliance",
    ],
    # ANTI-PATTERN: do NOT escalate on these alone
    "sentiment_only": [
        "angry_tone",
        "frustrated_tone",
        "profanity",
    ],
}


def should_escalate(message: str, account_flags: list[str]) -> tuple[bool, str]:
    """
    Decide whether to escalate to a human agent.
    Returns (should_escalate: bool, reason: str).

    Rules:
    - ESCALATE if any complexity signal is present (in message text OR account_flags)
    - DO NOT escalate on sentiment alone
    - An angry message about a $5 charge → do NOT escalate
    - A polite message mentioning "GDPR violation" → escalate

    TODO: implement keyword detection for complexity signals.
    Return (True, reason) or (False, "handle_in_bot").

    ANTI-PATTERN — do NOT do this:
        if "angry" in sentiment_score or "!" in message:
            escalate()  # escalating on sentiment alone wastes human agents
    """
    raise NotImplementedError


# --- Part C: Trim Tool Output -------------------------------------------------

def trim_tool_output(raw_output: dict, tool_name: str) -> str:
    """
    Reduce a verbose tool response to only what the model needs.

    EXAM RULE: never dump raw API responses into context.
    Extract only the fields the model needs for the next decision.

    Rules per tool:
    - "get_account": keep only id, plan, balance, status. Drop: audit_log, internal_flags, raw_db_row
    - "get_ticket":  keep only id, status, subject, last_updated. Drop: full_history, agent_notes, metadata
    - anything else: keep as-is (unknown tool, don't lose data)

    TODO: implement the trimming logic. Return a compact JSON string.
    """
    raise NotImplementedError


# --- Integration demo ---------------------------------------------------------

def handle_customer_message(message: str, account_id: str) -> str:
    """
    Full flow: build context → check escalation → respond or escalate.
    """
    # Simulated account data (would come from a real tool call)
    account = {
        "account_id": account_id,
        "plan": "Professional",
        "outstanding_balance": 0.0,
        "open_tickets": 2,
        "flags": ["high_value_transaction"],
    }
    raw_account_response = {
        **account,
        "audit_log": ["login 2025-01-01", "login 2025-01-02"],  # noise
        "internal_flags": {"risk_score": 0.1},                   # noise
        "raw_db_row": {"pg_id": 99999},                          # noise
    }

    trimmed = trim_tool_output(raw_account_response, "get_account")

    escalate, reason = should_escalate(message, account["flags"])
    if escalate:
        return f"[ESCALATED TO HUMAN — {reason}]"

    system_prompt = build_system_prompt_with_case_facts(
        case_facts=account,
        base_instructions="You are a helpful customer support agent. Be concise.",
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=[
            {"role": "user", "content": f"Account context (trimmed):\n{trimmed}\n\nCustomer: {message}"}
        ],
    )
    return response.content[0].text


# --- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    cases = [
        ("I'm SO angry about my bill!!!", "ACC-001"),           # angry but simple → no escalate
        ("Can you check on my open tickets?", "ACC-002"),       # normal
        ("This might be a GDPR violation", "ACC-003"),          # complexity signal → escalate
        ("My transaction of $1500 didn't go through", "ACC-004"),  # high_value → escalate
    ]

    for msg, acc_id in cases:
        print(f"\nMessage: {msg[:60]}")
        result = handle_customer_message(msg, acc_id)
        print(f"Result:  {result[:120]}")
