# Python Fluency Exercises
## Java Developer → FDE / Applied AI Engineer

**Your situation**: You write Java daily. The `ai-project` codebase exists and contains correct Python — but it was written by Claude Code, not by you. Every pattern in it needs to be studied, understood, and reproduced from scratch before you can call it yours. These exercises are the mechanism for that transfer.

**Each exercise follows the same structure**:
1. Read the existing file in `ai-project` — understand every line
2. Identify what is missing or improvable
3. Write the addition yourself, without copying
4. Verify it works

**All exercises target `ai-project` files** — no toy examples.

---

## Quick Reference: What You're Learning and Why

| Pattern | Why It Matters for FDE |
|---|---|
| `@lru_cache` | Expensive init (MeCab, embedding clients) — cache once, reuse forever |
| Async generators | Every streaming LLM response is an async generator |
| `@contextmanager` | Clean resource management — customers write connection leaks constantly |
| `@field_validator` | Pydantic v2 — you will debug customer validation issues every week |
| `@model_validator` | Cross-field validation — most common Pydantic v1→v2 migration question |
| `match/case` | Idiomatic Python 3.10+ — replaces chains of `if/elif` on enum-like values |
| `TypedDict` | Typed internal data shapes without Pydantic overhead |
| `functools.partial` | Pre-configure functions for A/B testing and parameterized pipelines |

---

## Order of Attack

| # | Exercise | Target File | Est. Time | Core Pattern |
|---|---|---|---|---|
| 1 | `@lru_cache` on MeCab tagger | `ai-project/worker/chunking/japanese.py` | 15 min | Memoization |
| 2 | Capstone: streaming script from scratch | `Python_Practice/scripts/stream_anthropic.py` | 30 min | Async generator |
| 3 | `@contextmanager` on psycopg2 | `ai-project/agent/tools/retrieval.py` | 20 min | Resource management |
| 4 | `@field_validator` on ChatRequest | `ai-project/backend/routers/chat.py` | 20 min | Pydantic v2 field validation |
| 5 | `match/case` on stop_reason | `ai-project/agent/loop.py` | 15 min | Pattern matching |
| 6 | `TypedDict` on retrieval rows | `ai-project/agent/tools/retrieval.py` | 15 min | Typed dicts |
| 7 | `functools.partial` chunk variants | `ai-project/worker/chunking/__init__.py` | 10 min | Partial application |
| 8 | `@model_validator` on pagination | `ai-project/backend/routers/documents.py` | 20 min | Cross-field validation |
| 9 | Async generator rewrite (from memory) | blank file | 30 min | Fluency test |

Start with **#1 and #2** — they are independent and together cover the two patterns you will use most.

---

## Exercise 1 — `@lru_cache` on MeCab Tagger

**Target file**: `ai-project/worker/chunking/japanese.py`

**Step 1 — Read first**: Open the file. It currently initializes `tagger = fugashi.Tagger()` at module level. Understand why this is a problem: this line runs at import time, which means the entire worker crashes if MeCab is not installed — even when no Japanese text is ever processed.

**Step 2 — What to add**: Replace the module-level singleton with a lazy-initialized cached function using `@lru_cache`.

```python
# worker/chunking/japanese.py — your version after the exercise
from functools import lru_cache
import fugashi
from models import Chunk


@lru_cache(maxsize=1)
def _get_tagger() -> fugashi.Tagger:
    """
    Initialize MeCab lazily and cache it forever.

    lru_cache(maxsize=1): store exactly one return value.
    - First call:  runs fugashi.Tagger() (~1s), caches the instance.
    - Every subsequent call: returns the cached instance instantly.

    Why not keep the module-level variable?
    - Module-level init runs at import time — crashes if MeCab is absent.
    - @lru_cache init runs on first call — fails only when actually needed.
    """
    return fugashi.Tagger()


def chunk_japanese(text: str, chunk_size: int, overlap: int) -> list[Chunk]:
    tagger = _get_tagger()          # ~1s on first call, instant after
    tokens = [w.surface for w in tagger(text)]
    chunks: list[Chunk] = []
    start = 0
    index = 0
    step = chunk_size - overlap

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(Chunk(
            text="".join(chunk_tokens),
            index=index,
            token_count=len(chunk_tokens),
        ))
        start += step
        index += 1

    return chunks
```

**Step 3 — Verify**:
```python
from worker.chunking.japanese import _get_tagger

_get_tagger()                   # first call — slow (~1s)
_get_tagger()                   # second call — instant
print(_get_tagger.cache_info()) # CacheInfo(hits=1, misses=1, maxsize=1, currsize=1)
```

**Java analogy**: Equivalent to a lazy-initialized `static final` field with double-checked locking — but `@lru_cache` is thread-safe with zero boilerplate.

---

## Exercise 2 — Capstone: Streaming Script from Scratch

**Target file**: `Python_Practice/scripts/stream_anthropic.py` *(write this file yourself)*

**Why this comes second**: Every streaming LLM response in `ai-project` is an async generator — `_redis_sse_stream` in `chat.py`, `stream()` in `llm_client.py`. Before you can claim you understand those files, you need to write the pattern from scratch once.

**Step 1 — Do not read existing code first**. Write this entirely from the description below.

**Step 2 — What to build**:
- An async generator function `token_stream(prompt)` that calls the Anthropic streaming API and yields text chunks
- A `main()` coroutine that consumes the generator and prints each chunk as it arrives
- An `asyncio.run(main())` entrypoint

```python
#!/usr/bin/env python3
"""
Capstone: stream an Anthropic response to stdout, one token at a time.

Usage:
    python scripts/stream_anthropic.py "explain pgvector in 3 sentences"
"""
import asyncio
import sys
import os
import anthropic


async def token_stream(prompt: str):
    """
    Async generator: 'async def' + 'yield' together make this an async generator.
    The caller uses 'async for chunk in token_stream(prompt)' to consume it.
    FastAPI's StreamingResponse does exactly this under the hood.

    Why async?
    The HTTP call to Anthropic is I/O-bound. Without async, the event loop
    blocks while waiting for each chunk — no other requests can be served.
    'yield' suspends this coroutine between chunks, freeing the event loop.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk                     # one token at a time


async def main():
    prompt = " ".join(sys.argv[1:]) or "What is RAG? Answer in one sentence."
    print(f"Prompt: {prompt}\n---")

    chunk_count = 0
    async for chunk in token_stream(prompt):
        print(chunk, end="", flush=True)    # flush=True required for real-time output
        chunk_count += 1

    print(f"\n---\n{chunk_count} chunks received")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 3 — After running it**: Open `ai-project/backend/routers/chat.py` and read `_redis_sse_stream`. You will recognize the identical generator structure — the only difference is that instead of yielding raw text, it wraps chunks in SSE format (`data: ...\n\n`) and reads from Redis instead of the Anthropic API.

**Java analogy**: No direct equivalent. The closest is `Flux<String>` in Project Reactor, but Python's async generator requires no framework — it is a language primitive.

---

## Exercise 3 — `@contextmanager` on psycopg2

**Target file**: `ai-project/agent/tools/retrieval.py`

**Step 1 — Read first**: Find `hybrid_retrieval()` in the file. It opens a psycopg2 connection and calls `conn.close()` in the `finally` block of a try/except. This works — but it mixes resource management with business logic. Every time you need a cursor, the pattern repeats.

**Step 2 — What to add**: Extract the connection lifecycle into a `@contextmanager` and refactor `hybrid_retrieval` to use it.

```python
# Add near the top of agent/tools/retrieval.py, after imports

from contextlib import contextmanager
import psycopg2
import psycopg2.extras


@contextmanager
def _pg_cursor(url: str):
    """
    @contextmanager turns a generator function into a context manager.
    The single 'yield' is the dividing line:
      - Code before yield  = __enter__  (setup)
      - Code after yield   = __exit__   (teardown — runs even on exception)
      - The yielded value  = what 'as cur' receives in the with-block

    Java equivalent:
        try (Connection conn = ds.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            // yield happens here
        }  // conn closed automatically
    """
    conn = psycopg2.connect(url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur               # caller's with-block runs here
    finally:
        conn.close()                # always runs — even on exception


# Refactor the connection block inside hybrid_retrieval:
#
# Before:
#   conn = psycopg2.connect(url)
#   with conn.cursor(...) as cur:
#       cur.execute(...)
#       rows = cur.fetchall()
#   conn.close()
#
# After:
#   with _pg_cursor(url) as cur:
#       cur.execute(...)
#       rows = cur.fetchall()
```

**Key insight**: The `finally` block in a `@contextmanager` is identical in intent to Java's `try-with-resources`. Python's version is explicit, composable, and reusable across any number of functions.

---

## Exercise 4 — `@field_validator` on ChatRequest

**Target file**: `ai-project/backend/routers/chat.py`

**Step 1 — Read first**: Find the `ChatRequest` class. It has two fields — `message: str` and `session_id: str | None` — with no validation. Any string passes, including empty strings and very long inputs.

**Step 2 — What to add**: Two field validators. Write them without copying from anywhere.

```python
# Replace ChatRequest in backend/routers/chat.py

from pydantic import BaseModel, field_validator

MAX_MESSAGE_LENGTH = 8000   # ~2000 tokens


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

    @field_validator("message")
    @classmethod                        # required in Pydantic v2 — omitting this is the #1 v1→v2 mistake
    def message_not_blank(cls, v: str) -> str:
        """
        'v' is the raw field value before it is assigned to the model.
        Whatever you return replaces the original value.
        Raising ValueError causes FastAPI to return HTTP 422 automatically.

        Why @classmethod?
        Pydantic calls this before the model instance exists — there is no
        'self' yet. @classmethod receives 'cls' (the model class) instead.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("message cannot be blank")
        if len(stripped) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"message too long: {len(stripped)} chars (max {MAX_MESSAGE_LENGTH})")
        return stripped     # automatic whitespace trimming for all callers

    @field_validator("session_id")
    @classmethod
    def session_id_valid_uuid(cls, v: str | None) -> str | None:
        """
        Pydantic skips this validator when session_id is None.
        Only runs when a value is actually provided.
        """
        if v is None:
            return v
        import uuid
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError(f"session_id must be a valid UUID, got: {v!r}")
        return v
```

**Step 3 — Verify**: Start the backend and send `POST /api/chat` with `{"message": "   "}`. Confirm you get HTTP 422 with a readable error — not a 500.

**Java analogy**: Equivalent to `@NotBlank` and `@Size` from Jakarta Bean Validation — but defined inline in the class, not via annotation processor.

---

## Exercise 5 — `match/case` on stop_reason

**Target file**: `ai-project/agent/loop.py`

**Step 1 — Read first**: Find the `while` loop inside `agent_loop()`. Locate the stop condition — currently a single `if response.stop_reason != "tool_use": return`. Every non-tool-use reason exits identically: no differentiation between normal completion, truncation, or unexpected values.

**Step 2 — What to change**: Replace the single `if` with a `match/case` block that handles each reason explicitly.

```python
# Inside agent_loop(), replace:
#   if response.stop_reason != "tool_use":
#       return
#
# with:

        match response.stop_reason:
            case "tool_use":
                pass    # continue — tool dispatch runs below

            case "end_turn":
                logger.debug(
                    "agent_loop: finished normally at iteration %d (session=%s)",
                    iteration, session_id,
                )
                return

            case "max_tokens":
                logger.warning(
                    "agent_loop: hit max_tokens at iteration %d — response may be truncated",
                    iteration,
                )
                messages.append({
                    "role": "assistant",
                    "content": (
                        "[Response truncated: max_tokens reached. "
                        "Please ask me to continue or break your task into smaller steps.]"
                    ),
                })
                return

            case "stop_sequence":
                logger.debug("agent_loop: stop sequence triggered at iteration %d", iteration)
                return

            case other:
                # Defensive catch-all — handles unknown values from future API versions
                logger.error(
                    "agent_loop: unexpected stop_reason=%r at iteration %d",
                    other, iteration,
                )
                return
```

**What to understand**:
- `case "tool_use": pass` — explicit no-op; no fall-through like Java switch
- `case other:` — catch-all that binds the unmatched value so you can log it
- Python 3.10+ only — check `python --version` before using

---

## Exercise 6 — `TypedDict` on Retrieval Rows

**Target file**: `ai-project/agent/tools/retrieval.py`

**Step 1 — Read first**: Find the line `rows = cur.fetchall()` inside `hybrid_retrieval()`. The result is `list[dict]` — no type information. Any key access is a blind string lookup. `row["rrf_score"]`, `row["score"]`, `row["rrf"]` — your IDE cannot tell which is correct.

**Step 2 — What to add**: A `TypedDict` at the top of the file, then annotate `rows`.

```python
# Add near the top of agent/tools/retrieval.py, after imports

from typing import TypedDict


class ChunkRow(TypedDict):
    """
    Typed shape of one row from the hybrid retrieval SQL query.

    TypedDict vs Pydantic BaseModel — choose based on trust and cost:
    - TypedDict:  zero runtime overhead; type hints only; no validation.
                  Use for data you generated yourself (your own SQL query).
    - Pydantic:   validates and coerces at runtime; has overhead.
                  Use for external data (user input, third-party API responses).
    """
    id: str
    content: str
    metadata: dict
    rrf_score: float


# Then annotate inside hybrid_retrieval:
#   rows: list[ChunkRow] = cur.fetchall()
#
# Now:
#   row["rrf_score"]   → your IDE knows this is float
#   row["content"]     → your IDE knows this is str
#   row["rrf"]         → mypy / Pylance flags this as an error immediately
```

**Java analogy**: Like a Java `record` or a `Map<String, Object>` with a documented schema. Type-check-time safety without the cost of class instantiation.

---

## Exercise 7 — `functools.partial` for Chunk Size Variants

**Target file**: `ai-project/worker/chunking/__init__.py`

**Step 1 — Read first**: The file calls `chunk_english(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)`. Your Week 4 eval plan requires comparing chunk sizes 256, 512, and 1024. Without `partial`, you need three wrapper functions that differ only in two argument values.

**Step 2 — What to add**: Named chunk-size variants using `partial`.

```python
# worker/chunking/__init__.py — add after the chunk() function

from functools import partial
from chunking.english import chunk_english
from chunking.japanese import chunk_japanese
from config import settings


def chunk(text: str, language: str) -> list:
    if language == "ja":
        return chunk_japanese(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
    return chunk_english(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)


# Pre-configured variants for A/B chunk size evaluation (Week 4 eval plan)
#
# partial(func, keyword=value) returns a new callable with those arguments pre-filled.
# chunk_256("some text") is identical to chunk_english("some text", chunk_size=256, overlap=25)
#
# Java equivalent: a factory method, or a lambda: text -> chunkEnglish(text, 256, 25)
chunk_256  = partial(chunk_english, chunk_size=256,  overlap=25)
chunk_512  = partial(chunk_english, chunk_size=512,  overlap=50)
chunk_1024 = partial(chunk_english, chunk_size=1024, overlap=100)
```

**Step 3 — Use it in your eval script**:
```python
from worker.chunking import chunk_256, chunk_512, chunk_1024

for name, fn in [("256", chunk_256), ("512", chunk_512), ("1024", chunk_1024)]:
    chunks = fn(document_text)
    precision = measure_retrieval_precision(chunks, questions)
    print(f"chunk_size={name}: precision@3={precision:.2f}")
```

---

## Exercise 8 — `@model_validator` on Pagination

**Target file**: `ai-project/backend/routers/documents.py`

**Step 1 — Read first**: Find `list_documents()`. It validates `page` and `per_page` inline with `if page < 1: page = 1` and `if per_page < 1 or per_page > 100: per_page = 20`. This silently corrects bad input instead of rejecting it, and the logic is buried in the handler.

**Step 2 — What to add**: A `ListDocumentsQuery` model that owns its own validation, then inject it into the route.

```python
# Add before the router definition in backend/routers/documents.py

from pydantic import BaseModel, Field, model_validator


class ListDocumentsQuery(BaseModel):
    """
    Query parameters for GET /api/documents.

    When to use @model_validator vs @field_validator:
    - @field_validator: your rule involves exactly one field.
    - @model_validator: your rule involves two or more fields, or the
      relationship between them.
    Here, adding a status filter is a single-field rule — but it's a
    good place to practice the model_validator pattern.
    """
    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    status: str | None = Field(
        default=None,
        description="Filter by document status: processing | ready | failed",
    )

    @model_validator(mode="after")
    def validate_status_value(self) -> "ListDocumentsQuery":
        """
        mode="after": runs after all individual fields are validated and coerced.
        'self' is the model instance — access fields directly as self.status.
        Return self to pass, raise ValueError to reject.

        mode="before": runs on the raw input dict before any field coercion.
        Use "before" only when you need to reshape or rename incoming keys.
        """
        allowed = {"processing", "ready", "failed", None}
        if self.status not in allowed:
            raise ValueError(
                f"status must be one of {allowed - {None}}, got: {self.status!r}"
            )
        return self


# Refactored route:
@router.get("/")
async def list_documents(
    query: ListDocumentsQuery = Depends(),  # Depends() with no args = inject as query params
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> dict[str, Any]:
    await rate_limiter.check(str(user.id))
    offset = (query.page - 1) * query.per_page

    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(query.per_page)
    )
    if query.status:
        stmt = stmt.where(Document.status == query.status)

    result = await db.execute(stmt)
    documents = result.scalars().all()

    return {
        "page": query.page,
        "per_page": query.per_page,
        "documents": [
            {
                "doc_id": str(doc.id),
                "filename": doc.filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "created_at": doc.created_at.isoformat(),
            }
            for doc in documents
        ],
    }
```

---

## Exercise 9 — Async Generator Rewrite (Fluency Test)

**Target file**: a blank file of your choice

**Purpose**: This is not a feature exercise — it is a test of internalization. If you can write `_redis_sse_stream` from memory against a spec, the async generator pattern is yours. If you cannot, go back to Exercise 2.

**Rules**:
1. Do not open `ai-project/backend/routers/chat.py`
2. Do not open this document except to read the spec below
3. Write the function in a blank file
4. Compare with the reference solution only after you finish

**Spec**:
```
Write an async generator: _redis_sse_stream(session_id: str)

1. Get the Redis client from get_redis()
2. Subscribe to pub/sub channel "session:{session_id}"
3. Loop:
   a. Wait for the next message with a 120s timeout using asyncio.wait_for
   b. asyncio.TimeoutError  → yield SSE error event, break
   c. message is None       → yield ": keepalive\n\n", sleep 0.1s, continue
   d. data starts "chunk:"  → yield "data: {text}\n\n"
   e. data == "[DONE]"      → yield "event: done\ndata: [DONE]\n\n", break
4. Always unsubscribe and close pubsub in a finally block
```

**Reference solution** — read only after your attempt:
```python
async def _redis_sse_stream(session_id: str):
    redis = get_redis()
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
                yield "event: error\ndata: Stream timed out\n\n"
                break

            if msg is None:
                yield ": keepalive\n\n"
                await asyncio.sleep(0.1)
                continue

            data = msg["data"].decode() if isinstance(msg["data"], bytes) else msg["data"]

            if data.startswith("chunk:"):
                yield f"data: {data[len('chunk:'):]}\n\n"
            elif data == "[DONE]":
                yield "event: done\ndata: [DONE]\n\n"
                break
    finally:
        await pubsub.unsubscribe(f"session:{session_id}")
        await pubsub.close()
```

**Reflection questions after comparing**:
- Did you use `break` or `return` to exit the loop? (`break` is correct — `return` in a generator raises `StopAsyncIteration` immediately, skipping `finally`)
- Did you remember `finally`? What happens if you omit it?
- Did `yield` feel natural or forced? If forced, redo Exercise 2 first.

---

## Patterns to Study in the Codebase (Not Rewrite Now)

These patterns exist in `ai-project` — read and understand them, but do not prioritize rewriting them until Month 2:

| Pattern | Where | What to understand |
|---|---|---|
| `asyncio.gather` / `asyncio.TaskGroup` | Could be used in tool dispatch | Concurrent coroutines vs sequential |
| `asyncio.Semaphore` | Could be used in embedding calls | Bounding concurrency |
| `threading.Lock` + `Queue` | `agent/loop.py:215` | Why threading (not asyncio) is used here |
| `Protocol` | Could replace duck typing in embedders | Structural typing without inheritance |
| `itertools.chain`, `islice` | Could optimize chunk pipelines | Lazy composition |

---

## Done Criteria

You are fluent when you can do all of the following without looking anything up:

- [ ] Explain `@lru_cache` to a customer in plain English — what it does, when to use it, what the limit means
- [ ] Write an async generator from scratch in under 5 minutes, with correct `finally` cleanup
- [ ] Choose between `@field_validator` and `@model_validator` without hesitating, and explain the difference out loud
- [ ] Write a `@contextmanager` for any resource, and explain why `finally` is in the generator body
- [ ] Use `match/case` fluently and explain why `case other:` is better than a bare `case _:`
- [ ] Explain when `TypedDict` is the right choice over Pydantic `BaseModel`
