---
name: viking-find
description: >
  Search the OpenViking knowledge base. Use for discovering where something is
  implemented, finding classes/methods/patterns, understanding architecture.
  Prefer this over Grep/Glob for discovery in unfamiliar code.
allowed-tools: Bash
---

# Viking Find — Search

## Semantic search (natural language)

```bash
curl -s -X POST http://localhost:1933/api/v1/search/find \
  -H "Content-Type: application/json" \
  -d '{"query": "$QUERY", "limit": 5}'
```

Returns ranked URIs with scores. Higher score = more relevant.

## Scoped search (limit to subtree)

Use `target_uri` to avoid results from unrelated modules:

```bash
curl -s -X POST http://localhost:1933/api/v1/search/find \
  -H "Content-Type: application/json" \
  -d '{"query": "$QUERY", "target_uri": "viking://resources/<project>/src", "limit": 5}'
```

## VLM-powered search (complex questions)

For complex, multi-faceted questions use `search` endpoint which does intent analysis
and multi-query expansion:

```bash
curl -s -X POST http://localhost:1933/api/v1/search/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how does the auth pipeline validate tokens and refresh sessions?", "uri": "viking://resources/<project>"}'
```

Use `find` for simple lookups, `search` for architectural questions.

## Exact match search (known symbol names)

```bash
curl -s -X POST http://localhost:1933/api/v1/search/grep \
  -H "Content-Type: application/json" \
  -d '{"pattern": "$SYMBOL", "uri": "viking://resources/<project>"}'
```

Note: `uri` is required for grep. Add `"ignore_case": true` for case-insensitive.

## Glob pattern search (find files by name)

```bash
curl -s -X POST http://localhost:1933/api/v1/search/glob \
  -H "Content-Type: application/json" \
  -d '{"pattern": "**/*Service*.ts", "uri": "viking://resources/<project>"}'
```

## After getting results — progressive loading

1. Check abstract (cheapest): `curl -s "http://localhost:1933/api/v1/content/abstract?uri=<URI>"`
2. Load overview if promising: `curl -s "http://localhost:1933/api/v1/content/overview?uri=<URI>"`
3. Load full content only if confirmed relevant: `curl -s "http://localhost:1933/api/v1/content/read?uri=<URI>"`

| Abstract says... | Action |
|-----------------|--------|
| Clearly relevant | Load overview, then decide on full read |
| Possibly relevant | Load overview to confirm |
| Not relevant | Skip, try next URI |
| Empty abstract | Load overview instead (some files have empty L0) |
