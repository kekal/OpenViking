---
name: viking-multiagent
description: >
  Multi-agent coordination via OpenViking sessions and shared memory.
  Trigger: at session start, at session end, when working alongside other agents,
  when switching tasks/issues.
allowed-tools: Bash
---

# Viking Multi-Agent — Session Protocol

## How it works

All agents on the same task share **one Viking session**. Each agent adds messages
to the shared session. When the task is done, committing the session extracts
persistent memories that survive forever.

```
EPHEMERAL (during work)                  PERSISTENT (after commit)
───────────────────────                  ─────────────────────────
viking://session/<session-id>/           viking://agent/.../memories/cases/
├── messages.jsonl        ──commit──►    ├── mem_xxx.md  (auto-extracted)
                                         viking://user/.../memories/
                                         ├── preferences/
                                         └── events/
```

After commit, the session can be deleted. Extracted memories are permanent and searchable.

## Task START — first agent creates the session

### 1. Search for context from past tasks

```bash
curl -s -X POST http://localhost:1933/api/v1/search/find \
  -H "Content-Type: application/json" \
  -d '{"query": "<task description or issue ID>", "target_uri": "viking://agent/", "limit": 5}'
```

### 2. Create a shared session

One agent creates the session. All other agents on the same task use this session ID.

```bash
SESSION_ID=$(curl -s -X POST http://localhost:1933/api/v1/sessions \
  -H "Content-Type: application/json" -d '{}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['result']['session_id'])")

echo "Session ID: $SESSION_ID"
```

Share this `SESSION_ID` with all agents working on the task.

### 3. Agent registers itself

Each agent adds a message announcing what it will work on:

```bash
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"role":"assistant","content":"Agent starting. Task: <issue ID>. Working on: <description>. Key files: <list>."}'
```

## DURING work — agents add to shared session

Each agent writes significant findings, decisions, and progress to the shared session:

```bash
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"role":"assistant","content":"Decision: <what was decided and why>. Files changed: <list>. Status: <in progress / done>."}'
```

Write a message when:
- Making an architectural or design decision
- Completing a significant piece of work
- Encountering a gotcha or unexpected behavior
- Changing shared files that other agents might touch

## Task END — commit session to persistent memory

When the task/issue is resolved:

### 1. Final agent writes completion summary

```bash
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{"role":"assistant","content":"Task complete.\n\nDone:\n- <what was completed>\n\nDecisions:\n- <key decisions and rationale>\n\nFiles changed:\n- <list>\n\nNotes for future:\n- <gotchas, warnings, context>"}'
```

### 2. Commit — extracts persistent memories

```bash
curl -s -X POST "http://localhost:1933/api/v1/sessions/$SESSION_ID/commit"
```

Viking's LLM reads the full session, extracts cases/patterns/preferences, and writes
them to `viking://agent/.../memories/` and `viking://user/.../memories/`.
These persist forever and are searchable by future sessions.

### 3. Delete the session (cleanup)

```bash
curl -s -X DELETE "http://localhost:1933/api/v1/sessions/$SESSION_ID"
```

The session artifacts are gone. The extracted memories remain.

## Switching tasks (user moves to a different issue)

1. **Commit current session** (steps above) — extracts memories
2. **Delete current session** — cleanup
3. **Create new session** for the new task — fresh start
4. **Search past memories** — the new session can find context from the old task via search

## Checking what other agents are doing

Read the current session's messages to see what's been done:

```bash
curl -s "http://localhost:1933/api/v1/sessions/$SESSION_ID" \
  -H "Content-Type: application/json"
```

## Conflict avoidance

Before editing a file, search the current session for claims:

```bash
curl -s -X POST http://localhost:1933/api/v1/search/grep \
  -H "Content-Type: application/json" \
  -d '{"pattern": "UserService.cs", "uri": "viking://session/"}'
```
