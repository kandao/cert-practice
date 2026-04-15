"""
Domain 5.3–5.5 — Multi-Pass Review + Context Recovery
=======================================================
Implement a review pipeline that avoids same-session self-review bias
and recovers gracefully when a subagent fails mid-task.

EXAM FOCUS:
- Self-review limitation: if you ask the same session that generated output
  to review it, it retains its reasoning context and tends to agree with itself
- Multi-pass solution: separate passes (or sessions) for local vs cross-file analysis
  Pass 1 — per-file: analyse each file independently, no cross-file knowledge
  Pass 2 — integration: given ALL pass-1 summaries, find cross-file issues
- Context degradation: in long sessions the model loses track of early context;
  use scratchpad files or /compact for extended tasks
- Local recovery: a subagent should attempt local recovery BEFORE escalating
  to the coordinator — don't escalate on every error
- Partial results: if a subagent fails partway through, return what it completed
  with a clear "partial_result" flag so the coordinator can decide what to do

TASK:
  Part A: implement two-pass code review (per-file then cross-file)
  Part B: implement a subagent that recovers locally and reports partial results
"""

import anthropic
import json

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"


# --- Part A: Two-Pass Review --------------------------------------------------

def review_single_file(filename: str, content: str) -> dict:
    """
    Pass 1 — local analysis. Reviews ONE file in isolation.
    No knowledge of other files.

    Returns: {"filename": str, "issues": list[str], "summary": str}

    TODO: call the API with a system prompt focused on LOCAL analysis only.
    System prompt must say: "Review this single file in isolation.
    Do not speculate about other files. Focus on: logic errors, missing edge cases,
    anti-patterns."
    Return parsed JSON matching the schema above.
    """
    raise NotImplementedError


def review_cross_file(file_summaries: list[dict]) -> dict:
    """
    Pass 2 — integration analysis. Gets ALL pass-1 summaries.
    Looks for cross-file issues: interface mismatches, duplicated logic,
    inconsistent error handling.

    Returns: {"cross_file_issues": list[str], "severity": "low"|"medium"|"high"}

    TODO: call the API with a NEW session (not continuing from pass 1).
    Pass all file_summaries as context in a single user message.
    System prompt: "You are reviewing the INTEGRATION between files.
    Given per-file summaries, identify: interface mismatches, duplicate logic,
    inconsistent patterns across files."

    ANTI-PATTERN — do NOT do this:
        # Asking the same session that wrote the code to review it
        messages.append({"role": "user", "content": "Now review your own output"})
    """
    raise NotImplementedError


# --- Part B: Subagent with Local Recovery + Partial Results -------------------

def process_files_with_recovery(file_list: list[str]) -> dict:
    """
    Process a list of files. If one fails, attempt local recovery once.
    If recovery fails, record it as a partial result and continue with the rest.
    Never escalate on first error.

    Returns:
    {
        "completed": [{"filename": str, "result": dict}],
        "failed":    [{"filename": str, "error": str, "partial_result": dict | None}],
        "is_partial": bool   # True if any file failed
    }

    TODO: implement with try/except around each file.
    On first failure: retry once with a simpler prompt (local recovery).
    On second failure: append to "failed" with partial_result=None and continue.

    ANTI-PATTERN — do NOT do this:
        try:
            result = process(file)
        except Exception:
            raise  # escalating immediately, no local recovery attempt
    """
    completed = []
    failed = []

    for filename in file_list:
        # Simulated file content
        content = f"# {filename}\ndef process(): pass"

        try:
            result = review_single_file(filename, content)
            completed.append({"filename": filename, "result": result})
        except Exception as first_error:
            # TODO: attempt local recovery (simpler prompt, smaller content)
            try:
                # Recovery attempt: ask for just a one-line summary instead
                recovery_result = None  # TODO: implement recovery call
                completed.append({"filename": filename, "result": recovery_result})
            except Exception as second_error:
                failed.append({
                    "filename": filename,
                    "error": str(second_error),
                    "partial_result": None,
                })

    return {
        "completed": completed,
        "failed": failed,
        "is_partial": len(failed) > 0,
    }


# --- Run ----------------------------------------------------------------------

SAMPLE_FILES = {
    "auth.py": """
def login(username, password):
    # No input validation
    query = f"SELECT * FROM users WHERE username='{username}'"
    return db.execute(query)
""",
    "api.py": """
from auth import login

def handle_request(data):
    user = login(data['user'], data['pass'])
    # Returns None if login fails, but callers expect a dict
    return {"status": "ok", "user": user}
""",
    "utils.py": """
def login(u, p):  # duplicate function name — different signature from auth.py
    return {"user": u}
""",
}

if __name__ == "__main__":
    print("=== Pass 1: Per-file analysis ===")
    summaries = []
    for filename, content in SAMPLE_FILES.items():
        summary = review_single_file(filename, content)
        summaries.append(summary)
        print(f"\n{filename}:")
        for issue in summary.get("issues", []):
            print(f"  - {issue}")

    print("\n=== Pass 2: Cross-file integration ===")
    cross = review_cross_file(summaries)
    print(f"Severity: {cross.get('severity')}")
    for issue in cross.get("cross_file_issues", []):
        print(f"  - {issue}")

    print("\n=== Recovery demo ===")
    result = process_files_with_recovery(list(SAMPLE_FILES.keys()))
    print(f"Completed: {len(result['completed'])} files")
    print(f"Failed:    {len(result['failed'])} files")
    print(f"Partial:   {result['is_partial']}")
