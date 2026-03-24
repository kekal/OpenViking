---
name: viking-status
description: >
  Check OpenViking health, processing queue, and what's indexed.
  Trigger: "is viking running", "check viking status", "what's indexed",
  "is indexing done", at the start of any session.
allowed-tools: Bash
---

# Viking Status — Health and Diagnostics

## Quick health check

```bash
curl -s http://localhost:1933/health
```

Returns `{"healthy": true}` if server is running.

## Full system status

```bash
curl -s http://localhost:1933/api/v1/system/status
```

## What's indexed

```bash
curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://resources/"
```

## Processing queue (is indexing done?)

Use the CLI for a formatted view:

```bash
ov status
```

Or via API — check the observer queue:

```bash
curl -s http://localhost:1933/api/v1/observer/queue
```

When all queues show `Pending: 0` and `In Progress: 0`, processing is complete.

## Detailed observer diagnostics

```bash
curl -s http://localhost:1933/api/v1/observer/vlm           # VLM (language model) status
curl -s http://localhost:1933/api/v1/observer/vikingdb       # vector database status
curl -s http://localhost:1933/api/v1/observer/transaction    # transaction status
curl -s http://localhost:1933/api/v1/observer/retrieval      # retrieval stats
curl -s http://localhost:1933/api/v1/observer/system         # system metrics (CPU, memory, disk)
```

## Wait for processing to complete

```bash
curl -s -X POST http://localhost:1933/api/v1/system/wait \
  -H "Content-Type: application/json" \
  -d '{"timeout": 120}'
```

## Session start checklist

1. `curl -s http://localhost:1933/health` — server alive?
2. `curl -s "http://localhost:1933/api/v1/fs/ls?uri=viking://resources/"` — what's indexed?
3. Search for relevant past context (see viking-memory skill)
