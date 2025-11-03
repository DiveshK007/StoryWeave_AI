# Agentic AWS + NVIDIA NIM Demo

## Story Engine demo

### Load demo corpus
```bash
curl -X POST \
  -F "files=@demo_corpus/story_beats.md" \
  -F "files=@demo_corpus/tropes_and_archetypes.md" \
  -F "files=@demo_corpus/sci_fi_worldbuilding.md" \
  http://localhost:8080/ingest
```

### Generate outline
```bash
curl -X POST http://localhost:8080/generate_outline \
  -H "Content-Type: application/json" \
  -d '{"premise":"A stray cat becomes captain of a starship","genre":"sci-fi","length":"short"}'
```

### Expand a scene
```bash
curl -X POST http://localhost:8080/expand_scene \
  -H "Content-Type: application/json" \
  -d '{"outline":{"logline":"","beats":[{"title":"Hook","goal":"","conflict":"","outcome":""}]},"scene_index":0,"protagonist":"Nova"}'
```
