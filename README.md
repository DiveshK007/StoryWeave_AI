# StoryWeave AI
Minimal RAG + LLM story tool. Ingest markdown knowledge → generate outline → expand scenes → export.

## Local run
cd services/orchestrator
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export USE_MOCK=1
uvicorn app.main:app --reload --port 8080
# open: http://127.0.0.1:8080/static/index.html

## API
POST /ingest            # multipart .md files
POST /generate_outline  # {premise, genre?, length?}
POST /expand_scene      # {outline, scene_index, protagonist}
POST /export            # {outline, scenes[]} → .txt

## NVIDIA (optional)
# put secrets in ~/.nim.env, then:
source ~/.nim.env
export USE_MOCK=0
uvicorn app.main:app --reload --port 8080

## Layout
services/orchestrator/app  # FastAPI, retrieval, UI
demo_corpus                # sample md files
projects                   # local outputs (gitignored)
