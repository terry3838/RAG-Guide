#!/usr/bin/env python3
"""
Qdrant retrieval + lightweight reranking for saju evidence selection.

Default pipeline:
1) dense retrieval from Qdrant (topN)
2) lexical overlap + phrase boost
3) weighted fusion rerank (topK)

Example:
  python3 qdrant_rerank.py "직업 적성 관성 재성" --source saju_raw_kimdaeyoung_elite.txt
  python3 qdrant_rerank.py "식신생재 재생관" --top 40 --rerank 8 --json
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os

TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9_]+")
CJK_TOKEN_RE = re.compile(r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]")


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def load_embedding_config(openclaw_config_path: Path, model_override: str | None = None) -> tuple[str, str, str]:
    cfg = json.loads(openclaw_config_path.read_text(encoding="utf-8"))
    mem = cfg["agents"]["defaults"]["memorySearch"]
    base_url = mem["remote"]["baseUrl"].rstrip("/")
    api_key = mem["remote"]["apiKey"]
    model = model_override or mem.get("model") or "embedding-query"
    return base_url, api_key, model


def tokenize(text: str) -> list[str]:
    toks = [t.lower() for t in TOKEN_RE.findall(text or "")]
    cjk = CJK_TOKEN_RE.findall(text or "")
    merged = toks + cjk
    return [t for t in merged if len(t) > 0]


def normalize_query_tokens(tokens: list[str]) -> list[str]:
    out: list[str] = []
    for t in tokens:
        out.append(t)
        for suffix in ("운세", "운", "해석", "관련", "풀이"):
            if t.endswith(suffix) and len(t) > len(suffix) + 1:
                out.append(t[: -len(suffix)])
    # unique preserve order
    uniq: list[str] = []
    for t in out:
        if t not in uniq:
            uniq.append(t)
    return uniq


def char_trigrams(text: str) -> set[str]:
    s = re.sub(r"\s+", "", (text or "").lower())
    if len(s) < 3:
        return {s} if s else set()
    return {s[i : i + 3] for i in range(len(s) - 2)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def lexical_score(query: str, q_tokens: list[str], title: str, content: str) -> float:
    text = f"{title}\n{content}"
    tt = tokenize(text)
    if not q_tokens or not tt:
        return 0.0

    cnt = Counter(tt)
    qset = list(dict.fromkeys(q_tokens))

    # 1) unique token hit ratio
    matched = sum(1 for t in qset if t in cnt)
    hit_ratio = matched / len(qset)

    # 2) title token hit ratio (strong signal)
    title_cnt = Counter(tokenize(title))
    title_hits = sum(1 for t in qset if t in title_cnt)
    title_hit_ratio = title_hits / len(qset)

    # 3) freq overlap (capped)
    overlap = sum(min(cnt[t], 3) for t in qset)
    overlap_score = overlap / (len(qset) * 3)

    # 4) trigram similarity (captures phrase-ish Korean match)
    tri_score = jaccard(char_trigrams(query), char_trigrams(text[:2400]))

    # phrase / full-hit boosts
    qn = query.strip().lower()
    phrase_boost = 0.1 if qn and qn in text.lower() else 0.0
    all_hit_boost = 0.05 if matched == len(qset) else 0.0

    score = (
        (0.45 * hit_ratio)
        + (0.2 * title_hit_ratio)
        + (0.2 * overlap_score)
        + (0.15 * tri_score)
        + phrase_boost
        + all_hit_boost
    )
    return min(1.0, max(0.0, score))


def minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        return [1.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


class EmbeddingClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def embed(self, text: str) -> list[float]:
        req = urllib.request.Request(
            self.base_url + "/embeddings",
            data=json.dumps({"model": self.model, "input": text}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["data"][0]["embedding"]


class QdrantClient:
    def __init__(self, base_url: str, api_key: str, collection: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.collection = collection

    def search(self, vector: list[float], limit: int, source: str | None = None) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
        }
        if source:
            body["filter"] = {"must": [{"key": "source", "match": {"value": source}}]}

        req = urllib.request.Request(
            self.base_url + f"/collections/{self.collection}/points/search",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "api-key": self.api_key},
            method="POST",
        )
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("result", [])


@dataclass
class Ranked:
    id: str
    source: str
    title: str
    chunk_index: int
    semantic_raw: float
    semantic_norm: float
    lexical: float
    score: float
    snippet: str
    doc_type: str
    topics: list[str]
    section_title: str


def main() -> None:
    project_root = Path(os.environ.get('RAG_GUIDE_PROJECT_ROOT', '.')).expanduser().resolve()
    ap = argparse.ArgumentParser(description="Qdrant retrieval + rerank for saju evidence")
    ap.add_argument("query", type=str)
    ap.add_argument("--qdrant-env", default=str(Path(os.environ.get('QDRANT_ENV_FILE', project_root / 'config' / 'qdrant.env.example')).expanduser().resolve()))
    ap.add_argument("--openclaw-config", default=str(Path(os.environ.get('OPENCLAW_CONFIG_FILE', project_root / 'config' / 'openclaw.json.example')).expanduser().resolve()))
    ap.add_argument("--embed-model", default=None)
    ap.add_argument("--source", default=None, help="Optional payload.source filter")
    ap.add_argument("--top", type=int, default=30, help="Dense retrieval topN")
    ap.add_argument("--rerank", type=int, default=8, help="Final reranked topK")
    ap.add_argument("--alpha", type=float, default=0.6, help="Semantic weight")
    ap.add_argument("--beta", type=float, default=0.4, help="Lexical weight")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    qenv = load_env(Path(args.qdrant_env))
    qclient = QdrantClient(qenv["QDRANT_URL"], qenv["QDRANT_API_KEY"], qenv["QDRANT_COLLECTION_NAME"])

    emb_base, emb_key, emb_model = load_embedding_config(Path(args.openclaw_config), args.embed_model)
    eclient = EmbeddingClient(emb_base, emb_key, emb_model)

    query_vec = eclient.embed(args.query)
    candidates = qclient.search(query_vec, limit=args.top, source=args.source)

    q_tokens = normalize_query_tokens(tokenize(args.query))
    sem_raw = [float(c.get("score", 0.0)) for c in candidates]
    sem_norm = minmax(sem_raw)

    # pre-compute lexical for adaptive penalty
    lex_vals: list[float] = []
    payloads: list[dict[str, Any]] = []
    for c in candidates:
        payload = c.get("payload") or {}
        payloads.append(payload)
        title = str(payload.get("title") or payload.get("doc_id") or payload.get("source") or "")
        content = str(payload.get("content") or payload.get("text") or "")
        lex_vals.append(lexical_score(args.query, q_tokens, title, content))

    # normalize alpha/beta
    denom = (args.alpha + args.beta) if (args.alpha + args.beta) > 0 else 1.0
    alpha = args.alpha / denom
    beta = args.beta / denom

    max_lex = max(lex_vals) if lex_vals else 0.0

    ranked: list[Ranked] = []
    query_lc = args.query.lower()
    query_terms = set(q_tokens)
    for c, payload, s_norm, lex in zip(candidates, payloads, sem_norm, lex_vals):
        title = str(payload.get("title") or payload.get("doc_id") or payload.get("source") or "")
        section_title = str(payload.get("section_title") or "")
        content = str(payload.get("content") or payload.get("text") or "")
        doc_type = str(payload.get("doc_type") or "")
        topics = payload.get("topics") or []
        if not isinstance(topics, list):
            topics = []

        text_blob = f"{title}\n{section_title}\n{content}".lower()
        exact_term_hits = sum(1 for t in query_terms if t and t in text_blob)
        exact_bonus = min(0.12, exact_term_hits * 0.02)
        topic_bonus = min(0.10, sum(1 for t in topics if str(t).lower() in query_lc) * 0.04)
        section_bonus = 0.05 if section_title and any(t in section_title.lower() for t in query_terms) else 0.0
        myeongsik_bonus = 0.05 if payload.get("is_myeongsik_chunk") else 0.0
        recommended_bonus = 0.03 if payload.get("embedding_recommended") else 0.0
        query_is_fortune = any(k in args.query for k in ["대운", "세운", "월운", "교운기"])
        fortune_bonus = 0.08 if (query_is_fortune and (doc_type == "fortune" or "대운세운" in topics)) else 0.0
        theory_bonus = 0.04 if doc_type == "theory" else 0.0
        case_bonus = 0.03 if doc_type == "case" else 0.0
        table_penalty = 0.15 if doc_type == "table" else 0.0

        # if lexical-signal exists in pool, downweight lexical-zero chunks
        zero_lex_penalty = 0.12 if (max_lex >= 0.15 and lex < 0.03) else 0.0
        score = max(0.0, (alpha * s_norm) + (beta * lex) + exact_bonus + topic_bonus + section_bonus + myeongsik_bonus + recommended_bonus + fortune_bonus + theory_bonus + case_bonus - zero_lex_penalty - table_penalty)

        ranked.append(
            Ranked(
                id=str(c.get("id")),
                source=str(payload.get("source") or payload.get("source_file") or payload.get("doc_id") or ""),
                title=title,
                chunk_index=int(payload.get("chunkIndex") or -1),
                semantic_raw=float(c.get("score", 0.0)),
                semantic_norm=s_norm,
                lexical=lex,
                score=score,
                snippet=(content.replace("\n", " ")[:220]),
                doc_type=doc_type,
                topics=[str(t) for t in topics],
                section_title=section_title,
            )
        )

    ranked.sort(key=lambda x: x.score, reverse=True)
    final = ranked[: max(1, args.rerank)]

    if args.json:
        out = {
            "query": args.query,
            "embed_model": emb_model,
            "retrieved": len(candidates),
            "returned": len(final),
            "weights": {"alpha": args.alpha, "beta": args.beta},
            "results": [
                {
                    "rank": i + 1,
                    "id": r.id,
                    "source": r.source,
                    "title": r.title,
                    "chunkIndex": r.chunk_index,
                    "score": round(r.score, 6),
                    "semantic_raw": round(r.semantic_raw, 6),
                    "semantic_norm": round(r.semantic_norm, 6),
                    "lexical": round(r.lexical, 6),
                    "doc_type": r.doc_type,
                    "topics": r.topics,
                    "section_title": r.section_title,
                    "snippet": r.snippet,
                }
                for i, r in enumerate(final)
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"[Rerank] query=\"{args.query}\" model={emb_model} retrieved={len(candidates)} returned={len(final)}")
    print(f"weights: semantic={args.alpha:.2f} lexical={args.beta:.2f}\n")
    for i, r in enumerate(final, 1):
        print(f"{i:02d}. {r.title} ({r.source}#{r.chunk_index})")
        print(
            f"    score={r.score:.4f} semantic={r.semantic_raw:.4f}/{r.semantic_norm:.4f} lexical={r.lexical:.4f} doc_type={r.doc_type} topics={','.join(r.topics)}"
        )
        if r.section_title:
            print(f"    section={r.section_title[:120]}")
        if r.snippet:
            print(f"    ↳ {r.snippet}")
        print()


if __name__ == "__main__":
    main()
