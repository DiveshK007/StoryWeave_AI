import os, math, random, requests

def _mock_vec(text: str, dim: int = 384):
    random.seed(hash(text) & 0xffffffff)
    v = [random.random() for _ in range(dim)]
    norm = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x / norm for x in v]

def call_llm(prompt: str, llm_url: str, max_tokens: int = 512):
    import json
    if os.getenv("USE_MOCK", "0") == "1":
        pl = prompt.lower()
        # Outline planner → return proper JSON with 6–7 beats including Inciting Incident
        if "return json with keys logline and beats" in pl or "story planner" in pl:
            data = {
                "logline": "A shy barista can pause time for 10 seconds, but each pause steals hours from tomorrow.",
                "beats": [
                    {"title":"Hook","goal":"Keep the café calm","conflict":"Time jitters spill orders","outcome":"Rin discovers the pause"},
                    {"title":"Inciting Incident","goal":"Save a child from a crash","conflict":"Ten-second limit nearly fails","outcome":"Child saved; Rin blacks out"},
                    {"title":"First Threshold","goal":"Use pauses to help quietly","conflict":"Ringing ears, blurred vision","outcome":"Rin commits to a secret rulebook"},
                    {"title":"Midpoint","goal":"Stop a closing-time robbery","conflict":"Multiple attackers exceed 10s","outcome":"Wins but loses half a day tomorrow"},
                    {"title":"Crisis","goal":"Protect a friend from a stalker","conflict":"Pauses cause memory gaps","outcome":"Work and friendships strain"},
                    {"title":"Climax","goal":"Catch stalker without pausing","conflict":"Must rely on wit not power","outcome":"Rin succeeds; sets new limits"},
                    {"title":"Resolution","goal":"Live with balance","conflict":"Temptation to overuse","outcome":"Rin keeps the gift for emergencies"}
                ]
            }
            return json.dumps(data)
        # Scene expansion → readable mock text
        return ("[MOCK LLM]\n"
                "Scene based on: " + prompt[:600] + "\n"
                "…cups rattle, air crystallizes, and time thins to a silver thread…\n"
                "— End of mock output —")
    # Real NIM call (when USE_MOCK is off)
    payload = {"model":"llama-3.1-nemotron-nano-8b-v1","prompt":prompt,"max_tokens":max_tokens,"temperature":0.2}
    r = requests.post(f"{llm_url}/v1/completions", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("choices",[{}])[0].get("text","")

def embed_text(chunks, embed_url: str):
    if os.getenv("USE_MOCK", "0") == "1":
        return [{"embedding": _mock_vec(ch)} for ch in chunks]
    payload = {"input": chunks}
    r = requests.post(f"{embed_url}/v1/embeddings", json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("data", [])
