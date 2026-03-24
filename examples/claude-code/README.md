# Claude Code Integration

Connect Claude Code CLI to OpenViking for semantic code summarisation, progressive context loading, and long-term memory across sessions.

## Prerequisites

- OpenViking server set up on `http://localhost:1933`
- Claude Code installed (`claude` CLI in PATH)

## Setup

### 1. Configure the OpenViking server

Copy the example config and edit paths:
```bash
mkdir -p ~/.openviking
cp config/ov.conf.example ~/.openviking/ov.conf
cp config/ovcli.conf.example ~/.openviking/ovcli.conf
```

Edit `~/.openviking/ov.conf`:
- Set `storage.workspace` to your desired workspace path
- The default uses Ollama for embeddings and `claude` CLI for the VLM

### 2. Install Ollama and pull the embedding model

```bash
# Install from https://ollama.com, then:
ollama pull nomic-embed-text
```

### 3. Start the stack

**Windows:**
```cmd
scripts\up.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/up.sh scripts/down.sh
./scripts/up.sh
```

### 4. Set up your project

Copy `CLAUDE.md.example` to your project root as `CLAUDE.md` and edit the
`<project>` placeholders to match your resource name in Viking:
```bash
cp CLAUDE.md.example /path/to/your/project/CLAUDE.md
```

Copy skills to your project's `.claude/skills/` directory:
```bash
cp -r skills/* /path/to/your/project/.claude/skills/
```

### 5. Index your codebase

```bash
ov add-resource /path/to/your/project --no-strict --ignore-dirs "node_modules,dist,.git,build"
```

## What's included

```
claude-code/
├── CLAUDE.md.example                  <- Agent instructions template (copy to project root)
├── README.md                          <- This file
├── config/
│   ├── ov.conf.example                <- Server config (Ollama embeddings + claude-code VLM)
│   └── ovcli.conf.example             <- CLI config
├── scripts/
│   ├── up.bat / up.sh                 <- Start Ollama + OpenViking
│   ├── down.bat / down.sh             <- Stop Ollama + OpenViking
│   └── start-server.vbs               <- Windows: run server as hidden process
└── skills/
    ├── viking-find/SKILL.md           <- Semantic + grep search
    ├── viking-browse/SKILL.md         <- ls, tree, abstract, overview
    ├── viking-index/SKILL.md          <- Add/re-index resources
    ├── viking-session/SKILL.md        <- Save session to long-term memory
    ├── viking-memory/SKILL.md         <- Recall past decisions
    ├── viking-multiagent/SKILL.md     <- Multi-agent coordination via sessions
    └── viking-status/SKILL.md         <- Health check and diagnostics
```

## How it works

No MCP server or proxy needed. Claude calls the OpenViking REST API directly via `curl` in Bash. The skills teach Claude the correct endpoints and workflows.

### Progressive context loading

Instead of reading entire files, Claude loads context in layers:
- **L0 Abstract** (~100 tokens) — one-sentence summary, cheapest relevance check
- **L1 Overview** (~2k tokens) — structured overview, read before committing to full load
- **L2 Full Read** — complete file content, only when confirmed relevant

### Long-term memory

Sessions can be committed to Viking memory, allowing future sessions to recall past decisions, bug fixes, and preferences.

## API endpoints used

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Semantic search | POST | `/api/v1/search/find` |
| Text search | POST | `/api/v1/search/grep` |
| List directory | GET | `/api/v1/fs/ls` |
| Directory tree | GET | `/api/v1/fs/tree` |
| L0 abstract | GET | `/api/v1/content/abstract` |
| L1 overview | GET | `/api/v1/content/overview` |
| L2 full read | GET | `/api/v1/content/read` |
| Add resource | POST | `/api/v1/resources` |
| Create session | POST | `/api/v1/sessions` |
| Add message | POST | `/api/v1/sessions/{id}/messages` |
| Commit session | POST | `/api/v1/sessions/{id}/commit` |
| Health check | GET | `/health` |
| System status | GET | `/api/v1/system/status` |
