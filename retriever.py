# retriever.py
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "data" / "index"
META_PATH = INDEX_DIR / "meta.json"
EMB_PATH  = INDEX_DIR / "embeddings.npy"
FAISS_PATH = INDEX_DIR / "faiss.index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class Retriever:
    def __init__(self):
        if not (META_PATH.exists() and EMB_PATH.exists()):
            raise RuntimeError("Index not found. Run `python ingest.py` first.")
        self.meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        self.embs = np.load(EMB_PATH)
        self.model = SentenceTransformer(MODEL_NAME)

        self.faiss_index = None
        try:
            import faiss
            if FAISS_PATH.exists():
                self.faiss_index = faiss.read_index(str(FAISS_PATH))
        except Exception:
            self.faiss_index = None

    def _encode_query(self, q: str):
        v = self.model.encode([q], convert_to_numpy=True)
        v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
        return v.astype(np.float32)

    def search(self, query: str, k: int = 3):
        q = self._encode_query(query)
        if self.faiss_index is not None:
            D, I = self.faiss_index.search(q, k)
            idxs, scores = I[0], D[0]
        else:
            sims = (self.embs @ q[0])
            k = min(k, sims.shape[0])
            idxs = np.argpartition(-sims, range(k))[:k]
            idxs = idxs[np.argsort(-sims[idxs])]
            scores = sims[idxs]

        hits = []
        for i, s in zip(idxs, scores):
            m = self.meta[int(i)]
            hits.append({"rank": len(hits)+1, "score": float(s), "file": m["file"], "text": m["text"]})
        return hits

    def files(self):
        return sorted({m["file"] for m in self.meta})
