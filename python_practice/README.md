# Python Practice
## Java Developer → FDE / Applied AI Engineer

**Context**: The `ai-project` codebase contains correct Python — written by Claude Code, not by you. These scripts transfer ownership of each pattern to you through runnable demos and hands-on exercises.

---

## Contents

### Reference docs (read first)
| File | Purpose |
|---|---|
| `01_Skills_Guide.md` | All 6 priority patterns explained with Java analogies |
| `02_Exercises.md` | Full exercise descriptions with apply-to-ai-project instructions |

### Scripts
| File | Pattern | Depends | Time |
|---|---|---|---|
| `scripts/00_skills_guide.py` | All 6 priorities — runnable demos | stdlib | ~20 min |
| `scripts/ex01_lru_cache.py` | `@lru_cache` | stdlib | 15 min |
| `scripts/ex02_async_generator.py` | Async generator (capstone) | `anthropic` optional | 30 min |
| `scripts/ex03_contextmanager.py` | `@contextmanager` | stdlib | 20 min |
| `scripts/ex04_field_validator.py` | `@field_validator` Pydantic v2 | `pydantic` | 20 min |
| `scripts/ex05_match_case.py` | `match/case` | stdlib, Python 3.10+ | 15 min |
| `scripts/ex06_typeddict.py` | `TypedDict` | stdlib | 15 min |
| `scripts/ex07_partial.py` | `functools.partial` | stdlib | 10 min |
| `scripts/ex08_model_validator.py` | `@model_validator` Pydantic v2 | `pydantic` | 20 min |
| `scripts/ex09_async_generator_rewrite.py` | Async generator from memory (fluency test) | stdlib | 30 min |

---

## How to Use

**Step 1 — Install dependencies** (once):
```bash
pip install pydantic anthropic
```

**Step 2 — Run the skills guide** to see all patterns in action:
```bash
cd Python_Practice/scripts
python 00_skills_guide.py
```

**Step 3 — Work through exercises in order**:
```bash
python ex01_lru_cache.py
python ex02_async_generator.py          # mock mode — no API key needed
python ex03_contextmanager.py
python ex04_field_validator.py
python ex05_match_case.py
python ex06_typeddict.py
python ex07_partial.py
python ex08_model_validator.py
python ex09_async_generator_rewrite.py  # write your implementation first
```

**Step 4 — Apply changes to ai-project**:
Each script ends with an `APPLY_DIFF` section showing exactly what to change in the target file.

**Step 5 — Run ex02 live** (after applying your implementation):
```bash
ANTHROPIC_API_KEY=sk-ant-... python ex02_async_generator.py --live
```

---

## Each Script Structure

Every exercise script follows the same layout:
1. **Docstring** — pattern, target file, time, problem statement, Java analogy
2. **Demo functions** — runnable examples with printed output
3. **`APPLY_DIFF`** — exact changes to make in the `ai-project` file
4. **`if __name__ == "__main__":`** — runs all demos

---

## Connection to 1Month_FDE_Plan.md

| Script | Plan section |
|---|---|
| `ex01_lru_cache.py` | Python Fluency Track — Level 1 |
| `ex02_async_generator.py` | Python Fluency Track — Capstone |
| `ex03_contextmanager.py` | Python Fluency Track — Level 1 |
| `ex04_field_validator.py` | Python Fluency Track — Level 3 |
| `ex05_match_case.py` | Python Fluency Track — Level 2 |
| `ex06_typeddict.py` | Python Fluency Track — Level 2 |
| `ex07_partial.py` | Week 4 eval — A/B chunk size comparison |
| `ex08_model_validator.py` | Python Fluency Track — Level 3 |
| `ex09_async_generator_rewrite.py` | Python Fluency Track — Capstone |

---

## Time Estimate

| Session | Scripts | Time |
|---|---|---|
| Session 1 | `00_skills_guide.py`, `ex01`, `ex02`, `ex03` | ~1.5 hrs |
| Session 2 | `ex04`, `ex05`, `ex06`, `ex07` | ~1.5 hrs |
| Session 3 | `ex08`, `ex09` + apply all changes to ai-project | ~1.5 hrs |
| **Total** | | **~4.5 hrs** |
