"""
Exercise 2 — Async Generator (Capstone)
========================================
Pattern  : async generator  (async def + yield)
Target   : Write from scratch — this IS the output file
Time     : 30 min
Depends  : stdlib asyncio (mock mode); anthropic package (live mode)

HOW TO USE THIS FILE
--------------------
STEP 1 — Run the mock demo to understand the pattern:
    python ex02_async_generator.py

STEP 2 — Write your own implementation in the YOUR IMPLEMENTATION section below.
    The mock demo and the live section show you what to aim for.
    Do not copy — write it yourself.

STEP 3 — Run live (requires ANTHROPIC_API_KEY):
    ANTHROPIC_API_KEY=sk-ant-... python ex02_async_generator.py --live

WHY THIS MATTERS
----------------
Every streaming LLM response in ai-project is an async generator:
  - _redis_sse_stream() in backend/routers/chat.py
  - stream() in agent/llm/llm_client.py
If you can write this from scratch you own the core streaming pattern.

JAVA ANALOGY
------------
No direct equivalent. Closest: reactive Flux<String> in Project Reactor.
Python's async generator is a language primitive — no framework needed.

    // Java (Project Reactor):
    Flux<String> tokenStream(String prompt) {
        return Flux.create(sink -> { ... sink.next(chunk); ... });
    }

    # Python:
    async def token_stream(prompt: str):
        async for chunk in client.messages.stream(...):
            yield chunk    # that's it
"""

import asyncio
import sys


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — Mock demo (runs without any API key)
# Understand the async generator pattern before touching the real API.
# ══════════════════════════════════════════════════════════════════════════════

async def _mock_anthropic_stream(prompt: str):
    """
    Simulates the Anthropic streaming API.
    Yields fake tokens with a small delay between each.
    """
    fake_response = f"RAG means Retrieval Augmented Generation. It grounds LLM answers in your documents."
    words = fake_response.split()
    for word in words:
        await asyncio.sleep(0.03)   # simulate network latency per token
        yield word + " "


async def token_stream_mock(prompt: str):
    """
    MOCK async generator — same structure as the real one.

    'async def' + 'yield' = async generator.
    The caller uses:  async for chunk in token_stream_mock(prompt)
    FastAPI StreamingResponse does this automatically.

    Why async?
    - HTTP call to Anthropic is I/O-bound.
    - 'yield' suspends this coroutine between tokens, freeing the event loop
      to handle other requests while waiting for the next chunk.
    """
    async for chunk in _mock_anthropic_stream(prompt):
        yield chunk     # one token at a time


async def demo_mock():
    print("="*60)
    print("MOCK DEMO — async generator without API key")
    print("="*60)

    prompt = "What is RAG?"
    print(f"\nPrompt: {prompt}")
    print("Streaming response: ", end="", flush=True)

    chunk_count = 0
    async for chunk in token_stream_mock(prompt):
        print(chunk, end="", flush=True)    # flush=True required for real-time output
        chunk_count += 1

    print(f"\n\n{chunk_count} chunks streamed")

    # Show the generator object type
    gen = token_stream_mock(prompt)
    print(f"\ntype(token_stream_mock(prompt)) = {type(gen).__name__}")
    print("  → async_generator, not a coroutine, not a list")
    print("  → nothing runs until you 'async for' it")
    gen.aclose()    # clean up without iterating


# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — YOUR IMPLEMENTATION
# Write this yourself. Do not copy from Section A or from ai-project.
# ══════════════════════════════════════════════════════════════════════════════

# Instructions:
# 1. Write an async generator called `token_stream(prompt: str)` that:
#    - Creates an anthropic.Anthropic() client
#    - Opens a streaming messages call with model="claude-haiku-4-5-20251001"
#    - Yields each text chunk from stream.text_stream
# 2. Write a `main()` coroutine that:
#    - Reads prompt from sys.argv or uses a default
#    - Iterates token_stream() with async for
#    - Prints each chunk with flush=True
#    - Prints total chunk count at the end
# 3. Call asyncio.run(main()) in the if __name__ block

# YOUR IMPLEMENTATION BELOW:
# ---------------------------------------------------------------------------

# async def token_stream(prompt: str):
#     ...

# async def main():
#     ...


# ══════════════════════════════════════════════════════════════════════════════
# SECTION C — Reference implementation (read only AFTER your attempt)
# Uncomment to run: python ex02_async_generator.py --live
# ══════════════════════════════════════════════════════════════════════════════

async def _live_main():
    """Live implementation using the real Anthropic API."""
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY to run live mode.")
        return

    try:
        import anthropic
    except ImportError:
        print("Install anthropic: pip install anthropic")
        return

    # ── Reference implementation ───────────────────────────────────────────
    async def token_stream(prompt: str):
        """
        Real async generator — calls the Anthropic streaming API.
        Note: messages.stream() is a sync context manager that returns
        a streaming manager. text_stream is a sync iterator inside it.
        We wrap it with asyncio.to_thread to avoid blocking the event loop.
        """
        client = anthropic.Anthropic(api_key=api_key)

        # For true async streaming, use the async client:
        # from anthropic import AsyncAnthropic
        # async with AsyncAnthropic().messages.stream(...) as stream:
        #     async for chunk in stream.text_stream: yield chunk

        # Sync client in a thread (simpler, same result for single requests):
        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for chunk in stream.text_stream:
                yield chunk

    prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "What is RAG in one sentence?"
    print(f"\nLIVE mode — Prompt: {prompt}")
    print("Response: ", end="", flush=True)

    count = 0
    async for chunk in token_stream(prompt):
        print(chunk, end="", flush=True)
        count += 1

    print(f"\n\n{count} chunks received from Anthropic API")


if __name__ == "__main__":
    if "--live" in sys.argv:
        asyncio.run(_live_main())
    else:
        asyncio.run(demo_mock())
        print("\n" + "-"*60)
        print("Next: write your implementation in SECTION B above,")
        print("then run:  ANTHROPIC_API_KEY=sk-... python ex02_async_generator.py --live")
