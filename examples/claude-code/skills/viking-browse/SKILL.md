---
name: viking-browse
description: >
  Navigate the OpenViking virtual filesystem. Use for orientation:
  "show me the structure of...", "what modules are in...",
  exploring unfamiliar directories, session start overview.
allowed-tools: Bash
---

# Viking Browse — Filesystem Navigation

## List directory contents

```bash
curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://resources/<project>"
```

## Directory tree (module overview)

```bash
# depth=1 for large directories (avoids huge JSON output)
curl -s "http://localhost:1933/api/v1/fs/tree?uri=viking://resources/<project>&depth=1"

# depth=2 only for smaller subdirectories
curl -s "http://localhost:1933/api/v1/fs/tree?uri=viking://resources/<project>/src&depth=2"
```

**Important:** Use `depth=1` for project root or large directories. Depth=2+ on large
dirs can produce 100KB+ JSON. Drill into subdirectories instead.

## Resource metadata

```bash
curl -s "http://localhost:1933/api/v1/fs/stat?uri=viking://resources/<project>/src"
```

## L0 abstract (fastest orientation, ~100 tokens)

```bash
curl -s "http://localhost:1933/api/v1/content/abstract?uri=viking://resources/<project>/src"
```

## L1 overview (planning context, ~2k tokens)

```bash
curl -s "http://localhost:1933/api/v1/content/overview?uri=viking://resources/<project>/src"
```

## Relations (cross-references between resources)

```bash
ov relations viking://resources/<project>/src/app.ts
```

## Workflow for unfamiliar module

1. `tree` at depth=1 — understand top-level structure
2. `abstract` on interesting subdirectory — one-sentence summary
3. `overview` on most relevant subdirectory — planning context
4. `find` with specific query — targeted file URIs
5. `read` only the confirmed-relevant files

## Key URIs

| Path | Contents |
|------|----------|
| `viking://resources/` | All indexed resources |
| `viking://resources/<project>/` | Project codebase root |
| `viking://user/memories/` | User preferences and decisions |
| `viking://agent/memories/` | Agent task memory |
