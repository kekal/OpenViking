---
name: viking-memory
description: >
  Save and recall decisions, fixes, and preferences in OpenViking long-term memory.
  Trigger: "remember this", "what did we decide about...", "have we fixed this before",
  "what are my preferences", at the start of a session on a known project.
allowed-tools: Bash
---

# Viking Memory — Save and Recall Context

## Quick save (one-shot, no session needed)

Save a specific insight, decision, or preference in one command:

```bash
ov add-memory "We decided to use connection pooling because creating new DB connections per request caused timeouts under load"
```

This creates a session, adds the message, and commits automatically.
Viking extracts structured memories to `viking://user/memories/` and `viking://agent/memories/`.

## Search user memories (preferences, decisions)

```bash
curl -s -X POST http://localhost:1933/api/v1/search/find \
  -H "Content-Type: application/json" \
  -d '{"query": "<what you are looking for>", "target_uri": "viking://user/memories/", "limit": 5}'
```

## Search agent memories (task patterns, solutions)

```bash
curl -s -X POST http://localhost:1933/api/v1/search/find \
  -H "Content-Type: application/json" \
  -d '{"query": "<what you are looking for>", "target_uri": "viking://agent/memories/", "limit": 5}'
```

## Browse saved memories

```bash
# List user memories
curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://user/memories/"

# List agent memories
curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://agent/memories/"
```

## Read a specific memory

```bash
# Abstract first (cheapest)
curl -s "http://localhost:1933/api/v1/content/abstract?uri=<memory-uri>"

# Full content if relevant
curl -s "http://localhost:1933/api/v1/content/read?uri=<memory-uri>"
```

## Link memories to code (relations)

Connect a memory to the code it references so they surface together in searches:

```bash
ov link viking://agent/memories/case_xxx viking://resources/<project>/src/services --reason "Auth refactor fix"

# See what's linked to a resource
ov relations viking://resources/<project>/src/services
```

## When to use

- **Save now (`ov add-memory`):** After a design decision, tricky bug fix, discovered gotcha
- **Recall (search):** At session start, before architectural choices, when a bug feels familiar
- **Link (relations):** When a memory relates to specific code, connect them for better retrieval
