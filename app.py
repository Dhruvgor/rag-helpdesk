# app.py
import os, json, time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from retriever import Retriever
from metrics import hit_at_k, mrr, ndcg_at_k

app = FastAPI(title="RAG Helpdesk", version="0.2.0")

# ---------------------- Globals ----------------------
FEEDBACK_DIR = os.path.join("data", "eval")
FEEDBACK_PATH = os.path.join(FEEDBACK_DIR, "feedback.jsonl")
ret: Optional[Retriever] = None

def load_retriever():
    global ret
    ret = Retriever()

@app.on_event("startup")
def _on_startup():
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    load_retriever()

# Serve static assets (UI)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
def root():
    # serve the HTML file
    return FileResponse("static/ui.html")

# ---------------------- Schemas ----------------------
class AskReq(BaseModel):
    question: str
    k: int = Field(3, ge=1, le=50)

class FeedbackReq(BaseModel):
    question: str
    answer_file: str
    k: int = Field(5, ge=1, le=50)
    persist: bool = True

# ---------------------- API ----------------------
@app.get("/files")
def list_files():
    if ret is None:
        raise HTTPException(503, "Retriever not ready.")
    return {"files": ret.files()}

def _answer_from_contexts(hits):
    return " ".join(h["text"] for h in hits)[:1000]

@app.post("/ask")
def ask(req: AskReq):
    if ret is None:
        raise HTTPException(503, "Retriever not ready.")
    t0 = time.time()
    hits = ret.search(req.question, k=req.k)
    latency = int((time.time() - t0) * 1000)
    return {"answer": _answer_from_contexts(hits), "contexts": hits, "latency_ms": latency}

# URL-bar friendly GET version
@app.get("/ask")
def ask_get(question: str, k: int = 3):
    return ask(AskReq(question=question, k=k))

@app.post("/feedback")
def feedback(req: FeedbackReq):
    if ret is None:
        raise HTTPException(503, "Retriever not ready.")
    hits = ret.search(req.question, k=req.k)
    rank = next((h["rank"] for h in hits if h["file"] == req.answer_file), None)

    record = {
        "question": req.question, "answer_file": req.answer_file,
        "k": req.k, "rank": rank, "timestamp": int(time.time()),
    }
    if req.persist:
        with open(FEEDBACK_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    return {"rank": rank, "hit_at_k": (rank is not None and rank <= req.k), "saved": req.persist}

@app.get("/metrics")
def metrics(k: int = 5):
    if not os.path.exists(FEEDBACK_PATH):
        raise HTTPException(404, "No feedback yet. POST /feedback first.")
    ranks = []
    with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                j = json.loads(line); r = j.get("rank")
                ranks.append(r if (r is None or (isinstance(r, int) and r > 0)) else None)
            except Exception:
                continue
    return {
        "count": len(ranks),
        f"hit@{k}": round(hit_at_k(ranks, k), 3),
        "mrr": round(mrr(ranks), 3),
        f"ndcg@{k}": round(ndcg_at_k(ranks, k), 3),
    }

@app.post("/reindex")
def reindex():
    try:
        import ingest
        ingest.main()
        load_retriever()
        return {"status": "ok", "message": "Index rebuilt and retriever reloaded."}
    except Exception as e:
        raise HTTPException(500, f"Reindex failed: {e}")

# Entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
