"""
Domain 1.4 — Programmatic Hook Enforcement (PostToolUse)
=========================================================
Implement a hook that intercepts tool results and enforces a business rule
before the model sees the output.

EXAM FOCUS:
- Hooks provide DETERMINISTIC enforcement — the rule always fires, regardless
  of how the model is prompted. This is the key advantage over prompt-based rules.
- Prompt-based guidance is PROBABILISTIC — the model might follow it, might not.
- Use hooks when: compliance, safety rails, data normalisation, audit logging
- Use prompts when: stylistic preferences, soft guidelines
- PostToolUse fires after a tool runs but before the result enters the context

RULE TO ENFORCE:
  If the tool "process_refund" returns an amount > $500, block it and
  return an escalation message instead of the actual result.
  The model should see the escalation message, not the original result.

TASK:
  1. Implement apply_post_tool_use_hook()
  2. Implement the agent loop that uses the hook before appending tool results
  3. Verify: refund of $200 goes through; refund of $800 is blocked
"""

import anthropic
import json
import re

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

REFUND_LIMIT = 500.0

TOOLS = [
    {
        "name": "process_refund",
        "description": "Processes a customer refund. Returns confirmation with amount.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount": {"type": "number", "description": "Refund amount in USD"},
            },
            "required": ["customer_id", "amount"],
        },
    }
]


def process_refund(customer_id: str, amount: float) -> str:
    """Stub tool — always 'succeeds'."""
    return f"Refund of ${amount:.2f} approved for customer {customer_id}. Transaction ID: TXN-{hash(customer_id) % 10000:04d}"


# --- Hook ---------------------------------------------------------------------

def apply_post_tool_use_hook(tool_name: str, tool_input: dict, tool_result: str) -> str:
    """
    PostToolUse hook. Returns the result to pass to the model.
    May return a modified/blocked result instead of the original.

    TODO: if tool_name == "process_refund" and amount > REFUND_LIMIT,
    return an escalation string instead of tool_result.
    Otherwise return tool_result unchanged.

    ANTI-PATTERN — do NOT do this instead:
        system_prompt = "Never approve refunds over $500"  # probabilistic, not guaranteed
    """
    # TODO: implement
    raise NotImplementedError


# --- Agent loop ---------------------------------------------------------------

def run_agent(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next(b.text for b in response.content if hasattr(b, "text"))

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                # Run the actual tool
                raw_result = process_refund(**block.input)

                # TODO: apply the hook — pass raw_result through apply_post_tool_use_hook()
                # Use the hooked result (not raw_result) in tool_results
                final_result = ...  # TODO

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": final_result,
                })

            messages.append({"role": "user", "content": tool_results})


# --- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Small refund ($200) — should go through ===")
    print(run_agent("Please process a $200 refund for customer CUST-001"))

    print("\n=== Large refund ($800) — should be blocked ===")
    print(run_agent("Please process an $800 refund for customer CUST-002"))
