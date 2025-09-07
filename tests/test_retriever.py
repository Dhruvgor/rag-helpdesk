# tests/test_retriever.py
from pathlib import Path
from retriever import Retriever

def test_retriever_runs():
    root = Path(__file__).resolve().parents[1]  # project root
    meta = root / "data" / "index" / "meta.json"
    assert meta.exists(), "Run `python ingest.py` once before tests."
    r = Retriever()
    out = r.search("test question", k=2)
    assert isinstance(out, list) and len(out) <= 2
    if out:
        e = out[0]
        assert {"rank","score","file","text"} <= set(e.keys())
