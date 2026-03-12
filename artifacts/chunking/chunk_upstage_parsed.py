#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

DATA_ROOT = Path(os.environ.get('RAG_GUIDE_DATA_ROOT', './data')).expanduser().resolve()
PARSED_DIR = DATA_ROOT / 'parsed'
OUT_DIR = DATA_ROOT / 'chunking'
DOCS_DIR = OUT_DIR / 'docs'
COMBINED_PATH = OUT_DIR / 'chunks.all.jsonl'
MANIFEST_PATH = OUT_DIR / 'manifest.json'

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---\n', re.S)
TITLE_CLEAN_RE = re.compile(r'\s+')

IGNORE_CATEGORIES = {'header', 'footer', 'footnote'}
KEEP_CATEGORIES = {'heading1', 'paragraph', 'list', 'table', 'caption', 'index'}
MAX_CHARS = 1200
MIN_CHARS = 250
OVERLAP = 120

TIANGAN = list('甲乙丙丁戊己庚辛壬癸')
DIZHI = list('子丑寅卯辰巳午未申酉戌亥')
TEN_GODS = ['비견', '겁재', '식신', '상관', '편재', '정재', '편관', '정관', '편인', '정인']
RELATIONS = ['합', '충', '형', '파', '해', '삼합', '육합', '반합', '방합', '천간충', '진진형', '자형']
SINSAL = ['역마살', '화개살', '망신살', '년살', '월살', '천살', '지살', '재살', '반안살', '장성살', '겁살', '육해살']
STATES = ['장생', '목욕', '관대', '건록', '제왕', '쇠', '병', '사', '묘', '절', '태', '양']
DOMAIN_HINTS = ['사주', '명리', '오행', '십성', '십신', '지장간', '천간', '지지', '일간', '대운', '세운', '월운', '격국', '용신', '기신', '합충', '형파해', '신살', '12운성', '십이운성']
TOPICS = {
    '격국': ['격국', '정재격', '편재격', '정관격', '편관격', '상관격', '식신격', '인수격', '건록격', '양인격', '재격'],
    '용신': ['용신', '기신', '희신', '구신'],
    '십신': TEN_GODS,
    '합충형파해': RELATIONS,
    '신살': SINSAL,
    '십이운성': STATES,
    '대운세운': ['대운', '세운', '월운', '교운기'],
    '직업': ['직업', '적성', '사업', '영업', '회사', '공무원', '의사', '변호사'],
    '재물': ['재물', '돈', '부자', '수입', '매출', '재성'],
    '연애결혼': ['연애', '결혼', '배우자', '궁합'],
    '건강': ['건강', '질병', '아프', '병'],
}

PLACEHOLDER_PATTERNS = [
    re.compile(r'!\[image\]\(/image/placeholder\)', re.I),
    re.compile(r'!\[Figure\]\([^)]*\)', re.I),
    re.compile(r'<!--\s*Page\s*\d+\s*-->', re.I),
]
WHITESPACE_RE = re.compile(r'[ \t]+')
MULTIBLANK_RE = re.compile(r'\n{3,}')
PAGE_RE = re.compile(r'page[_ ]?(\d+)|page\s*(\d+)', re.I)
SINGLE_STATE_PATTERNS = {
    '사': re.compile(r'(12운성|십이운성|[|/\\s])사([|/\\s]|$)'),
    '병': re.compile(r'(12운성|십이운성|[|/\\s])병([|/\\s]|$)'),
    '묘': re.compile(r'(12운성|십이운성|[|/\\s])묘([|/\\s]|$)'),
    '절': re.compile(r'(12운성|십이운성|[|/\\s])절([|/\\s]|$)'),
    '태': re.compile(r'(12운성|십이운성|[|/\\s])태([|/\\s]|$)'),
    '양': re.compile(r'(12운성|십이운성|[|/\\s])양([|/\\s]|$)'),
    '쇠': re.compile(r'(12운성|십이운성|[|/\\s])쇠([|/\\s]|$)'),
}
RELATION_PATTERNS = {
    '합': re.compile(r'(합충|합화|합거|천간합|육합|삼합|반합|방합|[子丑寅卯辰巳午未申酉戌亥甲乙丙丁戊己庚辛壬癸]{2,}합)'),
    '충': re.compile(r'(충돌|천간충|육충|충형|[子丑寅卯辰巳午未申酉戌亥甲乙丙丁戊己庚辛壬癸]{2,}충)'),
    '형': re.compile(r'(형파해|삼형|자형|진진형|형살|[子丑寅卯辰巳午未申酉戌亥]{2,}형)'),
    '파': re.compile(r'(형파해|파격|[子丑寅卯辰巳午未申酉戌亥]{2,}파)'),
    '해': re.compile(r'(형파해|육해|육해살|[子丑寅卯辰巳午未申酉戌亥]{2,}해)'),
}
MYEONGSIK_PATTERNS = [
    re.compile(r'시\s*일\s*월\s*년'),
    re.compile(r'천간\s*지지'),
    re.compile(r'(비견|겁재|식신|상관|편재|정재|편관|정관|편인|정인).*(비견|겁재|식신|상관|편재|정재|편관|정관|편인|정인)'),
    re.compile(r'[甲乙丙丁戊己庚辛壬癸].*[子丑寅卯辰巳午未申酉戌亥]'),
]
SKIP_TEXT_PATTERNS = [
    re.compile(r'^ISBN\\b', re.I),
    re.compile(r'저작권법'),
    re.compile(r'^\\{ 그림 목록 \\}$'),
    re.compile(r'^\\{ 표 목록 \\}$'),
    re.compile(r'^차례$'),
    re.compile(r'1판\\s*1쇄'),
    re.compile(r'All rights reserved', re.I),
    re.compile(r'무단전재'),
    re.compile(r'출판등록'),
    re.compile(r'^\[그림\d+'),
    re.compile(r'^\[ 표\d+'),
]


@dataclass
class Block:
    kind: str
    text: str
    page: int
    section: str


def clean_text(text: str) -> str:
    text = text or ''
    for pat in PLACEHOLDER_PATTERNS:
        text = pat.sub('', text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('*', '')
    text = re.sub(r'\|\s*---[^\n]*', '', text)
    text = re.sub(r'\n\s*\|', '\n|', text)
    text = WHITESPACE_RE.sub(' ', text)
    text = re.sub(r' ?\n ?', '\n', text)
    text = MULTIBLANK_RE.sub('\n\n', text)
    return text.strip()


def normalize_inline(text: str) -> str:
    text = clean_text(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return '\n'.join(lines)


def load_md_title(stem: str) -> str:
    md_path = PARSED_DIR / f'{stem}.md'
    if not md_path.exists():
        return stem
    raw = md_path.read_text(encoding='utf-8', errors='ignore')[:4000]
    m = FRONTMATTER_RE.match(raw)
    if m:
        fm = m.group(1)
        if yaml is not None:
            try:
                data = yaml.safe_load(fm) or {}
                title = data.get('title')
                if title:
                    return TITLE_CLEAN_RE.sub(' ', str(title)).strip()
            except Exception:
                pass
        for line in fm.splitlines():
            if line.lower().startswith('title:'):
                return TITLE_CLEAN_RE.sub(' ', line.split(':', 1)[1]).strip().strip('"\'')
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith('---') and not line.startswith('<!--'):
            return TITLE_CLEAN_RE.sub(' ', line.lstrip('#').strip())
    return stem


def should_skip_text(text: str, page: int, kind: str) -> bool:
    compact = text.strip()
    if not compact:
        return True
    if page <= 12:
        for pat in SKIP_TEXT_PATTERNS:
            if pat.search(compact):
                return True
    if kind in {'table', 'index'} and page <= 12:
        if ('PART ' in compact or '차례' in compact or '그림 목록' in compact or '표 목록' in compact):
            return True
        if compact.count('[ 그림') >= 3 or compact.count('[ 표') >= 3 or compact.count('[그림') >= 3 or compact.count('[표') >= 3:
            return True
    if page <= 20 and len(compact) < 180 and not any(h in compact for h in DOMAIN_HINTS):
        return True
    if any(x in compact for x in ['부록 사주에 관한 Q&A', '나가며 사주를 통해서 인생을 멋지게 바꾸자']):
        return True
    return False


def detect_topics(text: str) -> list[str]:
    hits: list[str] = []
    for topic, keys in TOPICS.items():
        if topic == '십이운성':
            matched = False
            for k in keys:
                if len(k) > 1 and k in text:
                    matched = True
                    break
                if len(k) == 1 and SINGLE_STATE_PATTERNS.get(k) and SINGLE_STATE_PATTERNS[k].search(text):
                    matched = True
                    break
            if matched:
                hits.append(topic)
            continue
        if topic == '합충형파해':
            matched = any((len(k) > 1 and k in text) or (len(k) == 1 and RELATION_PATTERNS[k].search(text)) for k in keys)
            if matched:
                hits.append(topic)
            continue
        if topic == '건강':
            matched = any(k in text for k in ['건강', '질병', '아프'])
            if matched:
                hits.append(topic)
            continue
        if any(k in text for k in keys):
            hits.append(topic)
    return hits


def has_myeongsik_signature(text: str) -> bool:
    if sum(1 for c in TIANGAN if c in text) >= 3 and sum(1 for c in DIZHI if c in text) >= 3:
        return True
    return any(p.search(text) for p in MYEONGSIK_PATTERNS)


def detect_doc_type(kind: str, text: str) -> str:
    if kind == 'table' or text.count('|') >= 4:
        return 'table'
    if has_myeongsik_signature(text) or any(k in text for k in ['사주 예', '명조 예', '사례', '실전 예', '일주 예']):
        return 'case'
    if any(k in text for k in ['대운', '세운', '월운', '교운기']):
        return 'fortune'
    return 'theory'


def extract_entities(text: str) -> dict:
    states: list[str] = []
    for x in STATES:
        if len(x) > 1 and x in text:
            states.append(x)
        elif len(x) == 1 and SINGLE_STATE_PATTERNS.get(x) and SINGLE_STATE_PATTERNS[x].search(text):
            states.append(x)
    relations: list[str] = []
    for x in RELATIONS:
        if len(x) > 1 and x in text:
            relations.append(x)
        elif len(x) == 1 and RELATION_PATTERNS.get(x) and RELATION_PATTERNS[x].search(text):
            relations.append(x)
    entity = {
        'heavenly_stems': sorted({c for c in TIANGAN if c in text}),
        'earthly_branches': sorted({c for c in DIZHI if c in text}),
        'ten_gods': [x for x in TEN_GODS if x in text],
        'relations': relations,
        'sinsal': [x for x in SINSAL if x in text],
        'states': states,
        'has_myeongsik_signature': has_myeongsik_signature(text),
    }
    return entity


def iter_blocks(data: dict) -> Iterable[Block]:
    elements = data.get('elements', [])
    current_section = data.get('title', '')
    for el in elements:
        kind = el.get('category', '')
        if kind in IGNORE_CATEGORIES or kind not in KEEP_CATEGORIES:
            continue
        page = int(el.get('page') or 0)
        content = el.get('content') or {}
        raw = content.get('markdown') or content.get('html') or content.get('text') or ''
        text = normalize_inline(raw)
        if not text or should_skip_text(text, page, kind):
            continue
        if kind == 'heading1':
            current_section = text.splitlines()[0][:120]
        yield Block(kind=kind, text=text, page=page, section=current_section)


def split_long_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            candidates = [text.rfind('\n\n', start, end), text.rfind('\n', start, end), text.rfind('. ', start, end), text.rfind('다. ', start, end)]
            cut = max(candidates)
            if cut > start + 200:
                end = cut + (0 if text[cut:cut+2] == '\n\n' else 1)
        part = text[start:end].strip()
        if part:
            parts.append(part)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return parts


def merge_blocks(blocks: list[Block]) -> list[dict]:
    chunks: list[dict] = []
    section = ''
    buffer = ''
    start_page = None
    kind = 'paragraph'

    def flush() -> None:
        nonlocal buffer, start_page, section, kind
        text = buffer.strip()
        if not text:
            buffer = ''
            start_page = None
            return
        for part_idx, part in enumerate(split_long_text(text)):
            chunks.append({
                'section_title': section,
                'page_start': start_page,
                'page_end': last_page,
                'kind': kind,
                'text': part,
                'part_index': part_idx,
            })
        buffer = ''
        start_page = None

    last_page = 0
    for b in blocks:
        last_page = b.page
        if b.kind == 'heading1':
            flush()
            section = b.text
            chunks.append({
                'section_title': section,
                'page_start': b.page,
                'page_end': b.page,
                'kind': 'heading1',
                'text': b.text,
                'part_index': 0,
            })
            continue

        candidate = (buffer + '\n\n' + b.text).strip() if buffer else b.text
        if b.kind == 'table':
            flush()
            kind = 'table'
            buffer = b.text
            start_page = b.page
            flush()
            kind = 'paragraph'
            continue

        if start_page is None:
            start_page = b.page
            kind = b.kind
        if len(candidate) > MAX_CHARS and len(buffer) >= MIN_CHARS:
            flush()
            start_page = b.page
            kind = b.kind
            buffer = b.text
        else:
            buffer = candidate
    flush()
    return chunks


def process_file(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding='utf-8'))
    blocks = list(iter_blocks(data))
    merged = merge_blocks(blocks)
    doc_id = path.stem
    title = data.get('title') or load_md_title(doc_id)
    out: list[dict] = []
    for idx, chunk in enumerate(merged):
        text = normalize_inline(chunk['text'])
        if not text or len(text) < 20:
            continue
        if chunk['section_title'] and any(x in chunk['section_title'] for x in ['그림 목록', '표 목록', '차례']):
            continue
        doc_type = detect_doc_type(chunk['kind'], text)
        topics = detect_topics(text)
        entities = extract_entities(text)
        chunk_id = f'{doc_id}:{idx:05d}'
        core_topics = {'격국', '용신', '십신', '합충형파해', '신살', '십이운성', '대운세운'}
        low_value = (
            len(text) < 80 or
            (chunk['page_start'] <= 20 and not entities['has_myeongsik_signature'] and not (set(topics) & core_topics))
        )
        out.append({
            'chunk_id': chunk_id,
            'doc_id': doc_id,
            'title': title,
            'section_title': chunk['section_title'],
            'page_start': chunk['page_start'],
            'page_end': chunk['page_end'],
            'parser_source': 'upstage_document_parse',
            'source_file': str(path),
            'doc_type': doc_type,
            'element_kind': chunk['kind'],
            'topics': topics,
            'entities': entities,
            'text': text,
            'char_len': len(text),
            'is_myeongsik_chunk': entities['has_myeongsik_signature'],
            'embedding_recommended': not low_value,
        })
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks: list[dict] = []
    manifest: dict[str, dict] = {}

    for path in sorted(PARSED_DIR.glob('*.json')):
        chunks = process_file(path)
        out_path = DOCS_DIR / f'{path.stem}.jsonl'
        with out_path.open('w', encoding='utf-8') as f:
            for row in chunks:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
        all_chunks.extend(chunks)
        manifest[path.stem] = {
            'source_file': str(path),
            'chunk_file': str(out_path),
            'chunks': len(chunks),
            'avg_char_len': round(sum(c['char_len'] for c in chunks) / len(chunks), 1) if chunks else 0,
            'doc_types': sorted({c['doc_type'] for c in chunks}),
            'topics': sorted({t for c in chunks for t in c['topics']}),
            'myeongsik_chunks': sum(1 for c in chunks if c['is_myeongsik_chunk']),
            'embedding_recommended_chunks': sum(1 for c in chunks if c['embedding_recommended']),
        }

    with COMBINED_PATH.open('w', encoding='utf-8') as f:
        for row in all_chunks:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    summary = {
        'source_dir': str(PARSED_DIR),
        'output_dir': str(OUT_DIR),
        'documents': len(manifest),
        'chunks': len(all_chunks),
        'max_chars': MAX_CHARS,
        'min_chars': MIN_CHARS,
        'overlap': OVERLAP,
        'docs': manifest,
    }
    MANIFEST_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'documents': len(manifest),
        'chunks': len(all_chunks),
        'combined_path': str(COMBINED_PATH),
        'manifest_path': str(MANIFEST_PATH),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
