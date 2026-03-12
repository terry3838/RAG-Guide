#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

DATA_ROOT = Path(os.environ.get('RAG_GUIDE_DATA_ROOT', './data')).expanduser().resolve()
INPUT = DATA_ROOT / 'chunking' / 'tiers' / 'chunks.primary.jsonl'
OUT = DATA_ROOT / 'chunking' / 'tiers' / 'chunks.primary.core.jsonl'
REPORT = DATA_ROOT / 'chunking' / 'tiers' / 'core_report.json'
CORE_TOPICS = {'격국', '용신', '십신', '합충형파해', '신살', '십이운성', '대운세운'}


def keep(row: dict) -> bool:
    topics = set(row.get('topics') or [])
    doc_type = row.get('doc_type') or ''
    text = row.get('text') or ''
    page = int(row.get('page_start') or 0)
    is_myeongsik = bool(row.get('is_myeongsik_chunk'))

    if is_myeongsik:
        return True
    if topics & CORE_TOPICS:
        return True
    if doc_type == 'fortune' and any(k in text for k in ['대운', '세운', '월운', '교운기']):
        return True
    if doc_type == 'case' and any(k in text for k in ['사주 예', '명조 예', '사례', '일주', '천간', '지지', '시 일 월 년']):
        return True
    if doc_type == 'theory' and page >= 40 and any(k in text for k in ['격국', '용신', '십신', '합충', '형파해', '신살', '12운성', '십이운성']):
        return True
    return False


def main() -> None:
    total = kept = 0
    per_doc = {}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with INPUT.open(encoding='utf-8') as fin, OUT.open('w', encoding='utf-8') as fout:
        for line in fin:
            row = json.loads(line)
            total += 1
            doc_id = row.get('doc_id') or 'unknown'
            per_doc.setdefault(doc_id, {'kept': 0, 'dropped': 0})
            if keep(row):
                fout.write(json.dumps(row, ensure_ascii=False) + '\n')
                kept += 1
                per_doc[doc_id]['kept'] += 1
            else:
                per_doc[doc_id]['dropped'] += 1
    REPORT.write_text(json.dumps({'total_primary': total, 'kept_core_primary': kept, 'per_doc': per_doc}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'input': str(INPUT), 'output': str(OUT), 'kept': kept, 'dropped': total-kept}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
