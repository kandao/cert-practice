"""
Exercise 3 — @contextmanager
=============================
Pattern  : contextlib.contextmanager
Target   : ai-project/agent/tools/retrieval.py
Time     : 20 min
Depends  : stdlib only (sqlite3 stands in for psycopg2)

PROBLEM
-------
hybrid_retrieval() in retrieval.py opens a psycopg2 connection and calls
conn.close() manually in a try/except block. This mixes resource management
with business logic, and the pattern must be repeated in every function that
needs a cursor.

YOUR TASK
---------
1. Run this script — observe that 'finally' always runs, even on exception.
2. Open ai-project/agent/tools/retrieval.py.
3. Add _pg_cursor(url) using @contextmanager (see APPLY_DIFF below).
4. Refactor hybrid_retrieval() to use it.

JAVA ANALOGY
------------
try-with-resources:
    try (Connection conn = dataSource.getConnection();
         PreparedStatement ps = conn.prepareStatement(sql)) {
        ResultSet rs = ps.executeQuery();
        // process rs
    }  // conn and ps auto-closed here, even on exception

Python @contextmanager does the same, explicitly.
The 'yield' is where the with-block body runs.
'finally' is the auto-close — always executes.
"""

import sqlite3
import tempfile
import os
from contextlib import contextmanager


# ── The pattern ───────────────────────────────────────────────────────────────

@contextmanager
def db_cursor(db_path: str):
    """
    @contextmanager turns a generator function into a context manager.

    Structure:
        setup code           ← __enter__ equivalent
        yield <value>        ← with-block runs here; <value> is what 'as x' receives
        teardown in finally  ← __exit__ equivalent; ALWAYS runs

    The caller never sees the connection — they only get the cursor.
    Resource management is fully encapsulated.
    """
    conn = sqlite3.connect(db_path)
    print(f"  [open]  connection to {os.path.basename(db_path)}")
    try:
        yield conn.cursor()         # caller's with-block runs here
    finally:
        conn.close()                # runs even if caller raised an exception
        print(f"  [close] connection closed")


# ── Demo 1: normal exit ───────────────────────────────────────────────────────

def demo_normal(db_path: str):
    print("\n--- Demo 1: normal exit ---")
    with db_cursor(db_path) as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, title TEXT)")
        cur.execute("INSERT INTO docs (title) VALUES (?)", ("RAG overview",))
        cur.execute("SELECT title FROM docs")
        row = cur.fetchone()
        print(f"  inside with-block: fetched '{row[0]}'")
    print("  after with-block: connection is closed")


# ── Demo 2: exception inside with-block ──────────────────────────────────────

def demo_exception(db_path: str):
    print("\n--- Demo 2: exception inside with-block ---")
    print("  Expecting: [open] ... error raised ... [close] ... exception caught")
    try:
        with db_cursor(db_path) as cur:
            cur.execute("SELECT title FROM docs")
            print(f"  inside with-block, about to raise...")
            raise RuntimeError("simulated query error")
    except RuntimeError as e:
        print(f"  exception caught: {e}")
    print("  Key: '[close]' printed BEFORE this line — finally always runs")


# ── Demo 3: without @contextmanager (the problem) ────────────────────────────

def demo_without_cm(db_path: str):
    print("\n--- Demo 3: without @contextmanager (manual try/finally) ---")
    conn = sqlite3.connect(db_path)
    print(f"  [open]  manual connection")
    try:
        cur = conn.cursor()
        cur.execute("SELECT title FROM docs")
        row = cur.fetchone()
        print(f"  fetched: '{row[0]}'")
        # imagine more business logic here...
        # imagine 5 more functions that each repeat this pattern...
    finally:
        conn.close()
        print(f"  [close] manual close")
    print("  Problem: every function that needs a cursor must repeat try/finally")


# ── Demo 4: stacking context managers ────────────────────────────────────────

def demo_stacking(db_path: str):
    print("\n--- Demo 4: stacking — two context managers in one with ---")

    @contextmanager
    def timer(label: str):
        import time
        t = time.time()
        yield
        print(f"  [{label}] elapsed: {(time.time()-t)*1000:.1f}ms")

    with db_cursor(db_path) as cur, timer("query"):
        cur.execute("SELECT title FROM docs")
        rows = cur.fetchall()
        print(f"  fetched {len(rows)} rows")
    # Both context managers' finally blocks run on exit


# ── Apply to ai-project ───────────────────────────────────────────────────────

APPLY_DIFF = """
CHANGES TO MAKE in ai-project/agent/tools/retrieval.py
=======================================================

ADD at the top, after existing imports:
    from contextlib import contextmanager

ADD this function before hybrid_retrieval():
    @contextmanager
    def _pg_cursor(url: str):
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(url)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                yield cur
        finally:
            conn.close()

CHANGE inside hybrid_retrieval() — replace the try block:
    # BEFORE:
    try:
        conn = psycopg2.connect(url)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (...))
            rows = cur.fetchall()
        conn.close()
    except Exception as e:
        return f"Database error: {e}"

    # AFTER:
    try:
        with _pg_cursor(url) as cur:
            cur.execute(sql, (...))
            rows = cur.fetchall()
    except Exception as e:
        return f"Database error: {e}"
"""


if __name__ == "__main__":
    print(__doc__)

    # Use a temp DB so the script is fully self-contained
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        demo_normal(db_path)
        demo_exception(db_path)
        demo_without_cm(db_path)
        demo_stacking(db_path)
    finally:
        os.unlink(db_path)

    print(APPLY_DIFF)
