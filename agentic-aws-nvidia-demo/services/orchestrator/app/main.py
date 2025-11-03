from fastapi import FastAPI, UploadFile, File
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from .settings import settings
from .retrieval import store
from .nim_client import call_llm

app = FastAPI(title='Agentic Orchestrator')

@app.post('/ingest')
async def ingest(files: List[UploadFile] = File(...)):
    paths = []
    for f in files:
        p = f"/tmp/{f.filename}"
        with open(p, 'wb') as out:
            out.write(await f.read())
        paths.append(p)
    store.ingest_docs(paths, settings.EMBED_URL)
    return {'ok': True, 'chunks': len(store.chunks)}

@app.get('/ask')
def ask(q: str):
    if not store.index:
        return {'error': 'no index; upload documents via /ingest first'}
    hits = store.search(q, settings.EMBED_URL, settings.TOP_K)
    ctx = '\n\n'.join([store.chunks[i] for i,_ in hits])
    prompt = (
        'Use the context to answer precisely. Cite key facts. '
        '\n\nContext:\n' + ctx + '\n\nQuestion: ' + q + '\nAnswer:'
    )
    text = call_llm(prompt, settings.LLM_URL, settings.MAX_TOKENS)
    return {'answer': text, 'matches': hits}

from pydantic import BaseModel
from typing import Optional
def check_beats_consistency(outline_json: dict) -> dict:
    issues = []
    beats = outline_json.get('beats', [])
    if len(beats) < 5:
        issues.append('Outline has fewer than 5 beats.')
    titles = [b.get('title','').lower() for b in beats]
    if not any('inciting' in t for t in titles):
        issues.append('Missing inciting incident.')
    return {'ok': len(issues)==0, 'issues': issues}

def check_continuity(prev_scenes: list, new_scene: dict) -> dict:
    names = []
    for sc in prev_scenes:
        n = sc.get('protagonist')
        if n:
            names.append(n)
    expected = names[0] if names else None
    if expected and new_scene.get('protagonist') and new_scene['protagonist'] != expected:
        return {'ok': False, 'issue': f'Protagonist changed from {expected} to {new_scene["protagonist"]}'}
    return {'ok': True}

class OutlineReq(BaseModel):
    premise: str
    genre: str = 'sci-fi'
    length: str = 'short'
    style: Optional[str] = None

@app.post('/generate_outline')
def generate_outline(req: OutlineReq):
    hits = store.search(f"{req.genre} story beats {req.premise}", settings.EMBED_URL, settings.TOP_K) if store.index else []
    ctx = '\n\n'.join([store.chunks[i] for i,_ in hits]) if hits else ''
    prompt = (
        f"You are a story planner. Premise: {req.premise}\nGenre: {req.genre}\nLength: {req.length}\n"
        f"Context:\n{ctx}\nReturn JSON with keys logline and beats (7 items max). Each beat: title, goal, conflict, outcome."
    )
    text = call_llm(prompt, settings.LLM_URL, 550)
    try:
        import json as _json
        outline = _json.loads(text)
    except Exception:
        outline = {'logline': req.premise, 'beats': [{'title':'Hook','goal':'','conflict':'','outcome':''}]}
    check = check_beats_consistency(outline)
    return {'outline': outline, 'consistency': check, 'matches': hits}

class SceneReq(BaseModel):
    outline: dict
    scene_index: int
    protagonist: Optional[str] = None
    style: Optional[str] = None

@app.post('/expand_scene')
def expand_scene(req: SceneReq):
    beats = req.outline.get('beats', [])
    idx = max(0, min(req.scene_index, len(beats)-1)) if beats else 0
    beat = beats[idx] if beats else {'title':'Scene','goal':'','conflict':'','outcome':''}
    prev = []
    continuity = check_continuity(prev, {'protagonist': req.protagonist or ''})
    prompt = (
        f"Expand the following beat into a cinematic scene. Beat: {beat}. "
        f"Style: {req.style or 'visceral, visual, concise action lines'}. "
        f"Write 10-15 sentences with clear start-middle-end. End with a one-line cliffhanger. "
    )
    text = call_llm(prompt, settings.LLM_URL, 700)
    return {'scene_text': text, 'continuity': continuity}


# serve /static
app.mount("/static", StaticFiles(directory="app/static"), name="static")
@app.post("/export", response_class=PlainTextResponse)
async def export_story(payload: dict):
    """
    Expects: {"outline": {...}, "scenes": ["...", "..."]}
    Returns: text/plain with download headers.
    """
    outline = payload.get("outline") or {}
    scenes = payload.get("scenes") or []

    lines = []
    lines.append("# Logline")
    lines.append((outline.get("logline") or "").strip())
    lines.append("\n# Beats")
    for i, b in enumerate(outline.get("beats", []), 1):
        lines.append(
            f"{i}. {b.get('title','')}: "
            f"goal={b.get('goal','')}; "
            f"conflict={b.get('conflict','')}; "
            f"outcome={b.get('outcome','')}"
        )

    lines.append("\n# Scenes")
    for i, s in enumerate(scenes, 1):
        lines.append(f"\n## Scene {i}\n{(s or '').strip()}")

    text = "\n".join(lines).strip() or "Empty story."
    headers = {"Content-Disposition": 'attachment; filename="story.txt"'}
    return PlainTextResponse(text, headers=headers)

from fastapi.responses import PlainTextResponse

@app.post("/export", response_class=PlainTextResponse)
async def export_story(payload: dict):
    outline = payload.get("outline", {})
    scenes = payload.get("scenes", [])
    text = "# " + outline.get("logline", "Untitled") + "\n\n"
    for i, beat in enumerate(outline.get("beats", [])):
        title = beat.get("title", f"Scene {i+1}")
        text += f"## {title}\nGoal: {beat.get('goal','')}\nConflict: {beat.get('conflict','')}\nOutcome: {beat.get('outcome','')}\n\n"
        if i < len(scenes):
            text += scenes[i] + "\n\n"
    return PlainTextResponse(text, media_type="text/plain")

