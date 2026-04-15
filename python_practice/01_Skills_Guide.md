# Python Skills Guide
## Java Developer → FDE / Applied AI Engineer

**Your situation**: You write Java daily. The `ai-project` codebase was built with Claude Code — the Python patterns in it are correct, but they are not yours yet. You need to be able to read, explain, reproduce, and debug every pattern in that codebase without assistance. As an FDE you will write Python in live customer workshops, review customer code on the spot, and debug unfamiliar codebases in real time. That requires ownership, not familiarity.

**How to use this**: For each section, find where the pattern appears in `ai-project`, read it until you understand every line, then close the file and rewrite it from memory. The goal is that you could explain it out loud to a customer's engineering team.

---

## Patterns in Your Codebase to Study and Own

These patterns exist in `ai-project` — written by Claude Code, not by you. Each one will come up in customer work. Study them until you can reproduce and explain them without reference.

| Pattern | Where to find it | What to be able to do |
|---|---|---|
| `async/await` and `asyncio.to_thread` | `agent/loop.py:389` | Explain why `to_thread` is used and what breaks without it |
| `async with pool.acquire()` | `worker/storage.py:49` | Explain connection pool lifecycle and what leaks without `async with` |
| List comprehensions with `zip` | `worker/storage.py:36` | Rewrite as a for-loop and back; explain memory difference |
| Type hints (`list[Chunk]`, `asyncpg.Pool`) | Throughout | Write a new typed function signature without looking |
| `lambda **kw: ...` dispatch table | `agent/loop.py:336` | Explain why `**kw` is used instead of positional args here |
| `pathlib.Path` over string paths | `agent/loop.py:33` | Explain two advantages of `Path` over `os.path` string operations |
| Module-level `re.compile()` | `agent/tools/database.py:21` | Explain the performance reason for compiling at module level |
| `threading.Lock` and `Queue` | `agent/loop.py:215` | Explain what race condition `Lock` prevents in `BackgroundManager` |
| f-strings | Throughout | Use f-strings with format specs: `f"{score:.4f}"`, `f"{name!r}"` |

These are your first study targets — read the actual code, not just the table.

---

## Priority 1 — Generator Functions and Async Generators

**Why this is first**: Every streaming LLM response is an async generator. You use them constantly but may not be able to write one from scratch confidently.

### Sync generator

```python
# 'yield' turns a function into a generator.
# The body does not run until you iterate over it.

def chunk_lines(file_path: str, batch_size: int = 100):
    """Yields lines in batches — never loads the whole file into memory."""
    batch = []
    with open(file_path) as f:
        for line in f:
            batch.append(line.strip())
            if len(batch) >= batch_size:
                yield batch     # pauses here; resumes on next iteration
                batch = []
    if batch:
        yield batch             # yield the final partial batch

# Usage
for batch in chunk_lines("corpus.txt"):
    embed(batch)                # process 100 lines at a time, memory stays flat
```

### Async generator — the LLM streaming pattern

```python
# 'async def' + 'yield' = async generator.
# FastAPI's StreamingResponse iterates this automatically.

async def token_stream(prompt: str):
    """Yields text chunks from Anthropic one at a time."""
    client = anthropic.Anthropic()
    with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk                 # caller gets one token at a time

# In FastAPI:
async def sse_endpoint():
    async def event_stream():
        async for chunk in token_stream("explain RAG"):
            yield f"data: {chunk}\n\n"  # SSE format
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### Generator expression — lazy list comprehension

```python
# List comprehension  → runs immediately, stores all results in memory
embeddings_list = [embed(chunk) for chunk in chunks]    # all in memory

# Generator expression → runs lazily, one item at a time
embeddings_gen  = (embed(chunk) for chunk in chunks)    # nothing runs yet

# The difference matters when chunks has 100,000 items
# Use [] when you need random access or len()
# Use () when you only need to iterate once
```

### Java analogy

There is no direct equivalent in Java. The closest is `Stream<T>` in Java 8+, but Python generators are simpler to write and compose. An async generator is roughly equivalent to a reactive `Flux<String>` in Project Reactor — but with far less boilerplate.

---

## Priority 2 — Pydantic v2 Patterns

**Why**: FastAPI is built on Pydantic. You will debug customer validation issues, help customers migrate from v1 to v2, and write request/response models in every project.

### Field validator — single field

```python
from pydantic import BaseModel, field_validator

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

    @field_validator("message")
    @classmethod                    # required in Pydantic v2 — most common v1→v2 mistake
    def message_not_blank(cls, v: str) -> str:
        """
        'v' is the raw value before assignment.
        Return value replaces the original — returning v.strip() gives free trimming.
        Raising ValueError → FastAPI automatically returns HTTP 422.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("message cannot be blank")
        return stripped             # callers always get a trimmed message
```

### Model validator — cross-field rules

```python
from pydantic import BaseModel, Field, model_validator

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: dict = {}

    @model_validator(mode="after")
    def top_k_requires_filters(self) -> "SearchRequest":
        """
        mode="after"  → all fields are already coerced Python types. Use self.field_name.
        mode="before" → receives raw dict. Use when you need to reshape the input itself.

        Rule: large result sets must be scoped with filters to avoid full-table scans.
        """
        if self.top_k > 20 and not self.filters:
            raise ValueError("top_k > 20 requires at least one filter")
        return self
```

### Settings with env var loading

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(description="Async PostgreSQL connection URL")
    llm_provider: str = Field(default="anthropic")
    max_tokens: int = Field(default=1024, ge=1, le=8192)
    anthropic_api_key: str = Field(default="")

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()   # reads from environment + .env file automatically
```

### Pydantic v1 → v2 migration — the questions customers always ask

| v1 pattern | v2 equivalent | Note |
|---|---|---|
| `@validator("field")` | `@field_validator("field")` + `@classmethod` | `@classmethod` is now required |
| `@root_validator` | `@model_validator(mode="after")` | `self` replaces `values` dict |
| `class Config: ...` | `model_config = {...}` | Config is now a dict |
| `.dict()` | `.model_dump()` | Old method still works but deprecated |
| `.json()` | `.model_dump_json()` | Same |
| `orm_mode = True` | `from_attributes = True` | Renamed in v2 |

---

## Priority 3 — `functools`

**Why**: These three functions replace patterns that Java requires entire classes for.

### `lru_cache` — memoize expensive pure functions

```python
from functools import lru_cache

# Without cache: fugashi.Tagger() runs every time — takes ~1s each call
# With cache: runs once, returns cached instance instantly ever after

@lru_cache(maxsize=1)
def get_tagger():
    import fugashi
    return fugashi.Tagger()     # expensive — dictionary load

# Verify caching works:
get_tagger()
get_tagger()
print(get_tagger.cache_info())  # CacheInfo(hits=1, misses=1, maxsize=1, currsize=1)

# Also useful for embedding model clients:
@lru_cache(maxsize=1)
def get_openai_client():
    import openai
    return openai.OpenAI()      # reuse one client across all requests
```

### `partial` — pre-configure functions

```python
from functools import partial
from worker.chunking.english import chunk_english

# Without partial: repeat all arguments everywhere
chunks = chunk_english(text, chunk_size=512, overlap=50)

# With partial: create named variants with arguments pre-filled
chunk_512  = partial(chunk_english, chunk_size=512,  overlap=50)
chunk_256  = partial(chunk_english, chunk_size=256,  overlap=25)
chunk_1024 = partial(chunk_english, chunk_size=1024, overlap=100)

# Now your A/B eval loop is clean:
for name, fn in [("256", chunk_256), ("512", chunk_512), ("1024", chunk_1024)]:
    precision = evaluate(fn(document_text), questions)
    print(f"{name}: {precision:.3f}")
```

### `reduce` — fold a list into a single value

```python
from functools import reduce

# Combine RRF scores from multiple retrieval passes
score_lists = {"vector": [0.9, 0.7, 0.5], "bm25": [0.8, 0.6, 0.4]}
combined = reduce(lambda a, b: [x + y for x, y in zip(a, b)], score_lists.values())
# combined = [1.7, 1.3, 0.9]

# Java equivalent: stream().reduce()
# Python's reduce is less common — prefer explicit loops when readability matters
```

---

## Priority 4 — `contextlib`

**Why**: You use `async with` everywhere but may not know how to *write* a context manager. Customers write bad resource management constantly — you need to recognize and fix it on the spot.

### `@contextmanager` — sync resources

```python
from contextlib import contextmanager
import psycopg2, psycopg2.extras

@contextmanager
def pg_cursor(url: str):
    """
    The @contextmanager decorator turns a generator into a context manager.
    The single 'yield' splits setup (before) from teardown (after).
    'finally' guarantees teardown even on exception — same as Java try-with-resources.
    """
    conn = psycopg2.connect(url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur           # caller's 'with' block runs here
    finally:
        conn.close()            # always runs

# Usage — identical to built-in context managers
with pg_cursor(database_url) as cur:
    cur.execute("SELECT * FROM chunks LIMIT 10")
    rows = cur.fetchall()
# conn.close() has already been called here
```

### `@asynccontextmanager` — async resources

```python
from contextlib import asynccontextmanager
import asyncpg

@asynccontextmanager
async def managed_connection(pool: asyncpg.Pool):
    """Async version — same structure, just add 'async' everywhere."""
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)

# Usage
async with managed_connection(pool) as conn:
    await conn.execute("UPDATE documents SET status = $1 WHERE id = $2", "ready", doc_id)
```

### `ExitStack` — dynamic stacking of context managers

```python
from contextlib import ExitStack

# When you don't know at write-time how many resources to open:
def process_files(paths: list[str]):
    with ExitStack() as stack:
        handles = [stack.enter_context(open(p)) for p in paths]
        # all files open here
        for fh in handles:
            process(fh.read())
    # all files closed here, even if one raised an exception
```

---

## Priority 5 — Python Data Structures for AI Code

**Why**: These replace verbose Java patterns with one-liners. You will reach for them constantly when processing retrieval results, token counts, and evaluation data.

### `defaultdict` — avoid KeyError on first access

```python
from collections import defaultdict

# Java equivalent: map.computeIfAbsent(key, k -> new ArrayList<>()).add(value)
# Python:
chunks_by_doc: dict[str, list] = defaultdict(list)

for chunk in retrieval_results:
    chunks_by_doc[chunk["doc_id"]].append(chunk)    # no KeyError on first access

# defaultdict(int) is useful for counting:
token_counts: dict[str, int] = defaultdict(int)
for token in tokens:
    token_counts[token] += 1    # no need to check if key exists
```

### `Counter` — frequency counting

```python
from collections import Counter

# Count token frequencies in retrieved chunks
all_tokens = [token for chunk in chunks for token in chunk.split()]
freq = Counter(all_tokens)

print(freq.most_common(10))     # top 10 tokens
print(freq["the"])              # frequency of "the"

# Useful in eval: which questions does your system fail on most?
failure_types = Counter(result["failure_type"] for result in eval_results if result["failed"])
print(failure_types.most_common())
```

### `TypedDict` — typed dict without Pydantic overhead

```python
from typing import TypedDict

class ChunkResult(TypedDict):
    """
    Use TypedDict for internal data you trust (your own SQL, your own functions).
    Use Pydantic BaseModel for external data (user input, API responses).

    TypedDict: zero runtime cost, type hints only
    Pydantic:  validates and coerces at runtime, has overhead
    """
    doc_id: str
    content: str
    rrf_score: float
    rank: int

# Your IDE now knows the exact shape:
def format_result(row: ChunkResult) -> str:
    return f"[{row['rank']}] {row['content'][:100]} (score: {row['rrf_score']:.4f})"
```

### `NamedTuple` — immutable record with field names

```python
from typing import NamedTuple

class RRFScore(NamedTuple):
    """
    Like a Java record — immutable, has field names, supports unpacking.
    Lighter than a dataclass when you don't need methods.
    """
    doc_id: str
    vector_rank: int
    bm25_rank: int

    def score(self, k: int = 60) -> float:
        return 1 / (k + self.vector_rank) + 1 / (k + self.bm25_rank)

# Can unpack like a tuple:
doc_id, v_rank, b_rank = RRFScore("abc", 1, 3)

# Can use in sorted():
results = sorted(scores, key=lambda s: s.score(), reverse=True)
```

---

## Priority 6 — Python Idioms That Replace Java Boilerplate

**Why**: You may be writing working-but-verbose Python that reads like Java. These are the patterns native Python developers reach for automatically.

### `enumerate` — loop with index

```python
# Java style (works but not idiomatic):
for i in range(len(chunks)):
    print(f"Chunk {i}: {chunks[i].text[:50]}")

# Python idiom:
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {chunk.text[:50]}")

# enumerate with start offset:
for i, chunk in enumerate(chunks, start=1):    # i starts at 1
    print(f"[{i}/{len(chunks)}] {chunk.text[:50]}")
```

### `zip` — iterate two sequences in parallel

```python
# Storing chunks with their embeddings:
for chunk, embedding in zip(chunks, embeddings):
    store(chunk.text, embedding)

# zip stops at the shorter sequence — use zip_longest if you need padding:
from itertools import zip_longest
for chunk, emb in zip_longest(chunks, embeddings, fillvalue=None):
    if emb is not None:
        store(chunk, emb)
```

### `dict.get()` with default — safe key access

```python
# Java: map.getOrDefault(key, defaultValue)
# Python:
metadata = row.get("metadata") or {}           # None or missing → empty dict
token_count = msg.get("token_count", 0)        # missing → 0
provider = os.getenv("LLM_PROVIDER", "anthropic")  # same pattern for env vars
```

### `match/case` — replace `if/elif` chains on enum-like values

```python
# Java: switch(stopReason) { case "tool_use": ... }
# Python 3.10+:
match response.stop_reason:
    case "tool_use":
        dispatch_tools(response)
    case "end_turn":
        return response
    case "max_tokens":
        log.warning("response truncated")
        return response
    case other:                         # catch-all — binds the value to 'other'
        raise ValueError(f"unexpected stop_reason: {other}")
```

### First-class functions — pass behavior as arguments

```python
# Functions are objects in Python — assign them, pass them, store them in dicts

# Handler dispatch (you already do this in agent/loop.py):
handlers = {
    "read_file":  lambda **kw: run_read(kw["path"]),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
}
result = handlers[tool_name](**tool_input)

# Strategy pattern without interfaces:
embedding_providers = {
    "voyage":  voyage_embed,
    "cohere":  cohere_embed,
    "openai":  openai_embed,
}
embed = embedding_providers[os.getenv("EMBEDDING_PROVIDER", "openai")]
vectors = embed(texts)      # call whichever was selected
```

### Property — computed attributes without getter methods

```python
# Java: private field + getSize() method
# Python: @property makes it look like a field but computed on access

from dataclasses import dataclass

@dataclass
class Document:
    filename: str
    content: str

    @property
    def word_count(self) -> int:
        return len(self.content.split())

    @property
    def is_large(self) -> bool:
        return self.word_count > 10_000

doc = Document("report.txt", "hello world ...")
print(doc.word_count)   # looks like a field, behaves like a method
print(doc.is_large)     # no () needed
```

### Exception chaining — preserve cause context

```python
# Java: throw new RuntimeException("message", cause)
# Python:
try:
    result = call_anthropic(prompt)
except anthropic.APIError as e:
    raise RuntimeError(f"LLM call failed for session {session_id}") from e
    #                                                                  ^^^^^^
    # 'from e' attaches the original exception as __cause__
    # Traceback shows both exceptions — critical for debugging in production
```

---

## How to Practice Using Your Existing Codebase

These five exercises build pattern recognition faster than reading:

**1. `async/await` audit** (15 min)
Open `backend/routers/chat.py`. Read every `async` and `await` and explain out loud: *why is this function async? What blocks if I remove this await?* If you cannot answer, you have a gap.

**2. Generator rewrite** (20 min)
Write `_redis_sse_stream` from scratch without looking at the original. Use only the spec: subscribe, loop, handle timeout / keepalive / chunk / done, unsubscribe in finally. Compare your version with the original.

**3. `@lru_cache` refactor** (15 min)
Replace `tagger = fugashi.Tagger()` in `worker/chunking/japanese.py` with a `@lru_cache(maxsize=1)` function. Run `_get_tagger.cache_info()` and confirm `misses=1` after two calls.

**4. `@field_validator` addition** (20 min)
Add `message_not_blank` and `session_id_valid_uuid` validators to `ChatRequest` in `backend/routers/chat.py`. Send an empty message to the API — confirm HTTP 422 with a clear error.

**5. `@contextmanager` refactor** (20 min)
Wrap the psycopg2 connection lifecycle in `agent/tools/retrieval.py` with a `@contextmanager`. The connection should close in `finally` — confirm by raising a deliberate exception mid-query and checking that no connection leak occurs.

---

## Mental Model: Python vs Java — The Core Difference

Java is **nominal** — types are defined by their class name and explicit interface declarations.
Python is **structural** — types are defined by what methods they have (duck typing).

```python
# Python doesn't care what class this is — only that it has .embed_batch()
def process(embedder):              # no type annotation needed for duck typing
    return embedder.embed_batch(texts)

# But for documentation and tooling, you can declare the shape with Protocol:
from typing import Protocol

class Embedder(Protocol):
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...

def process(embedder: Embedder) -> list[list[float]]:   # now your IDE helps
    return embedder.embed_batch(texts)

# Any class with embed_batch() satisfies this Protocol — no 'implements' keyword
# VoyageEmbedder, CohereEmbedder, MockEmbedder all work without inheritance
```

This is why your `llm_client.py` can switch providers with an env var — both `anthropic.Anthropic()` and `openai.OpenAI()` happen to have compatible interfaces, and Python's duck typing lets you call both through the same function without a shared base class.

---

## Done Criteria

You are fluent when you can do all of the following without looking anything up:

- [ ] Write an async generator that yields SSE-formatted chunks from a Redis pub/sub channel
- [ ] Write a `@contextmanager` for a psycopg2 connection with guaranteed cleanup
- [ ] Add a Pydantic v2 `@field_validator` and explain why `@classmethod` is required
- [ ] Explain the difference between `@field_validator` and `@model_validator` in one sentence
- [ ] Add `@lru_cache` to a function and verify it with `.cache_info()`
- [ ] Use `partial` to create three named variants of a function that differ only in their arguments
- [ ] Replace an `if/elif` chain on a string value with `match/case`
- [ ] Explain duck typing vs nominal typing to a customer who asks "why doesn't Python have interfaces?"
