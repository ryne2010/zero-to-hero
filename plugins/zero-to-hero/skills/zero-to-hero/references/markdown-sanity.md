# Markdown sanity policy

Canonical skill docs must be readable by humans and agents. Markdown files should use balanced fenced code blocks, should not include language-tagged fences as closing fences, and should avoid nested code fences unless the outer fence uses a longer delimiter.

This matters because Codex often copies prompts and command blocks directly from docs. Broken fences can merge instructions, commands, and prose into ambiguous context.

Run:

```bash
python scripts/markdown_sanity_check.py .
```

The checker is intentionally lightweight. It does not enforce stylistic Markdown preferences; it only rejects structural problems that can confuse agent execution.
