# Domain 3 Exercise — CLAUDE.md Hierarchy

## What this folder is

A practice workspace to understand how CLAUDE.md files compose across three levels:

```
~/.claude/CLAUDE.md                        ← user-level   (applies to ALL projects)
cert-practice/CLAUDE.md                    ← project-level (this file)
cert-practice/domain3_claude_code_config/  ← directory-level (most specific)
```

**Precedence**: directory > project > user. More specific wins on conflicts.

---

## Exercise 3.1 — Build the Hierarchy

**TODO — create these two files:**

1. `~/.claude/CLAUDE.md` — user-level rules that apply everywhere:
   - Always respond in the same language the user writes in
   - Never commit secrets or API keys
   - Prefer explicit error messages over silent failures

2. `domain3_claude_code_config/CLAUDE.md` — directory-level rules that OVERRIDE for this folder:
   - Use Python type hints on all function signatures
   - Run `python -m pytest` before reporting any task as complete
   - For any TODO in an exercise file, implement it, don't describe it

**Question**: If your user-level CLAUDE.md says "use 2-space indentation" but
this project-level file says "use 4-space indentation", which wins? Why?

**Answer**: TODO

---

## Exercise 3.2 — @import Syntax

Split rules into topic files using `@import`. This file already does it:

@import .claude/rules/style.md
@import .claude/rules/testing.md

**TODO — create those two files** in `.claude/rules/`:
- `style.md`: code style rules (formatting, naming conventions)
- `testing.md`: testing rules (when to write tests, how to name them)

---

## Project-Level Rules (active now)

- This is a cert practice workspace — every TODO in an exercise must be implemented, not described
- Python files: include a `if __name__ == "__main__":` block that demonstrates the exercise
- After implementing any exercise, run it and verify the output makes sense
