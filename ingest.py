# ingest.py
import glob, json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE, CHUNK_OVERLAP = 500, 50

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR  = BASE_DIR / "data" / "raw"
INDEX_DIR = BASE_DIR / "data" / "index"
META_PATH = INDEX_DIR / "meta.json"
EMB_PATH  = INDEX_DIR / "embeddings.npy"
FAISS_PATH = INDEX_DIR / "faiss.index"

def load_docs():
    return [(p.name, p.read_text(encoding="utf-8"))
            for p in sorted(RAW_DIR.glob("*.txt"))]

def chunk_words(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    toks = text.split()
    out, i = [], 0
    while i < len(toks):
        out.append(" ".join(toks[i:i+size]))
        i += max(1, size - overlap)
    return out

def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_docs()
    if not docs:
        raise SystemExit(f"No .txt docs in {RAW_DIR}")

    chunks, meta = [], []
    for fname, txt in docs:
        for c in chunk_words(txt):
            chunks.append(c)
            meta.append({"file": fname, "text": c})

    model = SentenceTransformer(MODEL_NAME)
    embs = model.encode(chunks, convert_to_numpy=True, show_progress_bar=True)
    embs = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-12)

    np.save(EMB_PATH, embs)
    META_PATH.write_text(json.dumps(meta), encoding="utf-8")

    try:
        import faiss
        index = faiss.IndexFlatIP(embs.shape[1])
        index.add(embs.astype(np.float32))
        faiss.write_index(index, str(FAISS_PATH))
        print(f"Indexed {len(chunks)} chunks (FAISS + .npy).")
    except Exception as e:
        print(f"FAISS unavailable ({e}). Saved numpy embeddings only.")
        print(f"Indexed {len(chunks)} chunks (.npy only).")

if __name__ == "__main__":
    main()
