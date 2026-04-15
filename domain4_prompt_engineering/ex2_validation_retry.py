"""
Domain 4.4 — Validation-Retry Loop
====================================
Make the model fix its own output by feeding back specific errors.

EXAM FOCUS:
- Append the SPECIFIC validation error to the next prompt, not a generic "try again"
- Generic feedback ("that's wrong, retry") gives the model nothing to act on
- detected_pattern field: tracks which validation rule triggered, useful for
  logging dismissal patterns (e.g. model keeps hitting the same error)
- Max retry limit prevents infinite loops — but the exit condition is validation
  passing, NOT iteration count (iteration cap alone is an anti-pattern)
- Self-review in the same session has limited value: the model retains its
  reasoning context and tends to re-confirm its own output

TASK:
  The model extracts structured data from a receipt. Your validator checks:
    1. total_amount must equal sum of line items (within $0.01)
    2. date must be ISO format YYYY-MM-DD
    3. all item prices must be positive

  Implement validate() and run_extraction_with_retry().
  The retry loop must pass specific error messages back, not generic ones.
"""

import anthropic
import json
import re
from dataclasses import dataclass

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"
MAX_RETRIES = 3

EXTRACT_TOOL = {
    "name": "extract_receipt",
    "description": "Extract structured data from a receipt text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "Purchase date in YYYY-MM-DD format"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"},
                    },
                    "required": ["name", "price"],
                },
            },
            "total_amount": {"type": "number", "description": "Total amount in USD"},
        },
        "required": ["date", "items", "total_amount"],
    },
}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]          # specific, actionable error messages
    detected_patterns: list[str]  # which rule triggered (for logging)


def validate(data: dict) -> ValidationResult:
    """
    Validate the extracted receipt data.
    Return specific error messages (not generic ones).

    TODO: check the 3 rules described in the docstring above.
    Each error message should state exactly what's wrong and what the correct value should be.

    Example of a SPECIFIC error (good):
      "total_amount is 45.00 but sum of items is 42.50 — they must match within $0.01"
    Example of a GENERIC error (bad, don't do this):
      "total is wrong"
    """
    errors = []
    detected_patterns = []

    # TODO: Rule 1 — total_amount vs sum of items
    # TODO: Rule 2 — date format YYYY-MM-DD
    # TODO: Rule 3 — all prices positive

    return ValidationResult(valid=len(errors) == 0, errors=errors, detected_patterns=detected_patterns)


def run_extraction_with_retry(receipt_text: str) -> dict:
    """
    Extract and validate with up to MAX_RETRIES correction attempts.

    On failure: append specific errors to the conversation and retry.
    On success: return the validated data.
    On max retries exceeded: raise ValueError with the last errors.

    TODO: implement the retry loop.

    ANTI-PATTERN — do NOT do this:
        for i in range(MAX_RETRIES):
            result = extract(...)
            # no validation, just hope it's right

    ANTI-PATTERN — do NOT do this on retry:
        messages.append({"role": "user", "content": "That's wrong, please try again"})
        # gives the model nothing to act on
    """
    messages = [
        {"role": "user", "content": f"Extract the receipt data from this text:\n\n{receipt_text}"}
    ]

    for attempt in range(MAX_RETRIES + 1):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_receipt"},
            messages=messages,
        )

        # Extract the tool call input
        tool_block = next((b for b in response.content if b.type == "tool_use"), None)
        if not tool_block:
            raise ValueError("Model did not call extract_receipt")

        data = tool_block.input
        result = validate(data)

        if result.valid:
            print(f"  Validated on attempt {attempt + 1}")
            return data

        if attempt == MAX_RETRIES:
            raise ValueError(f"Extraction failed after {MAX_RETRIES} retries. Last errors: {result.errors}")

        # TODO: append assistant turn and a user turn with SPECIFIC error feedback
        # The error message must include result.errors — not a generic "try again"
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": "TODO: construct specific error feedback here"  # TODO: fix this
        })

    raise ValueError("Should not reach here")


# --- Run ----------------------------------------------------------------------

RECEIPT_WITH_ERRORS = """
Receipt - Jan 5 2025
Coffee: $4.50
Sandwich: $12.00
Cookie: $3.00
Total: $22.00
"""
# The total is wrong (should be $19.50). The date is not ISO format.

RECEIPT_VALID = """
Receipt - 2025-01-05
Coffee: $4.50
Sandwich: $12.00
Cookie: $3.00
Total: $19.50
"""

if __name__ == "__main__":
    print("=== Receipt with errors (model must self-correct) ===")
    try:
        data = run_extraction_with_retry(RECEIPT_WITH_ERRORS)
        print(json.dumps(data, indent=2))
    except ValueError as e:
        print(f"Failed: {e}")

    print("\n=== Valid receipt (should pass first try) ===")
    data = run_extraction_with_retry(RECEIPT_VALID)
    print(json.dumps(data, indent=2))
