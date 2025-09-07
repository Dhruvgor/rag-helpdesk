# eval.py
import os, json
from retriever import Retriever
from metrics import hit_at_k, mrr, ndcg_at_k

FEEDBACK_DIR = "data/eval"
FEEDBACK_PATH = os.path.join(FEEDBACK_DIR, "feedback.jsonl")

def interactive(k=5, persist=True):
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    ret = Retriever()
    files = ret.files()
    print("\nInteractive Retrieval Eval")
    print("--------------------------")
    print(f"Available files ({len(files)}): {', '.join(files)}")
    print("Type 'done' to finish.\n")

    ranks = []
    while True:
        q = input("Question: ").strip()
        if not q or q.lower() == "done":
            break
        ans = input("Correct filename (exact match from list above): ").strip()
        if ans not in files:
            print("  ! Not in indexed files. Try again.")
            continue

        hits = ret.search(q, k=k)
        rank = None
        for h in hits:
            if h["file"] == ans:
                rank = h["rank"]
                break
        ranks.append(rank)
        print(f"  → Rank: {rank if rank is not None else 'NOT FOUND in top-'+str(k)}")
        print(f"  Stats so far | hit@{k}: {hit_at_k(ranks,k):.3f} | MRR: {mrr(ranks):.3f} | nDCG@{k}: {ndcg_at_k(ranks,k):.3f}\n")

        if persist:
            with open(FEEDBACK_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"question": q, "answer_file": ans, "k": k, "rank": rank}) + "\n")

    print("\nFinal metrics")
    print(f"  Queries: {len(ranks)}")
    print(f"  hit@{k}: {hit_at_k(ranks,k):.3f}")
    print(f"  MRR: {mrr(ranks):.3f}")
    print(f"  nDCG@{k}: {ndcg_at_k(ranks,k):.3f}")

if __name__ == "__main__":
    interactive(k=5, persist=True)
