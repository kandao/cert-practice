"""
Domain 2.1 — Tool Description Best Practices
=============================================
Write tool schemas that guide the model reliably. Compare good vs bad.

EXAM FOCUS:
- Tool descriptions must specify: input format, units, edge cases, examples
- Vague descriptions produce semantic errors even when the schema is valid
- 4–5 tools per agent max — more than that degrades selection accuracy
- Required vs optional fields: only mark required what truly is required
- Enums: always include an 'other' value with a companion detail field
  so the model isn't forced to pick a wrong category

TASK:
  Part A — fix the BAD tool schemas below. Each has a specific problem.
  Part B — call the API with both versions on the same prompt and compare
           whether the model calls the tool correctly.
"""

import anthropic
import json

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"


# =============================================================================
# Part A — Fix the bad schemas
# =============================================================================

# --- Tool 1: Unit ambiguity ---------------------------------------------------
# PROBLEM: 'amount' has no unit specified. Model may pass dollars, cents, or yen.
BAD_TOOL_CONVERT_CURRENCY = {
    "name": "convert_currency",
    "description": "Converts currency.",
    "input_schema": {
        "type": "object",
        "properties": {
            "amount": {"type": "number"},
            "from_currency": {"type": "string"},
            "to_currency": {"type": "string"},
        },
        "required": ["amount", "from_currency", "to_currency"],
    },
}

# TODO: fix by specifying unit, format, and an example in the description
GOOD_TOOL_CONVERT_CURRENCY = {
    "name": "convert_currency",
    "description": "TODO — add unit (USD whole dollars), format, and one example",
    "input_schema": BAD_TOOL_CONVERT_CURRENCY["input_schema"],  # schema can stay the same
}


# --- Tool 2: Enum without 'other' ---------------------------------------------
# PROBLEM: category enum has no escape hatch. Model is forced into a wrong bucket.
BAD_TOOL_FILE_TICKET = {
    "name": "file_support_ticket",
    "description": "Files a customer support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["billing", "technical", "shipping"],
            },
        },
        "required": ["description", "category"],
    },
}

# TODO: add "other" to the enum and a companion "category_detail" optional field
GOOD_TOOL_FILE_TICKET = {
    "name": "file_support_ticket",
    "description": "TODO",
    "input_schema": {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["billing", "technical", "shipping"],  # TODO: add "other"
            },
            # TODO: add category_detail optional field
        },
        "required": ["description", "category"],
    },
}


# --- Tool 3: Missing edge-case handling in description -----------------------
# PROBLEM: no guidance on what to pass when the city is unknown / ambiguous.
BAD_TOOL_WEATHER = {
    "name": "get_weather",
    "description": "Gets weather for a location.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "country_code": {"type": "string"},
        },
        "required": ["city"],
    },
}

# TODO: describe format (full name not abbreviation), when to include country_code,
#       and what to do if the city is ambiguous (e.g. "Springfield")
GOOD_TOOL_WEATHER = {
    "name": "get_weather",
    "description": "TODO",
    "input_schema": BAD_TOOL_WEATHER["input_schema"],
}


# =============================================================================
# Part B — Compare behaviour
# =============================================================================

def call_with_tool(tool: dict, prompt: str) -> dict | None:
    """Returns the tool_use block if the model called the tool, else None."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=[tool],
        messages=[{"role": "user", "content": prompt}],
    )
    for block in response.content:
        if block.type == "tool_use":
            return {"name": block.name, "input": block.input}
    return None


if __name__ == "__main__":
    # Test 1 — does the model include units in convert_currency?
    prompt1 = "Convert 50 dollars to euros"
    print("BAD schema result:", call_with_tool(BAD_TOOL_CONVERT_CURRENCY, prompt1))
    print("GOOD schema result:", call_with_tool(GOOD_TOOL_CONVERT_CURRENCY, prompt1))

    # Test 2 — does the model pick a wrong category or use 'other'?
    prompt2 = "I need help with a damaged item I received"  # doesn't fit billing/technical/shipping cleanly
    print("\nBAD schema result:", call_with_tool(BAD_TOOL_FILE_TICKET, prompt2))
    print("GOOD schema result:", call_with_tool(GOOD_TOOL_FILE_TICKET, prompt2))
