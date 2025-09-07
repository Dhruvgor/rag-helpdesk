# metrics.py
import math
from typing import List, Optional

def hit_at_k(ranks: List[Optional[int]], k: int = 3) -> float:
    hits = sum(1 for r in ranks if r is not None and r <= k)
    return hits / max(1, len(ranks))

def mrr(ranks: List[Optional[int]]) -> float:
    vals = [1.0/r for r in ranks if r is not None and r > 0]
    return sum(vals) / max(1, len(ranks))

def ndcg_at_k(ranks: List[Optional[int]], k: int = 3) -> float:
    # binary relevance (1 if found; 0 otherwise)
    dcg = 0.0
    for r in ranks:
        if r is not None and r <= k:
            dcg += 1.0 / math.log2(r + 1)
    # IDCG when every query has one relevant doc at rank 1 (best case)
    idcg = 1.0 / math.log2(1 + 1)
    return (dcg / max(1e-12, idcg)) / max(1, len(ranks))
