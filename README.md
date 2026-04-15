# Cert Practice — Claude Certified Architect

Hands-on exercises organized by exam domain. Each file is self-contained — no shared utilities.

| Domain | Weight | Folder |
|--------|--------|--------|
| 1. Agentic Architecture | ~25% | `domain1_agentic_architecture/` |
| 2. Tool Design & MCP | ~20% | `domain2_tool_design_mcp/` |
| 3. Claude Code Config | ~20% | `domain3_claude_code_config/` |
| 4. Prompt Engineering | ~20% | `domain4_prompt_engineering/` |
| 5. Context Management | ~15% | `domain5_context_management/` |

## How to use

Each exercise file has:
- A docstring explaining what you're building and why it matters for the exam
- Starter scaffolding
- `# TODO` markers for what you implement
- An `# ANTI-PATTERN` comment showing the wrong approach to recognise on the exam

Run each file directly: `python exercise_X.py`

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key
```
