#!/usr/bin/env python3
from pathlib import Path
from runpy import run_path
import hashlib
import json
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('BIBLE_STUDY_SOURCE', Path.home() / 'bible/2026'))
# Use the importer's registry so newly registered books enter the gate automatically.
BOOK_SOURCE_DIRS = {
    cfg['slug']: folder
    for folder, cfg in run_path(str(ROOT / 'scripts/import_studies.py'))['BOOKS'].items()
}
FIXED_COUNTS = {'proverbs': 31, 'ecclesiastes': 12, 'job': 42, 'john': 41, 'acts': 28}


def check_books(source, books, counts):
    errors = []
    expected = FIXED_COUNTS.copy()
    expected_book_count = len(BOOK_SOURCE_DIRS)
    if len(books) != expected_book_count:
        errors.append(f'books data count={len(books)}/{expected_book_count}')
    books_by_slug = {book['slug']: book for book in books}
    for slug in books_by_slug.keys() - BOOK_SOURCE_DIRS.keys():
        errors.append(f'unknown book data:{slug}')

    for slug, folder in BOOK_SOURCE_DIRS.items():
        chapters = [
            int(p.stem.rsplit('-', 1)[1])
            for p in (source / folder).glob(f'*-{slug}-*.md')
        ]
        latest_chapter = max(chapters, default=0)
        if latest_chapter and slug not in FIXED_COUNTS:
            expected[slug] = latest_chapter

        book = books_by_slug.get(slug)
        if book is None:
            errors.append(f'{slug} book data missing')
        elif latest_chapter:
            # John has two reading series: 41 records, with a maximum chapter of 21.
            expected_records = expected.get(slug, latest_chapter)
            if book['records'] != expected_records or book['latest_chapter'] != latest_chapter:
                errors.append(f'{slug} populated state mismatch')
        elif book['records'] != 0 or book['latest_chapter'] != 0 or book['status'] != '준비 중':
            errors.append(f'{slug} zero-record state mismatch')

    if counts != expected:
        errors.append(f'counts={counts}; expected={expected}')
    return errors


def main(root=ROOT, source=SOURCE):
    errors = []
    studies = sorted((root / '_studies').glob('*.md'))
    manifest = json.loads((root / '_data/source-manifest.json').read_text())
    books = json.loads((root / '_data/books.json').read_text())
    source_files = manifest.get('source_files', [])
    published_files = manifest.get('published_files', [])
    omitted = manifest.get('omitted', [])
    actual_sources = sorted(source.glob('*/*.md'))
    if manifest.get('source_count') != len(source_files) or len(source_files) != len(actual_sources):
        errors.append(f"source_count={manifest.get('source_count')}/{len(source_files)}/{len(actual_sources)}")
    declared_sources = {item['source_file'] for item in source_files}
    for path in actual_sources:
        relative = path.relative_to(source).as_posix()
        if relative not in declared_sources:
            errors.append(f'unimported source:{relative}')
            public_file = Path('_studies') / path.name
            if not (root / public_file).is_file():
                errors.append(f'public study missing:{public_file.as_posix()}')
    if manifest.get('published_count') != len(published_files):
        errors.append(f"published_count={manifest.get('published_count')}/{len(published_files)}")
    if len(studies) != len(published_files):
        errors.append(f'study files={len(studies)}/{len(published_files)}')
    if len(published_files) + len(omitted) != len(source_files):
        errors.append('source/public/omitted count mismatch')
    if len(omitted) != 1 or '2026-04-30-john-1.md' not in omitted[0]['source_file']:
        errors.append('expected John duplicate omission missing')

    counts = {}
    for p in studies:
        text = p.read_text()
        slug = re.search(r'^book_slug:\s*"(.*?)"$', text, re.M)
        ch = re.search(r'^chapter:\s*(\d+)$', text, re.M)
        if not slug or not ch:
            errors.append(f'metadata missing:{p.name}')
            continue
        counts[slug.group(1)] = counts.get(slug.group(1), 0) + 1
        for i, label in [(1, '오늘의 본문'), (2, '핵심 구절'), (3, '구조 분석'), (4, '해석'), (5, '삶 적용'), (6, '묵상/기도'), (7, '한눈에 보는 요약')]:
            if not re.search(r'^## ' + str(i) + r'\..*' + re.escape(label), text, re.M):
                errors.append(f'{p.name}:missing section {i}')
        if '저장 파일명:' in text or '다음에는 성경 어느 장' in text:
            errors.append(f'automation leak:{p.name}')
        if re.search(r'^#\s+', text, re.M):
            errors.append(f'duplicate source H1:{p.name}')
        for line in text.splitlines():
            if ('NKRV:' in line or 'ESV:' in line) and len(line) > 500:
                errors.append(f'overlong quotation:{p.name}')

    errors.extend(check_books(source, books, counts))
    for item in source_files:
        p = source / item['source_file']
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != item['source_sha256']:
            errors.append(f'source hash:{p}')
    required_files = ['books.md', '_layouts/book.html', '_layouts/study.html', '_layouts/home-bible.html']
    required_files.extend(f'{slug}.md' for slug in BOOK_SOURCE_DIRS)
    for required in required_files:
        if not (root / required).exists():
            errors.append('missing:' + required)
    if errors:
        print('\n'.join('FAIL: ' + x for x in errors[:80]))
        return 1
    print(f'SOURCE_AND_CONTENT_TESTS_PASS source={len(source_files)} published={len(published_files)} books={len(books)} duplicate_omitted=1')
    return 0


if __name__ == '__main__':
    sys.exit(main())
