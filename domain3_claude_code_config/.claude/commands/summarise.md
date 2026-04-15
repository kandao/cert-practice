# Exercise 3.3 — Custom Slash Command

This file defines a `/summarise` slash command for this project.

**Exam focus**:
- Custom commands live in `.claude/commands/<name>.md`
- They are project-scoped (committed to the repo, shared with team)
- The command body is a prompt template — `$ARGUMENTS` is replaced with what the user types
- Skills (`.claude/skills/`) differ: they have SKILL.md frontmatter and support `context: fork`

---

## Command definition

Summarise the following in 3 bullet points, then give a one-sentence "so what":

$ARGUMENTS

---

## TODO — answer these questions in this file

**Q1**: A teammate wants a `/deploy` command that only they use (not the team).
Where should they put it and in what file?

**Answer**: TODO

**Q2**: You want a command that runs in a forked context so it doesn't pollute
the main conversation history. Should you use a command or a skill? Why?

**Answer**: TODO

**Q3**: What is the `argument-hint` field in SKILL.md frontmatter used for?

**Answer**: TODO
