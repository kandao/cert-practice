---
description: Review a file for correctness and suggest improvements
context: fork
allowed-tools: Read, Grep, Glob
argument-hint: <file-path>
---

# Exercise 3.4 — Skill with SKILL.md Frontmatter

**Exam focus**:
- `context: fork` → skill runs in an isolated session; changes don't affect main conversation
- `allowed-tools` → restricts which tools the skill can call (principle of least privilege)
- `argument-hint` → shown in the UI autocomplete when the user types `/review`
- Skills differ from commands: skills have frontmatter; commands are plain markdown prompts

---

## Skill body

Read the file at $ARGUMENTS. Review it for:
1. Correctness — does the logic do what the docstring claims?
2. Anti-patterns — list any patterns that would be wrong answers on the cert exam
3. Missing TODOs — list any unimplemented sections

Return findings as a numbered list. Be specific about line numbers.

---

## TODO — fill in these answers

**Q1**: This skill has `context: fork`. If the user runs `/review ex1_agent_loop.py`
and the skill reads that file, will those Read tool calls appear in the main
conversation history?

**Answer**: TODO

**Q2**: Why is `allowed-tools: Read, Grep, Glob` appropriate here instead of allowing all tools?

**Answer**: TODO

**Q3**: You want to add a skill that can edit files. What field do you change, and what's the risk?

**Answer**: TODO
