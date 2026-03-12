#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import uuid
from pathlib import Path
from typing import Iterable

import requests

PROJECT_ROOT = Path(os.environ.get('RAG_GUIDE_PROJECT_ROOT', '.')).expanduser().resolve()
DATA_ROOT = Path(os.environ.get('RAG_GUIDE_DATA_ROOT', PROJECT_ROOT / 'data')).expanduser().resolve()
DEFAULT_INPUT = DATA_ROOT / 'embeddings' / 'chunks.upstage-embedding-query.jsonl'
DEFAULT_QDRANT_ENV = Path(os.environ.get('QDRANT_ENV_FILE', PROJECT_ROOT / 'config' / 'qdrant.env.example')).expanduser().resolve()


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


def batched(seq: list[dict], size: int) -> Iterable[list[dict]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def qdrant_request(method: str, url: str, api_key: str, **kwargs):
    headers = kwargs.pop('headers', {})
    headers['api-key'] = api_key
    headers.setdefault('Content-Type', 'application/json')
    resp = requests.request(method, url, headers=headers, timeout=120, **kwargs)
    if not resp.ok:
        raise RuntimeError(f'Qdrant {method} {url} failed: {resp.status_code} {resp.text}')
    if resp.content:
        return resp.json()
    return {'status': 'ok'}


def ensure_collection(base_url: str, api_key: str, collection: str, size: int, distance: str = 'Cosine') -> None:
    url = f'{base_url}/collections/{collection}'
    body = {'vectors': {'size': size, 'distance': distance}}
    resp = requests.put(
        url,
        headers={'api-key': api_key, 'Content-Type': 'application/json'},
        data=json.dumps(body).encode('utf-8'),
        timeout=120,
    )
    if resp.status_code == 409:
        return
    if not resp.ok:
        raise RuntimeError(f'Qdrant PUT {url} failed: {resp.status_code} {resp.text}')


def main() -> None:
    ap = argparse.ArgumentParser(description='Upload embedded saju chunks to Qdrant')
    ap.add_argument('--input', default=str(DEFAULT_INPUT))
    ap.add_argument('--qdrant-env', default=str(DEFAULT_QDRANT_ENV))
    ap.add_argument('--collection', default='saju_v2_curated')
    ap.add_argument('--batch-size', type=int, default=128)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    env = load_env(Path(args.qdrant_env))
    base_url = env['QDRANT_URL'].rstrip('/')
    api_key = env['QDRANT_API_KEY']

    rows = []
    for row in iter_rows(Path(args.input)):
        rows.append(row)
        if args.limit and len(rows) >= args.limit:
            break
    if not rows:
        raise SystemExit('No embedded rows found')

    vector_size = len(rows[0]['vector'])
    ensure_collection(base_url, api_key, args.collection, vector_size)

    total = 0
    for batch in batched(rows, args.batch_size):
        points = []
        for row in batch:
            vector = row.pop('vector')
            point = {
                'id': str(uuid.uuid5(uuid.NAMESPACE_URL, row['chunk_id'])),
                'vector': vector,
                'payload': row,
            }
            points.append(point)
        body = {'points': points}
        qdrant_request(
            'PUT',
            f'{base_url}/collections/{args.collection}/points',
            api_key,
            data=json.dumps(body).encode('utf-8'),
        )
        total += len(points)
        if total % 500 == 0:
            print(f'uploaded {total}', flush=True)

    print(json.dumps({'uploaded': total, 'collection': args.collection, 'vector_size': vector_size}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
