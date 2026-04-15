"""
Domain 1.1 — Agentic Loop Lifecycle
=====================================
Build a correct agentic loop that drives tool use until the model is done.

EXAM FOCUS:
- stop_reason == 'tool_use'  → extract tool calls, run them, send results back
- stop_reason == 'end_turn'  → model is done, exit the loop
- NEVER count iterations to decide when to stop (anti-pattern)
- NEVER parse the text output to detect "I'm done" (anti-pattern)

TASK: Implement the loop below. The agent has one tool: get_weather(city: str).
Expected flow:
  User: "What's the weather in Tokyo and Paris?"
  → model calls get_weather("Tokyo")
  → model calls get_weather("Paris")   (may be parallel or sequential)
  → model produces final answer
  → loop exits on end_turn
"""

import anthropic
import json

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

# --- Tool definition -----------------------------------------------------------

TOOLS = [
    {
        "name": "get_weather",
        "description": "Returns current weather for a city. Input must be a city name string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Tokyo'"}
            },
            "required": ["city"],
        },
    }
]


def get_weather(city: str) -> str:
    """Stub — replace with a real API call if you want live data."""
    data = {"Tokyo": "22°C, partly cloudy", "Paris": "15°C, rainy"}
    return data.get(city, f"No data for {city}")


def dispatch_tool(name: str, tool_input: dict) -> str:
    if name == "get_weather":
        return get_weather(tool_input["city"])
    raise ValueError(f"Unknown tool: {name}")


# --- Agent loop ---------------------------------------------------------------

def run_agent(user_message: str) -> str:
    """
    Drive the conversation until stop_reason == 'end_turn'.
    Return the final text response.
    """
    messages = [{"role": "user", "content": user_message}]

    # TODO: implement the loop
    #
    # Skeleton:
    #
    # while True:
    #     response = client.messages.create(...)
    #
    #     if response.stop_reason == "end_turn":
    #         # TODO: extract the text from response.content and return it
    #         ...
    #
    #     if response.stop_reason == "tool_use":
    #         # TODO: find all tool-use blocks in response.content
    #         # TODO: for each, call dispatch_tool() and collect results
    #         # TODO: append the assistant turn and a user turn with tool results
    #         # TODO: continue the loop
    #         ...
    #
    # ANTI-PATTERN — do NOT do this:
    #   for i in range(10):          # arbitrary cap
    #       ...
    #   if "final answer" in text:   # parsing NL to detect done
    #       break
    raise NotImplementedError("Implement the loop")


# --- Run ----------------------------------------------------------------------

if __name__ == "__main__":
    result = run_agent("What's the weather like in Tokyo and Paris right now?")
    print(result)
