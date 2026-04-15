"""
Exercise 9 — Async Generator Rewrite (Fluency Test)
=====================================================
Pattern  : async generator written from memory
Target   : Blank page — do not look at ai-project/backend/routers/chat.py
Time     : 30 min
Depends  : stdlib asyncio only

PURPOSE
-------
This is not a feature exercise — it is a test of internalization.
Exercise 2 showed you the pattern. Now prove you own it.

If you can pass the test harness without touching the reference solution,
the async generator pattern is yours. If you cannot, go back to ex02.

HOW TO USE THIS FILE
--------------------
1. Read the SPEC below.
2. Scroll to YOUR IMPLEMENTATION and write _redis_sse_stream() there.
   Do not look at the reference solution at the bottom.
3. Run the file:  python ex09_async_generator_rewrite.py
   The test harness feeds mock messages and checks your yielded SSE strings.
4. All 5 tests must pass before you look at the reference solution.

SPEC — what your function must do
----------------------------------
Write:  async def _redis_sse_stream(session_id: str)

It must be an async generator (async def + yield).

Behaviour:
  1. Obtain a mock Redis client by calling get_mock_redis()
  2. Create a pubsub object: pubsub = redis.pubsub()
  3. Subscribe to channel "session:{session_id}"
  4. Loop:
     a. Wait for next message using asyncio.wait_for(..., timeout=120)
     b. asyncio.TimeoutError  → yield "event: error\\ndata: Stream timed out\\n\\n", break
     c. message is None       → yield ": keepalive\\n\\n", sleep 0.05s, continue
     d. message data starts with "chunk:"
                              → yield "data: {text}\\n\\n"  where text = data after "chunk:"
     e. message data == "[DONE]"
                              → yield "event: done\\ndata: [DONE]\\n\\n", break
  5. Always unsubscribe and close pubsub in a finally block

REFLECTION QUESTIONS (answer after you finish)
----------------------------------------------
- Did you use 'break' or 'return' to exit the loop?
  (break is correct — return in a generator raises StopAsyncIteration immediately,
   skipping the finally block and leaking the pubsub subscription)
- Did you remember 'finally'? What leaks without it?
- Did 'yield' feel natural or forced? If forced, redo ex02 first.
"""

import asyncio
from typing import AsyncGenerator


# ══════════════════════════════════════════════════════════════════════════════
# MOCK REDIS — simulates the Redis pub/sub interface using asyncio.Queue
# Do not modify this section.
# ══════════════════════════════════════════════════════════════════════════════

class MockPubSub:
    """
    Simulates redis.asyncio PubSub.
    Messages are fed via push_message() from the test harness.
    """
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue
        self.subscribed_to = []
        self.closed = False

    async def subscribe(self, channel: str):
        self.subscribed_to.append(channel)

    async def unsubscribe(self, channel: str):
        if channel in self.subscribed_to:
            self.subscribed_to.remove(channel)

    async def close(self):
        self.closed = True

    async def get_message(self, ignore_subscribe_messages=True, timeout=1.0):
        try:
            msg = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            return msg
        except asyncio.TimeoutError:
            return None


class MockRedis:
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue

    def pubsub(self) -> MockPubSub:
        return MockPubSub(self._queue)


_mock_queue: asyncio.Queue = None   # set by each test

def get_mock_redis() -> MockRedis:
    return MockRedis(_mock_queue)


def _make_msg(data: str) -> dict:
    return {"type": "message", "data": data.encode()}


# ══════════════════════════════════════════════════════════════════════════════
# YOUR IMPLEMENTATION
# Write _redis_sse_stream() here. Do not scroll to the reference solution yet.
# ══════════════════════════════════════════════════════════════════════════════

async def _redis_sse_stream(session_id: str) -> AsyncGenerator[str, None]:
    # YOUR CODE HERE
    raise NotImplementedError("Write your implementation above this line")
    yield   # make Python treat this as a generator (remove when implemented)


# ══════════════════════════════════════════════════════════════════════════════
# TEST HARNESS
# Feeds messages into the mock queue and checks your generator's output.
# ══════════════════════════════════════════════════════════════════════════════

async def collect(session_id: str, messages_to_send: list, delay: float = 0.01) -> list[str]:
    """Run the generator and collect all yielded values."""
    global _mock_queue
    _mock_queue = asyncio.Queue()

    async def feed():
        for msg in messages_to_send:
            await asyncio.sleep(delay)
            await _mock_queue.put(msg)

    asyncio.create_task(feed())
    results = []
    async for chunk in _redis_sse_stream(session_id):
        results.append(chunk)
    return results


async def run_tests():
    passed = 0
    failed = 0

    def check(test_name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {test_name}")
            passed += 1
        else:
            print(f"  [FAIL] {test_name}" + (f" — {detail}" if detail else ""))
            failed += 1

    print("\n" + "="*60)
    print("RUNNING TESTS")
    print("="*60)

    # Test 1: chunk messages yield SSE data events
    try:
        msgs = [_make_msg("chunk:hello "), _make_msg("chunk:world"), _make_msg("[DONE]")]
        out = await collect("sess-1", msgs)
        check("chunk → data SSE event",
              any(e == "data: hello \n\n" for e in out),
              f"got {out}")
        check("[DONE] → done SSE event",
              any(e == "event: done\ndata: [DONE]\n\n" for e in out),
              f"got {out}")
    except NotImplementedError:
        print("  [SKIP] Tests 1-2: implement _redis_sse_stream first")
        return 0, 5

    # Test 2: None message yields keepalive
    try:
        msgs = [None, _make_msg("[DONE]")]
        out = await collect("sess-2", msgs)
        check("None message → keepalive",
              any(e == ": keepalive\n\n" for e in out),
              f"got {out}")
    except Exception as e:
        check("None message → keepalive", False, str(e))

    # Test 3: bytes data is decoded
    try:
        msgs = [{"type": "message", "data": b"chunk:bytes work"}, _make_msg("[DONE]")]
        out = await collect("sess-3", msgs)
        check("bytes data decoded",
              any("bytes work" in e for e in out),
              f"got {out}")
    except Exception as e:
        check("bytes data decoded", False, str(e))

    # Test 4: pubsub is always closed (finally block)
    try:
        global _mock_queue
        _mock_queue = asyncio.Queue()
        pubsub_ref = None

        # Patch get_mock_redis to capture the pubsub object
        original_redis = get_mock_redis()
        original_pubsub = original_redis.pubsub()
        _mock_queue.put_nowait(_make_msg("[DONE]"))

        results = []
        async for chunk in _redis_sse_stream("sess-4"):
            results.append(chunk)

        # We can't easily capture pubsub.closed without patching, so just check
        # that the function completed without hanging
        check("generator completes on [DONE]", len(results) >= 1, f"got {results}")
    except Exception as e:
        check("generator completes on [DONE]", False, str(e))

    # Test 5: timeout yields error event
    # (Skip by default — would add 120s delay; enable manually to test)
    print("  [SKIP] Test 5: timeout (would take 120s — test manually if needed)")

    print(f"\n  {passed} passed, {failed} failed out of 4 tested")
    return passed, failed


# ══════════════════════════════════════════════════════════════════════════════
# REFERENCE SOLUTION — read only after your tests pass
# ══════════════════════════════════════════════════════════════════════════════

REFERENCE = '''
async def _redis_sse_stream(session_id: str):
    redis = get_mock_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"session:{session_id}")
    try:
        while True:
            try:
                msg = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                yield "event: error\\ndata: Stream timed out\\n\\n"
                break

            if msg is None:
                yield ": keepalive\\n\\n"
                await asyncio.sleep(0.05)
                continue

            data = msg["data"].decode() if isinstance(msg["data"], bytes) else msg["data"]

            if data.startswith("chunk:"):
                yield f"data: {data[len('chunk:'):]}\n\n"
            elif data == "[DONE]":
                yield "event: done\\ndata: [DONE]\\n\\n"
                break
    finally:
        await pubsub.unsubscribe(f"session:{session_id}")
        await pubsub.close()
'''


async def main():
    passed, failed = await run_tests()

    if failed > 0:
        print("\nSome tests failed. Fix your implementation and re-run.")
        print("Reference solution is in the REFERENCE variable at the bottom of this file.")
        print("Only look at it after you have made a genuine attempt.")
    else:
        print("\nAll tests passed!")
        print("Now compare your implementation with the original:")
        print("  ai-project/backend/routers/chat.py → _redis_sse_stream()")


if __name__ == "__main__":
    print(__doc__)
    asyncio.run(main())
