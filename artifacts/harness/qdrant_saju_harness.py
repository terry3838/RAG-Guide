#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RERANK = ROOT / 'qdrant_rerank.py'

BUCKETS = {
    'geokguk': ['격국', '정재격', '편재격', '월지가 재', '월지 정관'],
    'relations': ['합', '충', '형', '파', '해', '육합', '반합', '방합', '천간충'],
    'sinsal': ['역마', '화개', '망신', '년살', '월살', '겁살', '재살', '장성살'],
    'states': ['장생', '목욕', '관대', '건록', '제왕', '쇠', '병', '사', '묘', '절', '태', '양'],
    'ten_gods': ['비견', '겁재', '식신', '상관', '편재', '정재', '편관', '정관', '편인', '정인'],
    'fortune': ['대운', '세운', '월운', '명과 운', '성중유패', '패중유성'],
}


def run_rerank(query: str, top: int, rerank: int, qdrant_env: str | None = None, source: str | None = None) -> dict:
    cmd = [sys.executable, str(RERANK), query, '--top', str(top), '--rerank', str(rerank), '--json']
    if qdrant_env:
        cmd += ['--qdrant-env', qdrant_env]
    if source:
        cmd += ['--source', source]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return {'query': query, 'error': p.stderr.strip() or p.stdout.strip(), 'results': []}
    return json.loads(p.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(description='Bucketed Qdrant harness for saju CRAG retrieval')
    ap.add_argument('query', help='user query or focus phrase')
    ap.add_argument('--daymaster', default='')
    ap.add_argument('--month-branch', default='')
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--rerank', type=int, default=4)
    ap.add_argument('--qdrant-env', default=None)
    ap.add_argument('--source', default=None)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    enrich = []
    if args.daymaster:
        enrich.append(f'{args.daymaster}일간')
    if args.month_branch:
        enrich.append(f'월지 {args.month_branch}')
    enrich_text = ' '.join(enrich).strip()

    out = {'input': args.query, 'daymaster': args.daymaster, 'month_branch': args.month_branch, 'buckets': {}}
    seen = set()
    diversified = []

    for bucket, terms in BUCKETS.items():
        term_window = 4 if bucket in {'relations', 'sinsal', 'fortune', 'geokguk'} else 3
        q = f"{args.query} {' '.join(terms[:term_window])} {enrich_text}".strip()
        data = run_rerank(q, args.top, args.rerank, qdrant_env=args.qdrant_env, source=args.source)
        bucket_results = []
        for r in data.get('results', []):
            key = (r.get('source'), r.get('title'))
            bucket_results.append(r)
            if key not in seen:
                seen.add(key)
                diversified.append({'bucket': bucket, **r})
        out['buckets'][bucket] = {'query': q, 'count': len(bucket_results), 'results': bucket_results}

    out['diversified_top'] = diversified[:12]

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for item in out['diversified_top']:
            print(f"[{item['bucket']}] {item['title']} :: {item['snippet'][:180]}")


if __name__ == '__main__':
    main()
