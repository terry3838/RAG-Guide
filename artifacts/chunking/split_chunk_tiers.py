#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

DATA_ROOT = Path(os.environ.get('RAG_GUIDE_DATA_ROOT', './data')).expanduser().resolve()
INPUT = DATA_ROOT / 'chunking' / 'chunks.all.jsonl'
OUTDIR = DATA_ROOT / 'chunking' / 'tiers'
PRIMARY = OUTDIR / 'chunks.primary.jsonl'
SECONDARY = OUTDIR / 'chunks.secondary_table.jsonl'
REPORT = OUTDIR / 'report.json'


def classify(row: dict) -> str:
    doc_type = row.get('doc_type') or ''
    topics = set(row.get('topics') or [])
    text = row.get('text') or ''
    is_myeongsik = bool(row.get('is_myeongsik_chunk'))
    recommended = bool(row.get('embedding_recommended'))

    # low-value chunks stay out of both upload candidates
    if not recommended:
        return 'drop'

    # tables go secondary by default
    if doc_type == 'table':
        return 'secondary'

    # explicit theory/case/fortune go primary
    if doc_type in {'theory', 'case', 'fortune'}:
        return 'primary'

    # fallback: if it's clearly domain-rich, keep primary
    if is_myeongsik or topics & {'격국', '용신', '십신', '합충형파해', '신살', '십이운성', '대운세운'}:
        return 'primary'

    if len(text) >= 200:
        return 'primary'
    return 'drop'


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    counts = {'total': 0, 'primary': 0, 'secondary': 0, 'drop': 0}
    per_doc: dict[str, dict[str, int]] = {}

    with INPUT.open(encoding='utf-8') as fin, \
         PRIMARY.open('w', encoding='utf-8') as f_primary, \
         SECONDARY.open('w', encoding='utf-8') as f_secondary:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            counts['total'] += 1
            bucket = classify(row)
            counts[bucket] += 1
            doc_id = row.get('doc_id') or 'unknown'
            per_doc.setdefault(doc_id, {'primary': 0, 'secondary': 0, 'drop': 0})
            per_doc[doc_id][bucket] += 1

            if bucket == 'primary':
                row['retrieval_tier'] = 'primary'
                f_primary.write(json.dumps(row, ensure_ascii=False) + '\n')
            elif bucket == 'secondary':
                row['retrieval_tier'] = 'secondary_table'
                f_secondary.write(json.dumps(row, ensure_ascii=False) + '\n')

    REPORT.write_text(json.dumps({'counts': counts, 'per_doc': per_doc}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'primary': str(PRIMARY), 'secondary': str(SECONDARY), 'report': str(REPORT), 'counts': counts}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
