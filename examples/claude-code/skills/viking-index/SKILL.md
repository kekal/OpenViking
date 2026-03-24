---
name: viking-index
description: >
  Add or re-index content in the OpenViking knowledge base.
  Trigger: "index this", "add to viking", "re-index after changes".
allowed-tools: Bash
---

# Viking Index — Adding Resources

## Index a local directory

```bash
curl -s -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project",
    "reason": "Project codebase",
    "ignore_dirs": "node_modules,dist,.git,build",
    "strict": false
  }'
```

## Index with blocking (wait for processing)

```bash
curl -s -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project/src",
    "reason": "Source code",
    "strict": false,
    "wait": true
  }'
```

Use `"wait": true` for small directories only. For large codebases, omit and poll status.

## Wait for background processing

```bash
curl -s -X POST http://localhost:1933/api/v1/system/wait \
  -H "Content-Type: application/json" \
  -d '{"timeout": 120}'
```

## Check status

```bash
curl -s http://localhost:1933/health
```

## Re-index specific files after changes

Use the `reindex` endpoint to target a specific URI without re-adding the whole resource:

```bash
# Re-index a single file
curl -s -X POST http://localhost:1933/api/v1/content/reindex \
  -H "Content-Type: application/json" \
  -d '{"uri": "viking://resources/<project>/src/app.ts"}'

# Force regeneration of abstracts/overviews
curl -s -X POST http://localhost:1933/api/v1/content/reindex \
  -H "Content-Type: application/json" \
  -d '{"uri": "viking://resources/<project>/src", "regenerate": true, "wait": true}'
```

## Re-index the whole codebase

`add-resource` only processes new/changed files. Just re-run:

```bash
curl -s -X POST http://localhost:1933/api/v1/resources \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/project", "reason": "Updated code", "strict": false}'
```

## Force full re-index (nuclear option)

Delete first via CLI then re-add:
```bash
ov rm -r viking://resources/<project>
```

## Export / Import knowledge base

```bash
# Backup
ov export viking://resources/<project> /path/to/backup.viking

# Restore
ov import /path/to/backup.viking viking://resources/<project>
```
