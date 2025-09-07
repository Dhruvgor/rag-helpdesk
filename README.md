RAG Helpdesk (Mini)
Retrieval-augmented QA over local documents with interactive evaluation, a tiny UI, and pragmatic engineering (tests, version-pinned deps, and Docker option).
Stack: FastAPI • Sentence-Transformers (MiniLM) • FAISS (optional, NumPy fallback) • scikit-learn • PyTest.

Why this exists (not another toy chatbot)
Most small teams have knowledge scattered across PDFs, FAQs, and notes. LLMs can answer questions, but hallucinate and leak context when not grounded. Full “AI platform” projects are often overkill for a small doc set.
This project is a minimal, transparent RAG workflow that a small team could actually run: - Grounding: answers come from the team’s own docs. - Measurable: retrieval quality is evaluated (hit@k, MRR, nDCG) using your judgements. - Reproducible: one command to index, one to serve; pinned dependencies; tests. - Cost-aware: default path uses free, local embeddings; a generator head is optional.
My goal wasn’t to “build a chatbot.” It was to demonstrate thoughtful design choices and trade-offs when turning unstructured docs into reliable, queryable knowledge.

What this is (and isn’t)
This is: - A small RAG service that you can index, query, and evaluate honestly. - A demo of engineering discipline: version pinning, tests, CI-friendly layout, and optional Docker. - An example of interactive data collection: you can log judgements and see the metrics move.
This is not: - A production-grade enterprise search product. - A UI showcase. The interface is intentionally simple; the value is in evaluation + reproducibility. - A guarantee against hallucinations. By default the API returns contexts only (no generator) to stay safe.

Repo structure
rag-helpdesk/
  app.py               # API + UI routes (/ , /ui, /ask, /files, /feedback, /metrics, /reindex)
  ingest.py            # chunk -> embed -> write index (FAISS if available, plus embeddings.npy + meta.json)
  retriever.py         # unified retriever (FAISS or NumPy), optional TF-IDF hybrid (see README)
  metrics.py           # hit@k, MRR, nDCG implementations
  requirements.txt     # pinned dependencies
  tests/
    test_retriever.py  # minimal sanity test
  data/
    raw/               # <- put .txt docs here
    index/             # built artefacts
    eval/              # feedback.jsonl (judgements)
  static/
    ui.html            # small UI
    ui.js
    styles.css
  Dockerfile           # optional container image (if you add it)

Quickstart
1) Install deps and index local docs
pip install -r requirements.txt
python ingest.py          # builds data/index/*
Put your .txt files in data/raw/ first (four sample AI docs are fine to start).
2) Run the API + UI
python app.py

opens http://127.0.0.1:8000  (UI at /)

3) Use the UI
Ask a question → get contexts + latency.
Submit feedback (pick the file that best answers the question).
Get metrics → shows hit@k, MRR, nDCG@k.
Reindex when you change data/raw/ (no server restart needed).
4) API examples (PowerShell)

# List files
(iwr http://127.0.0.1:8000/files).Content

# Ask (POST)
iwr -Uri http://127.0.0.1:8000/ask -Method POST -ContentType 'application/json' \`\
  -Body '{"question":"What is RAG?","k":3}' | Select-Object -Expand Content

# Feedback
iwr -Uri http://127.0.0.1:8000/feedback -Method POST -ContentType 'application/json' \`\
  -Body '{"question":"What is RAG?","answer_file":"rag_and_vector_search.txt","k":5,"persist":true}' |\
  Select-Object -Expand Content

# Metrics
(iwr 'http://127.0.0.1:8000/metrics?k=5').Content

Evaluation (how quality is measured)
Why eval matters: A demo can look smart while returning the wrong source. Retrieval evaluation makes failure explicit.
What we log: Every time you submit feedback, we store a judgement to data/eval/feedback.jsonl:
{"question":"What is RAG?","answer_file":"rag_and_vector_search.txt","k":5,"rank":1,"timestamp":...}
Metrics: - hit@k – was the right file in the top-k? - MRR – how early did we find the right file? (1/rank) - nDCG@k – position-sensitive score; higher is better.
Tip: label the best file for each question (noisy labels drag metrics down).

Design choices & trade-offs
Embeddings: all-MiniLM-L6-v2 (fast, no GPU required). You can swap models in ingest.py / retriever.py.
Index: FAISS Inner-Product if available; otherwise vector-normalised NumPy similarity.
Chunking: defaults (e.g., 500 tokens with overlap). Larger chunks improve recall but add noise; tune in ingest.py.
Safety: the default /ask returns stitched contexts without LLM generation to avoid hallucinations. Add a generator head only when retrieval is solid.
Interactive eval: product teams learn faster when they can judge live and see metrics update.

What’s deliberately “imperfect” (honest limits)
No generator head by default. That’s intentional—generation hides retrieval errors. When you add it, keep contexts visible and cite sources.
Single-vector dense retrieval. Domain-specific jargon or code-mixed corpora may need TF-IDF hybrid or reranking (see below).
Basic metadata. No per-doc ACLs, no anonymisation. Don’t put sensitive data in data/raw/.
Toy scale. Great for a few hundred docs. For millions, you’ll need a proper ANN service, cache, monitoring, and a queue.

Optional improvements (small code changes)
1) Hybrid retrieval (embedding + TF-IDF)
Add a TF-IDF scorer and combine with embeddings to reduce synonym misses and keyword gaps. (I’ve left hooks in retriever.py; enable method="hybrid" and tune alpha.)
2) CSV export for charts
Expose /feedback.csv and /metrics.csv so you can plot progress in the README or a notebook.
3) Generator head
Add a small local model (e.g., FLAN-T5 via transformers) and keep sources inline in the answer. Guard against long outputs and missing contexts.

CI / tests
Run tests:
pytest -q
Suggested CI (GitHub Actions) at .github/workflows/ci.yml:
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python ingest.py
      - run: pytest -q

Docker (optional)
docker build -t rag-helpdesk .
docker run -p 8000:8000 rag-helpdesk
# then open http://127.0.0.1:8000
If you want to mount docs at runtime instead of baking them into the image, adjust the Dockerfile and call /reindex on start.

Security & privacy
Don’t index sensitive data; this demo doesn’t implement redaction or per-user access control.
If you add an external LLM, pass only minimal context and scrub PII.

FAQ
Why not just fine-tune an LLM?
Because facts change and access is the constraint. RAG lets you refresh knowledge by re-indexing docs, not retraining weights.
Why not a fancy UI?
Because flashy UIs hide retrieval error. This repo’s value is evaluation and reproducibility.
It missed an obvious answer—why?
Likely chunking or wording. Increase k, raise chunk size/overlap, or enable the TF-IDF hybrid.


