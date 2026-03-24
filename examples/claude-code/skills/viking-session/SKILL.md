---
name: viking-session
description: >
  Save conversation context to OpenViking long-term memory.
  Trigger: "save this session", "remember what we discussed", "commit to memory",
  at the end of a coding session, after solving a bug or making decisions.
  For quick single insights, prefer viking-memory's "ov add-memory" instead.
allowed-tools: Bash
---

# Viking Session — Save Context to Memory

## When to use sessions vs add-memory

| Scenario | Use |
|----------|-----|
| Save a single insight or decision | `ov add-memory "..."` (see viking-memory skill) |
| Track a multi-step task with multiple findings | Session workflow below |
| Multi-agent coordination | Session workflow (see viking-multiagent skill) |

## Why

When a session ends, valuable context is lost. Viking session commit extracts
decisions, fixes, and patterns into long-term memory for future sessions.

## Quick one-shot memory save

For saving a specific insight, skip sessions entirely:

```bash
ov add-memory "We decided to use async polling because synchronous calls blocked the UI thread"
```

## Full session workflow

### Step 1 — Create session

```bash
SESSION_ID=$(curl -s -X POST http://localhost:1933/api/v1/sessions \
  -H "Content-Type: application/json" -d '{}' | python -c "import sys,json;print(json.load(sys.stdin)['result']['session_id'])")
```

### Step 2 — Add messages

```bash
# User message
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":[{"type":"text","text":"<user message>"}]}'

# Assistant message
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"role":"assistant","content":[{"type":"text","text":"<assistant response>"}]}'
```

### Step 3 — Commit at session end

```bash
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/commit"
```

Viking extracts: bug fixes, architectural decisions, user preferences, key patterns.
Writes to `viking://user/memories/` and `viking://agent/memories/`.

### Step 4 — Cleanup

```bash
curl -s -X DELETE "http://localhost:1933/api/v1/sessions/$SESSION_ID"
```
