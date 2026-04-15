"""
Exercise 1 — @lru_cache
=======================
Pattern  : functools.lru_cache
Target   : ai-project/worker/chunking/japanese.py
Time     : 15 min
Depends  : stdlib only (no external packages)

PROBLEM
-------
The current japanese.py initialises `tagger = fugashi.Tagger()` at module level.
This runs at import time — if MeCab is not installed the entire worker crashes
even when no Japanese text is ever processed.

YOUR TASK
---------
1. Run this script and read the output to understand @lru_cache.
2. Open ai-project/worker/chunking/japanese.py.
3. Replace the module-level `tagger = fugashi.Tagger()` line with a
   `@lru_cache(maxsize=1)` function called `_get_tagger()`.
4. Update `chunk_japanese()` to call `_get_tagger()` instead of `tagger`.
5. Verify with cache_info() as shown below.

JAVA ANALOGY
------------
Equivalent to lazy-initialised static final with double-checked locking:

    private static volatile Tagger instance;
    public static Tagger getInstance() {
        if (instance == null) {
            synchronized (Tagger.class) {
                if (instance == null) instance = new Tagger();
            }
        }
        return instance;
    }

Python's @lru_cache is thread-safe and requires zero boilerplate.
"""

from functools import lru_cache
import time


# ── Mock ─────────────────────────────────────────────────────────────────────
# We mock fugashi.Tagger so this script runs without MeCab installed.
# The lru_cache behaviour is identical regardless of what the function returns.

class _MockTagger:
    """Stands in for fugashi.Tagger — counts how many times it was created."""
    _instance_count = 0

    def __init__(self):
        _MockTagger._instance_count += 1
        time.sleep(0.05)    # simulate the ~1s MeCab dictionary load
        print(f"  [Tagger.__init__] called (total initialisations: {_MockTagger._instance_count})")

    def __call__(self, text: str):
        """Return fake token objects with a .surface attribute."""
        class Token:
            def __init__(self, s): self.surface = s
        return [Token(w) for w in text.split()]


# ── Before: module-level init (the problem) ──────────────────────────────────

def demo_before():
    print("\n--- BEFORE: module-level init ---")
    print("  tagger = _MockTagger()  ← runs at import time, every time the module loads")
    tagger = _MockTagger()   # imagine this is the top of japanese.py
    tokens = [w.surface for w in tagger("日本語 テスト")]
    print(f"  tokens = {tokens}")
    print(f"  Problem: if MeCab is absent this line crashes the worker on startup,")
    print(f"           even if no Japanese documents are ever processed.")


# ── After: @lru_cache(maxsize=1) ─────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_tagger() -> _MockTagger:
    """
    Lazy init + permanent cache.

    lru_cache(maxsize=1):
      - Stores exactly ONE return value (the Tagger instance).
      - First call  : executes the body, caches the result, returns it.
      - Every later : returns the cached instance instantly — body never runs again.
      - Thread-safe : Python's GIL + lru_cache internals guarantee this.
    """
    return _MockTagger()


def chunk_japanese(text: str, chunk_size: int = 3, overlap: int = 1) -> list[str]:
    tagger = _get_tagger()          # fast after first call
    tokens = [w.surface for w in tagger(text)]
    chunks, start = [], 0
    step = chunk_size - overlap
    while start < len(tokens):
        chunks.append("".join(tokens[start:start + chunk_size]))
        start += step
    return chunks


def demo_after():
    print("\n--- AFTER: @lru_cache(maxsize=1) ---")

    print("\nFirst call to _get_tagger() — slow (initialises Tagger):")
    t0 = time.time()
    _get_tagger()
    print(f"  elapsed: {(time.time()-t0)*1000:.1f}ms")

    print("\nSecond call to _get_tagger() — instant (cached):")
    t0 = time.time()
    _get_tagger()
    print(f"  elapsed: {(time.time()-t0)*1000:.2f}ms")

    print("\nThird call (from chunk_japanese):")
    result = chunk_japanese("alpha beta gamma delta epsilon")
    print(f"  chunks: {result}")

    info = _get_tagger.cache_info()
    print(f"\ncache_info(): {info}")
    print(f"  hits={info.hits}   ← returned cached instance {info.hits} times")
    print(f"  misses={info.misses} ← actually ran __init__ {info.misses} time")
    assert info.misses == 1, "Tagger should only be initialised once"
    assert info.hits >= 2,   "Should have at least 2 cache hits"
    print("\nAll assertions passed.")


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/worker/chunking/japanese.py
==========================================================

REMOVE these lines at the top of the file:
    tagger = fugashi.Tagger()

ADD this function after the imports:
    @lru_cache(maxsize=1)
    def _get_tagger() -> fugashi.Tagger:
        return fugashi.Tagger()

CHANGE inside chunk_japanese():
    # before:
    tokens = [w.surface for w in tagger(text)]

    # after:
    tokens = [w.surface for w in _get_tagger()(text)]

Also add to imports at top:
    from functools import lru_cache

VERIFY:
    python -c "
    from worker.chunking.japanese import _get_tagger, chunk_japanese
    chunk_japanese('テスト')
    chunk_japanese('もう一度')
    print(_get_tagger.cache_info())   # should show misses=1
    "
"""


if __name__ == "__main__":
    print(__doc__)
    demo_before()
    demo_after()
    print(APPLY_DIFF)
