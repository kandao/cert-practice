"""
Domain 2.2–2.3 — Structured Tool Error Responses
==================================================
Return errors in a structured way so the model can reason about them.

EXAM FOCUS:
- Tool results can signal errors via content fields, not just exceptions
- Key fields: isError, errorCategory, isRetryable
- isRetryable=True → model may retry with different inputs
- isRetryable=False → model should escalate or inform user, not retry
- Generic error strings ("something went wrong") give the model nothing to act on
- Structured errors let the model choose the right recovery path

ERROR CATEGORIES (use these consistently):
  "invalid_input"    — caller passed bad data, retrying same input won't help
  "not_found"        — resource doesn't exist
  "rate_limited"     — transient, retry after delay
  "permission_denied"— caller lacks access, retrying won't help
  "upstream_error"   — external service failed, may be transient

TASK:
  1. Implement each tool function to return a structured result dict
  2. Implement run_agent() with an agentic loop
  3. Observe: the model retries rate_limited errors but not invalid_input errors
"""

import anthropic
import json
import time

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

# Simulate a call counter for rate limiting
_call_count = {"lookup_user": 0}

TOOLS = [
    {
        "name": "lookup_user",
        "description": (
            "Looks up a user by ID. ID must be a positive integer. "
            "Returns user details on success. "
            "May return rate_limited error on high traffic — wait and retry. "
            "Returns not_found if the user does not exist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "description": "Positive integer user ID"}
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "send_email",
        "description": "Sends an email to a user. Requires a valid email address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_email": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to_email", "subject", "body"],
        },
    },
]


# --- Tool implementations -----------------------------------------------------

def lookup_user(user_id: int) -> dict:
    """
    Returns a structured result. Three scenarios:
    - user_id <= 0      → invalid_input, not retryable
    - user_id == 999    → rate_limited, retryable (first call only)
    - user_id == 404    → not_found, not retryable
    - otherwise         → success

    TODO: implement returning structured dicts like:
    Success:  {"success": True, "user": {"id": user_id, "name": "...", "email": "..."}}
    Error:    {"isError": True, "errorCategory": "...", "isRetryable": bool, "message": "..."}
    """
    _call_count["lookup_user"] += 1

    # TODO: handle user_id <= 0 → invalid_input, isRetryable=False
    # TODO: handle user_id == 999 AND first call → rate_limited, isRetryable=True
    # TODO: handle user_id == 404 → not_found, isRetryable=False
    # TODO: handle normal case → success
    raise NotImplementedError


def send_email(to_email: str, subject: str, body: str) -> dict:
    """
    Returns structured result.
    - Missing '@' in email → invalid_input, not retryable
    - Otherwise → success

    TODO: implement
    """
    raise NotImplementedError


def dispatch_tool(name: str, tool_input: dict) -> str:
    """Dispatch and return result as JSON string for the model."""
    if name == "lookup_user":
        result = lookup_user(**tool_input)
    elif name == "send_email":
        result = send_email(**tool_input)
    else:
        result = {"isError": True, "errorCategory": "invalid_input", "isRetryable": False, "message": f"Unknown tool: {name}"}
    return json.dumps(result)


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
                result_str = dispatch_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })
            messages.append({"role": "user", "content": tool_results})


# --- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Valid user lookup ===")
    print(run_agent("Look up user 42 and send them a welcome email"))

    print("\n=== Invalid user ID ===")
    print(run_agent("Look up user -5"))

    print("\n=== Rate limited (user 999) ===")
    _call_count["lookup_user"] = 0  # reset
    print(run_agent("Look up user 999"))
