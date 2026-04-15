"""
00_skills_guide.py — Runnable demos for all 6 Python fluency priorities.

Each demo() function is self-contained and prints its output.
Run the whole file:  python 00_skills_guide.py
Run one section:     python -c "import 00_skills_guide; 00_skills_guide.demo_1()"

No external dependencies — stdlib only.
"""

# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY 1 — Generator Functions and Async Generators
# ─────────────────────────────────────────────────────────────────────────────

def demo_1():
    print("\n" + "="*60)
    print("PRIORITY 1 — Generators and Async Generators")
    print("="*60)

    # ── 1a. Sync generator ────────────────────────────────────────
    def chunk_words(text: str, size: int):
        """
        'yield' turns a function into a generator.
        The body does NOT run until you iterate — nothing executes on call.
        Each 'yield' pauses the function; next() resumes it.
        """
        words = text.split()
        for i in range(0, len(words), size):
            yield words[i:i + size]   # pause here, hand value to caller

    text = "the quick brown fox jumps over the lazy dog"
    print("\n[1a] Sync generator — chunk_words(text, 3):")
    for chunk in chunk_words(text, 3):
        print("  ", chunk)

    # Key: calling the function returns a generator object, runs NOTHING yet
    gen = chunk_words(text, 3)
    print(f"  type(gen) = {type(gen).__name__}")  # <generator object>

    # ── 1b. Generator expression — lazy list comprehension ───────
    print("\n[1b] Generator expression vs list comprehension:")
    words = text.split()

    list_comp = [w.upper() for w in words]      # runs immediately, all in memory
    gen_expr  = (w.upper() for w in words)      # runs lazily, one at a time

    print(f"  list_comp type: {type(list_comp).__name__}  len={len(list_comp)}")
    print(f"  gen_expr  type: {type(gen_expr).__name__}   (no len — not computed yet)")
    print(f"  first from gen_expr: {next(gen_expr)}")

    # ── 1c. Async generator (pattern demo — asyncio not needed to read) ──
    print("\n[1c] Async generator pattern (conceptual):")
    print("""
  async def token_stream(prompt: str):
      # 'async def' + 'yield' = async generator
      # caller uses:  async for chunk in token_stream(prompt)
      client = anthropic.Anthropic()
      with client.messages.stream(...) as stream:
          for chunk in stream.text_stream:
              yield chunk    # one token at a time, event loop free between yields

  # In FastAPI — StreamingResponse pulls from the generator automatically:
  return StreamingResponse(token_stream(prompt), media_type="text/event-stream")
  """)

    # ── 1d. Prove generators are lazy ────────────────────────────
    print("[1d] Proving laziness — side-effect generator:")
    def noisy(n):
        for i in range(n):
            print(f"  generating {i}")
            yield i

    gen = noisy(3)
    print("  generator created — nothing printed yet")
    print(f"  next(gen) = {next(gen)}")   # only now does "generating 0" print
    print(f"  next(gen) = {next(gen)}")


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY 2 — Pydantic v2 Patterns
# ─────────────────────────────────────────────────────────────────────────────

def demo_2():
    print("\n" + "="*60)
    print("PRIORITY 2 — Pydantic v2 Patterns")
    print("="*60)

    try:
        from pydantic import BaseModel, field_validator, model_validator, Field
    except ImportError:
        print("  [SKIP] pydantic not installed — run: pip install pydantic")
        return

    # ── 2a. @field_validator ─────────────────────────────────────
    class ChatRequest(BaseModel):
        message: str
        session_id: str | None = None

        @field_validator("message")
        @classmethod                        # required in Pydantic v2
        def message_not_blank(cls, v: str) -> str:
            stripped = v.strip()
            if not stripped:
                raise ValueError("message cannot be blank")
            return stripped                 # return value REPLACES the original

    print("\n[2a] @field_validator:")
    req = ChatRequest(message="  hello world  ")
    print(f"  input:  '  hello world  '")
    print(f"  stored: '{req.message}'")     # auto-stripped

    try:
        ChatRequest(message="   ")
    except Exception as e:
        print(f"  blank message → {e}")

    # ── 2b. @model_validator ─────────────────────────────────────
    class SearchRequest(BaseModel):
        query: str
        top_k: int = 5
        filters: dict = {}

        @model_validator(mode="after")
        def top_k_requires_filters(self) -> "SearchRequest":
            """mode='after': self.field_name gives coerced Python types."""
            if self.top_k > 20 and not self.filters:
                raise ValueError("top_k > 20 requires at least one filter")
            return self

    print("\n[2b] @model_validator(mode='after'):")
    ok = SearchRequest(query="rag", top_k=5)
    print(f"  top_k=5, no filters → OK: {ok.top_k}")

    try:
        SearchRequest(query="rag", top_k=50)
    except Exception as e:
        print(f"  top_k=50, no filters → {e}")

    ok2 = SearchRequest(query="rag", top_k=50, filters={"dept": "eng"})
    print(f"  top_k=50, with filters → OK: {ok2.top_k}")

    # ── 2c. v1 → v2 migration cheat sheet ───────────────────────
    print("\n[2c] Pydantic v1 → v2 migration — most common breakages:")
    cheatsheet = [
        ("@validator('field')",   "@field_validator('field') + @classmethod"),
        ("@root_validator",       "@model_validator(mode='after')"),
        ("class Config: ...",     "model_config = {...}"),
        (".dict()",               ".model_dump()"),
        (".json()",               ".model_dump_json()"),
        ("orm_mode = True",       "from_attributes = True"),
    ]
    for old, new in cheatsheet:
        print(f"  v1: {old:<30}  →  v2: {new}")


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY 3 — functools
# ─────────────────────────────────────────────────────────────────────────────

def demo_3():
    print("\n" + "="*60)
    print("PRIORITY 3 — functools")
    print("="*60)

    from functools import lru_cache, partial
    import time

    # ── 3a. lru_cache ────────────────────────────────────────────
    call_count = 0

    @lru_cache(maxsize=128)
    def slow_embed(text: str) -> int:
        """Simulate an expensive embedding call."""
        nonlocal call_count
        call_count += 1
        time.sleep(0.01)       # pretend this takes 10ms
        return hash(text) % 1000

    print("\n[3a] @lru_cache — call count stays low despite repeated inputs:")
    texts = ["hello", "world", "hello", "hello", "world", "new"]
    for t in texts:
        slow_embed(t)

    info = slow_embed.cache_info()
    print(f"  processed {len(texts)} texts")
    print(f"  cache hits={info.hits}  misses={info.misses}  (actual calls={call_count})")
    print(f"  lru_cache(maxsize=1) pattern: cache exactly ONE result forever")

    # ── 3b. partial ──────────────────────────────────────────────
    def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
        words = text.split()
        chunks, i = [], 0
        step = chunk_size - overlap
        while i < len(words):
            chunks.append(" ".join(words[i:i+chunk_size]))
            i += step
        return chunks

    chunk_256  = partial(chunk_text, chunk_size=256,  overlap=25)
    chunk_512  = partial(chunk_text, chunk_size=512,  overlap=50)
    chunk_1024 = partial(chunk_text, chunk_size=1024, overlap=100)

    sample = " ".join([f"word{i}" for i in range(600)])
    print("\n[3b] functools.partial — pre-configured chunk size variants:")
    for name, fn in [("chunk_256", chunk_256), ("chunk_512", chunk_512), ("chunk_1024", chunk_1024)]:
        result = fn(sample)
        print(f"  {name}(600 words) → {len(result)} chunks")

    print(f"\n  partial(chunk_text, chunk_size=256, overlap=25) is identical to:")
    print(f"  lambda text: chunk_text(text, chunk_size=256, overlap=25)")
    print(f"  but partial is introspectable: chunk_256.func = {chunk_256.func.__name__}")
    print(f"  chunk_256.keywords = {chunk_256.keywords}")


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY 4 — contextlib
# ─────────────────────────────────────────────────────────────────────────────

def demo_4():
    print("\n" + "="*60)
    print("PRIORITY 4 — contextlib")
    print("="*60)

    from contextlib import contextmanager
    import sqlite3, tempfile, os

    # ── 4a. Basic @contextmanager ─────────────────────────────────
    @contextmanager
    def db_cursor(db_path: str):
        """
        @contextmanager turns a generator into a context manager.
        Single 'yield' splits setup (before) from teardown (after).
        'finally' guarantees teardown even when the with-block raises.

        Java: try (Connection c = ...) { ... }  // auto-close
        Python: @contextmanager does the same, explicitly
        """
        conn = sqlite3.connect(db_path)
        print(f"  [cm] connection opened")
        try:
            yield conn.cursor()
        finally:
            conn.close()
            print(f"  [cm] connection closed (always runs)")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    print("\n[4a] @contextmanager — normal exit:")
    with db_cursor(db_path) as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS t (x INTEGER)")
        cur.execute("INSERT INTO t VALUES (42)")
        print(f"  inside with-block, inserted row")
    # "connection closed" prints here

    print("\n[4b] @contextmanager — exception inside with-block:")
    try:
        with db_cursor(db_path) as cur:
            print(f"  about to raise...")
            raise RuntimeError("simulated error")
    except RuntimeError:
        print(f"  exception caught — but connection was still closed (see above)")

    os.unlink(db_path)

    # ── 4b. Prove the difference vs manual try/finally ───────────
    print("\n[4c] Pattern comparison:")
    print("""
  # Without @contextmanager — connection management mixed into business logic:
  conn = psycopg2.connect(url)
  try:
      with conn.cursor() as cur:
          cur.execute(sql)
          rows = cur.fetchall()
  finally:
      conn.close()   # repeated in every function that needs a cursor

  # With @contextmanager — management extracted once, reused everywhere:
  with _pg_cursor(url) as cur:
      cur.execute(sql)
      rows = cur.fetchall()
  # conn.close() is in _pg_cursor's finally — runs automatically
  """)


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY 5 — Python Data Structures for AI Code
# ─────────────────────────────────────────────────────────────────────────────

def demo_5():
    print("\n" + "="*60)
    print("PRIORITY 5 — Python Data Structures for AI Code")
    print("="*60)

    from collections import defaultdict, Counter
    from typing import TypedDict, NamedTuple

    # ── 5a. defaultdict ──────────────────────────────────────────
    print("\n[5a] defaultdict — group retrieval chunks by doc_id:")
    raw_chunks = [
        {"doc_id": "doc-1", "content": "chunk A", "score": 0.9},
        {"doc_id": "doc-2", "content": "chunk B", "score": 0.8},
        {"doc_id": "doc-1", "content": "chunk C", "score": 0.7},
        {"doc_id": "doc-3", "content": "chunk D", "score": 0.6},
        {"doc_id": "doc-1", "content": "chunk E", "score": 0.5},
    ]

    by_doc: dict[str, list] = defaultdict(list)
    for chunk in raw_chunks:
        by_doc[chunk["doc_id"]].append(chunk["content"])
        # No KeyError on first access — defaultdict creates [] automatically

    for doc_id, contents in by_doc.items():
        print(f"  {doc_id}: {contents}")

    # ── 5b. Counter ──────────────────────────────────────────────
    print("\n[5b] Counter — token frequency in retrieved chunks:")
    tokens = "the cat sat on the mat the cat".split()
    freq = Counter(tokens)
    print(f"  most_common(3): {freq.most_common(3)}")
    print(f"  freq['the'] = {freq['the']}")
    print(f"  freq['dog'] = {freq['dog']}  ← missing key returns 0 (not KeyError)")

    # ── 5c. TypedDict ────────────────────────────────────────────
    print("\n[5c] TypedDict — typed shape for retrieval rows:")

    class ChunkRow(TypedDict):
        id: str
        content: str
        rrf_score: float
        rank: int

    row: ChunkRow = {"id": "abc", "content": "hello world", "rrf_score": 0.87, "rank": 1}
    print(f"  row['rrf_score'] = {row['rrf_score']}  (IDE knows this is float)")
    print(f"  isinstance(row, dict) = {isinstance(row, dict)}  (TypedDict IS a dict at runtime)")
    print(f"  TypedDict adds zero runtime cost — type hints only")

    # ── 5d. NamedTuple ───────────────────────────────────────────
    print("\n[5d] NamedTuple — immutable record with field names:")

    class RRFScore(NamedTuple):
        doc_id: str
        vector_rank: int
        bm25_rank: int

        def score(self, k: int = 60) -> float:
            return 1 / (k + self.vector_rank) + 1 / (k + self.bm25_rank)

    s = RRFScore("doc-1", vector_rank=1, bm25_rank=3)
    print(f"  s = {s}")
    print(f"  s.score() = {s.score():.6f}")
    doc_id, v_rank, b_rank = s    # unpacks like a tuple
    print(f"  unpacked: doc_id={doc_id}, v_rank={v_rank}, b_rank={b_rank}")

    scores = [RRFScore("d1", 1, 5), RRFScore("d2", 3, 1), RRFScore("d3", 2, 2)]
    ranked = sorted(scores, key=lambda s: s.score(), reverse=True)
    print(f"  sorted by RRF score: {[s.doc_id for s in ranked]}")


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY 6 — Python Idioms That Replace Java Boilerplate
# ─────────────────────────────────────────────────────────────────────────────

def demo_6():
    print("\n" + "="*60)
    print("PRIORITY 6 — Python Idioms That Replace Java Boilerplate")
    print("="*60)

    # ── 6a. enumerate ────────────────────────────────────────────
    print("\n[6a] enumerate — loop with index (never use range(len(...))):")
    chunks = ["alpha", "beta", "gamma", "delta"]

    print("  Java-style (works but not idiomatic):")
    for i in range(len(chunks)):
        print(f"    [{i}] {chunks[i]}")

    print("  Python-style:")
    for i, chunk in enumerate(chunks, start=1):
        print(f"    [{i}/{len(chunks)}] {chunk}")

    # ── 6b. zip ──────────────────────────────────────────────────
    print("\n[6b] zip — iterate two sequences in parallel:")
    texts = ["doc A content", "doc B content", "doc C content"]
    embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]

    for text, embedding in zip(texts, embeddings):
        print(f"  '{text[:10]}...' → {embedding}")

    # ── 6c. dict.get() ───────────────────────────────────────────
    print("\n[6c] dict.get() — safe key access with default:")
    metadata = {"doc_id": "abc-123", "language": "en"}
    print(f"  metadata.get('language', 'unknown')  = {metadata.get('language', 'unknown')}")
    print(f"  metadata.get('author', 'unknown')    = {metadata.get('author', 'unknown')}")
    print(f"  metadata['author']                   → KeyError")

    # ── 6d. match/case ───────────────────────────────────────────
    print("\n[6d] match/case — replaces if/elif chains on enum-like values:")

    def handle_stop(reason: str) -> str:
        match reason:
            case "tool_use":    return "dispatch tools"
            case "end_turn":    return "finished normally"
            case "max_tokens":  return "TRUNCATED — warn user"
            case other:         return f"unexpected: {other!r}"  # 'other' binds the value

    for r in ["end_turn", "tool_use", "max_tokens", "unknown_reason"]:
        print(f"  stop_reason={r!r:20} → {handle_stop(r)}")

    # ── 6e. First-class functions ─────────────────────────────────
    print("\n[6e] First-class functions — strategy pattern without interfaces:")

    def embed_voyage(texts):  return [f"voyage:{hash(t)%100}" for t in texts]
    def embed_openai(texts):  return [f"openai:{hash(t)%100}" for t in texts]
    def embed_cohere(texts):  return [f"cohere:{hash(t)%100}" for t in texts]

    import os
    providers = {"voyage": embed_voyage, "openai": embed_openai, "cohere": embed_cohere}
    provider  = os.getenv("EMBEDDING_PROVIDER", "openai")
    embed     = providers[provider]

    result = embed(["hello", "world"])
    print(f"  EMBEDDING_PROVIDER={provider!r} → {result}")

    # ── 6f. Exception chaining ────────────────────────────────────
    print("\n[6f] Exception chaining — 'raise X from Y' preserves cause:")
    print("""
  try:
      result = call_anthropic(prompt)
  except anthropic.APIError as e:
      raise RuntimeError(f"LLM call failed for session {session_id}") from e
      #                                                                  ^^^ 'from e'
      # Traceback shows BOTH exceptions — critical for production debugging.
      # Without 'from e': cause is lost, traceback is harder to read.
  """)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("Python Skills Guide — Runnable Demos")
    print("Java Developer → FDE / Applied AI Engineer")

    demo_1()
    demo_2()
    demo_3()
    demo_4()
    demo_5()
    demo_6()

    print("\n" + "="*60)
    print("Done. Run individual demos: python -c \"")
    print("  import importlib, sys")
    print("  sys.path.insert(0, '.')")
    print("  m = importlib.import_module('00_skills_guide')")
    print("  m.demo_3()  # run only Priority 3\"")
    print("="*60)


if __name__ == "__main__":
    main()
