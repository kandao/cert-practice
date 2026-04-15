"""
Exercise 6 — TypedDict
=======================
Pattern  : typing.TypedDict
Target   : ai-project/agent/tools/retrieval.py  →  hybrid_retrieval()
Time     : 15 min
Depends  : stdlib only

PROBLEM
-------
hybrid_retrieval() fetches rows with cur.fetchall() which returns list[dict].
There is no type information — your IDE cannot tell you that row["rrf_score"]
is a float or that row["content"] is a str. Typos in key names are only caught
at runtime.

YOUR TASK
---------
1. Run this script — understand the difference between plain dict, TypedDict,
   and Pydantic BaseModel.
2. Open ai-project/agent/tools/retrieval.py.
3. Add ChunkRow(TypedDict) near the top.
4. Annotate the rows variable:  rows: list[ChunkRow] = cur.fetchall()

JAVA ANALOGY
------------
TypedDict is like a Java record or a typed Map:

    // Java record (immutable, typed fields):
    record ChunkRow(String id, String content, Map<?,?> metadata, double rrfScore) {}

    // TypedDict (mutable dict with documented schema, zero runtime cost):
    class ChunkRow(TypedDict):
        id: str
        content: str
        metadata: dict
        rrf_score: float

Key difference from Pydantic:
  TypedDict = type hints only, zero runtime overhead, no validation.
  Use it for data YOU generated (your own SQL) where you trust the shape.
  Use Pydantic for external data (user input, API responses) that needs validation.
"""

from typing import TypedDict, get_type_hints


# ── The TypedDict ─────────────────────────────────────────────────────────────

class ChunkRow(TypedDict):
    """
    Typed shape of one row from the hybrid retrieval SQL query.

    At runtime ChunkRow IS just a plain dict — isinstance(row, dict) is True.
    The type annotations exist only for your IDE and mypy.
    No class instantiation, no __init__, no validation overhead.
    """
    id: str
    content: str
    metadata: dict
    rrf_score: float


# ── Demos ─────────────────────────────────────────────────────────────────────

def demo_basic():
    print("\n--- Basic TypedDict usage ---")

    # At runtime, a TypedDict is a plain dict
    row: ChunkRow = {
        "id": "chunk-abc",
        "content": "RAG stands for Retrieval Augmented Generation.",
        "metadata": {"doc_id": "doc-1", "language": "en"},
        "rrf_score": 0.8742,
    }

    print(f"  row['content']   = {row['content'][:40]}...")
    print(f"  row['rrf_score'] = {row['rrf_score']}")
    print(f"  isinstance(row, dict) = {isinstance(row, dict)}  ← still a dict at runtime")
    print(f"  type(row)             = {type(row).__name__}")


def demo_type_hints():
    print("\n--- What your IDE and mypy see ---")
    hints = get_type_hints(ChunkRow)
    print(f"  get_type_hints(ChunkRow) = {hints}")
    print("""
  With 'row: ChunkRow':
    row["rrf_score"]  → IDE knows: float
    row["content"]    → IDE knows: str
    row["rrf"]        → mypy flags: TypedDict "ChunkRow" has no key "rrf"
    row["rrf_score"]  → mypy flags if you assign: row["rrf_score"] = "oops"
  """)


def demo_vs_plain_dict():
    print("\n--- TypedDict vs plain dict ---")

    # Plain dict — no type info, IDE cannot help
    plain: dict = {"id": "x", "content": "y", "metadata": {}, "rrf_score": 0.5}

    # TypedDict — same at runtime, but documented shape
    typed: ChunkRow = {"id": "x", "content": "y", "metadata": {}, "rrf_score": 0.5}

    print(f"  plain dict: type={type(plain).__name__}  IDE knows nothing about keys")
    print(f"  TypedDict:  type={type(typed).__name__}  IDE knows all key names and types")
    print(f"  Runtime cost difference: ZERO — they are the same object at runtime")


def demo_vs_pydantic():
    print("\n--- TypedDict vs Pydantic BaseModel ---")
    print("""
  TypedDict:
    - Zero runtime overhead — it IS a plain dict
    - No validation — wrong types silently accepted at runtime
    - Use for: internal data you generated yourself (your own SQL, your own functions)

  Pydantic BaseModel:
    - Validates and coerces on instantiation — wrong types raise ValidationError
    - Has overhead (field parsing, model creation)
    - Use for: external data (user HTTP input, API responses, config files)

  Rule of thumb:
    Data from YOUR code         → TypedDict
    Data from OUTSIDE your code → Pydantic
  """)

    try:
        from pydantic import BaseModel

        class ChunkRowPydantic(BaseModel):
            id: str
            content: str
            rrf_score: float

        # Pydantic validates — wrong type raises error
        try:
            ChunkRowPydantic(id=123, content="hello", rrf_score="not a float")
        except Exception as e:
            print(f"  Pydantic with wrong types: {type(e).__name__} — validates!")

        # TypedDict does NOT validate at runtime
        bad: ChunkRow = {"id": 123, "content": "hello", "metadata": {}, "rrf_score": "oops"}  # type: ignore
        print(f"  TypedDict with wrong types: no error — {bad['id']!r} stored as-is")

    except ImportError:
        print("  (pydantic not installed — skipping Pydantic comparison)")


def demo_annotating_rows():
    print("\n--- How to annotate the rows variable in hybrid_retrieval ---")
    print("""
  # In ai-project/agent/tools/retrieval.py, inside hybrid_retrieval():
  #
  # BEFORE:
  rows = cur.fetchall()
  #
  # AFTER:
  rows: list[ChunkRow] = cur.fetchall()
  #
  # Now when you write:
  for row in rows:
      score = row["rrf_score"]    # IDE: float
      text  = row["content"]      # IDE: str
      meta  = row["metadata"]     # IDE: dict
  """)


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/agent/tools/retrieval.py
=======================================================

ADD to imports at the top:
    from typing import TypedDict

ADD this class after the imports, before _get_embedding():
    class ChunkRow(TypedDict):
        id: str
        content: str
        metadata: dict
        rrf_score: float

CHANGE inside hybrid_retrieval(), after the cursor execution:
    # BEFORE:
    rows = cur.fetchall()

    # AFTER:
    rows: list[ChunkRow] = cur.fetchall()

That's it. No runtime behaviour changes — only type information added.
"""


if __name__ == "__main__":
    print(__doc__)
    demo_basic()
    demo_type_hints()
    demo_vs_plain_dict()
    demo_vs_pydantic()
    demo_annotating_rows()
    print(APPLY_DIFF)
