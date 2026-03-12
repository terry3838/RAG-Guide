#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

import requests

PROJECT_ROOT = Path(os.environ.get('RAG_GUIDE_PROJECT_ROOT', '.')).expanduser().resolve()
DATA_ROOT = Path(os.environ.get('RAG_GUIDE_DATA_ROOT', PROJECT_ROOT / 'data')).expanduser().resolve()
DEFAULT_INPUT = DATA_ROOT / 'chunking' / 'chunks.all.jsonl'
DEFAULT_ENV = PROJECT_ROOT / '.env.local'
DEFAULT_OUTPUT = DATA_ROOT / 'embeddings' / 'chunks.upstage-embedding-query.jsonl'
API_URL = 'https://api.upstage.ai/v1/embeddings'


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        out[k.strip()] = v.strip()
    return out


def iter_rows(path: Path) -> Iterable[dict]:
    with path.open(encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def build_embedding_input(row: dict) -> str:
    title = row.get('title') or ''
    section = row.get('section_title') or ''
    topics = ', '.join(row.get('topics') or [])
    doc_type = row.get('doc_type') or ''
    entities = row.get('entities') or {}
    ten_gods = ', '.join(entities.get('ten_gods') or [])
    relations = ', '.join(entities.get('relations') or [])
    sinsal = ', '.join(entities.get('sinsal') or [])
    states = ', '.join(entities.get('states') or [])
    text = row.get('text') or ''
    parts = [
        f'[title] {title}' if title else '',
        f'[section] {section}' if section else '',
        f'[doc_type] {doc_type}' if doc_type else '',
        f'[topics] {topics}' if topics else '',
        f'[ten_gods] {ten_gods}' if ten_gods else '',
        f'[relations] {relations}' if relations else '',
        f'[sinsal] {sinsal}' if sinsal else '',
        f'[states] {states}' if states else '',
        text,
    ]
    return '\n'.join(p for p in parts if p).strip()


def batched(seq: list[dict], size: int) -> Iterable[list[dict]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def call_embeddings(api_key: str, model: str, inputs: list[str], timeout: int = 120) -> list[list[float]]:
    resp = requests.post(
        API_URL,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={'model': model, 'input': inputs},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    items = sorted(data['data'], key=lambda x: x['index'])
    return [item['embedding'] for item in items]


def main() -> None:
    ap = argparse.ArgumentParser(description='Embed curated saju chunks with Upstage embeddings API')
    ap.add_argument('--input', default=str(DEFAULT_INPUT))
    ap.add_argument('--env-file', default=str(DEFAULT_ENV))
    ap.add_argument('--output', default=str(DEFAULT_OUTPUT))
    ap.add_argument('--model', default='embedding-query')
    ap.add_argument('--batch-size', type=int, default=64)
    ap.add_argument('--min-chars', type=int, default=100)
    ap.add_argument('--only-recommended', action='store_true', default=True)
    ap.add_argument('--all', action='store_true', help='Ignore embedding_recommended flag')
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    env = load_env(Path(args.env_file))
    api_key = env.get('UPSTAGE_KEY') or os.environ.get('UPSTAGE_KEY')
    if not api_key:
        raise SystemExit('UPSTAGE_KEY not found in env file or environment')

    rows: list[dict] = []
    for row in iter_rows(Path(args.input)):
        if not args.all and not row.get('embedding_recommended', False):
            continue
        if int(row.get('char_len') or 0) < args.min_chars:
            continue
        rows.append(row)
        if args.limit and len(rows) >= args.limit:
            break

    if not rows:
        raise SystemExit('No rows selected for embedding')

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with out_path.open('w', encoding='utf-8') as f:
        for batch in batched(rows, args.batch_size):
            inputs = [build_embedding_input(r) for r in batch]
            vectors = call_embeddings(api_key, args.model, inputs)
            for row, emb_input, vector in zip(batch, inputs, vectors):
                payload = dict(row)
                payload['embedding_model'] = args.model
                payload['embedding_input'] = emb_input
                payload['vector'] = vector
                f.write(json.dumps(payload, ensure_ascii=False) + '\n')
                total += 1
                if total % 500 == 0:
                    print(f'embedded {total}', flush=True)

    print(json.dumps({'embedded': total, 'output': str(out_path), 'model': args.model}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
