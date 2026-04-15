"""
Exercise 7 — functools.partial
================================
Pattern  : functools.partial
Target   : ai-project/worker/chunking/__init__.py
Time     : 10 min
Depends  : stdlib only

PROBLEM
-------
The Week 4 eval plan requires A/B testing three chunk sizes (256, 512, 1024).
Without partial you would write three wrapper functions or repeat all arguments
at every call site. partial creates named, pre-configured callables cleanly.

YOUR TASK
---------
1. Run this script — compare chunk counts across sizes on a sample text.
2. Open ai-project/worker/chunking/__init__.py.
3. Add the three partial variants shown in APPLY_DIFF.
4. Use them in your Week 4 eval script to compare retrieval precision.

JAVA ANALOGY
------------
partial is equivalent to a factory method or a lambda that pre-fills arguments:

    // Java lambda pre-filling args:
    Function<String, List<Chunk>> chunk256 = text -> chunkEnglish(text, 256, 25);

    # Python partial — same concept, more introspectable:
    chunk_256 = partial(chunk_english, chunk_size=256, overlap=25)

    # partial is better than a lambda because:
    chunk_256.func     → chunk_english      (the original function)
    chunk_256.keywords → {chunk_size: 256, overlap: 25}  (pre-filled args)
"""

from functools import partial


# ── Inline chunk_english to keep this script self-contained ──────────────────
# (In your eval script you'd import from worker.chunking)

def chunk_english(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Sliding window chunker — same logic as ai-project/worker/chunking/english.py"""
    words = text.split()
    chunks, start = [], 0
    step = max(1, chunk_size - overlap)
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += step
    return chunks


# ── The partial variants ──────────────────────────────────────────────────────

chunk_256  = partial(chunk_english, chunk_size=256,  overlap=25)
chunk_512  = partial(chunk_english, chunk_size=512,  overlap=50)
chunk_1024 = partial(chunk_english, chunk_size=1024, overlap=100)


# ── Demos ─────────────────────────────────────────────────────────────────────

def demo_basic():
    print("\n--- partial creates a pre-configured callable ---")

    sample = " ".join([f"word{i}" for i in range(600)])

    print(f"\n  Sample text: 600 words")
    for name, fn in [("chunk_256", chunk_256), ("chunk_512", chunk_512), ("chunk_1024", chunk_1024)]:
        chunks = fn(sample)
        avg_len = sum(len(c.split()) for c in chunks) / len(chunks)
        print(f"  {name:12}: {len(chunks):3} chunks, avg {avg_len:.0f} words/chunk")


def demo_equivalence():
    print("\n--- partial call is identical to calling the original with pre-filled args ---")

    text = "the quick brown fox jumps over the lazy dog"
    r1 = chunk_256(text)
    r2 = chunk_english(text, chunk_size=256, overlap=25)

    print(f"  chunk_256(text)                             = {r1}")
    print(f"  chunk_english(text, chunk_size=256, overlap=25) = {r2}")
    print(f"  Equal: {r1 == r2}")


def demo_introspection():
    print("\n--- partial is introspectable (lambda is not) ---")

    print(f"  chunk_256.func     = {chunk_256.func.__name__}")
    print(f"  chunk_256.keywords = {chunk_256.keywords}")
    print(f"  chunk_256.args     = {chunk_256.args}  (positional pre-fills, empty here)")

    # lambda has no introspection
    chunk_lam = lambda text: chunk_english(text, chunk_size=256, overlap=25)
    print(f"\n  lambda equivalent: {chunk_lam}")
    print(f"  lambda has no .func or .keywords — can't inspect pre-filled values")


def demo_eval_loop():
    print("\n--- Usage in eval A/B test (Week 4) ---")

    # Simulate a simple eval
    corpus = " ".join([f"term{i}" for i in range(1000)])
    query_terms = ["term42", "term100", "term500"]

    def precision_at_3(chunks: list[str], terms: list[str]) -> float:
        """Fraction of query terms that appear in the top 3 chunks."""
        top3 = chunks[:3]
        hits = sum(1 for t in terms if any(t in c for c in top3))
        return hits / len(terms)

    print(f"\n  {'Strategy':<12} {'Chunks':>8} {'Precision@3':>14}")
    print(f"  {'-'*12} {'-'*8} {'-'*14}")
    for name, fn in [("chunk_256", chunk_256), ("chunk_512", chunk_512), ("chunk_1024", chunk_1024)]:
        chunks = fn(corpus)
        p = precision_at_3(chunks, query_terms)
        print(f"  {name:<12} {len(chunks):>8} {p:>14.2f}")

    print(f"\n  This is the pattern for your Week 4 eval plan.")
    print(f"  Swap in real retrieval and real questions for actual measurements.")


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/worker/chunking/__init__.py
==========================================================

ADD to imports at the top:
    from functools import partial

ADD after the chunk() function:
    # Pre-configured variants for A/B chunk size evaluation (eval plan, Week 4)
    chunk_256  = partial(chunk_english, chunk_size=256,  overlap=25)
    chunk_512  = partial(chunk_english, chunk_size=512,  overlap=50)
    chunk_1024 = partial(chunk_english, chunk_size=1024, overlap=100)

USAGE in your eval script:
    from worker.chunking import chunk_256, chunk_512, chunk_1024

    for name, fn in [("256", chunk_256), ("512", chunk_512), ("1024", chunk_1024)]:
        chunks = fn(document_text)
        precision = measure_retrieval_precision(chunks, questions)
        print(f"chunk_size={name}: precision@3={precision:.3f}")
"""


if __name__ == "__main__":
    print(__doc__)
    demo_basic()
    demo_equivalence()
    demo_introspection()
    demo_eval_loop()
    print(APPLY_DIFF)
