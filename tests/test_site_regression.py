"""Exercise the publish gate against generated, disposable source archives."""
from collections import Counter
from contextlib import redirect_stdout
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from runpy import run_path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SITE = run_path(str(ROOT / 'tests/test_site.py'))
REGISTRY = run_path(str(ROOT / 'scripts/import_studies.py'))['BOOKS']


class SiteRegressionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'site'
        self.source = Path(temporary.name) / 'source'
        for folder, cfg in REGISTRY.items():
            slug = cfg['slug']
            if slug == 'john':
                # Preserve the real archive's 41 records across two reading series.
                series = [
                    (date(2026, 5, 1), [ch for ch in range(1, 22) if ch != 3]),
                    (date(2026, 6, 1), list(range(1, 22))),
                ]
            else:
                count = SITE['FIXED_COUNTS'].get(slug, 1 if slug == 'colossians' else 0)
                series = [(date(2026, 1, 1), list(range(1, count + 1)))]
            for start, chapters in series:
                for offset, chapter in enumerate(chapters):
                    self.write_source(folder, cfg, start + timedelta(days=offset), chapter)
        self.write_source('John', REGISTRY['John'], date(2026, 4, 30), 1)
        self.import_source()
        for relative in ['books.md', '_layouts/book.html', '_layouts/study.html', '_layouts/home-bible.html']:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        for cfg in REGISTRY.values():
            (self.root / f"{cfg['slug']}.md").touch()

    def write_source(self, folder, cfg, day, chapter):
        path = self.source / folder / f"{day}-{cfg['slug']}-{chapter}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"## 1. 오늘의 본문\n- 오늘의 장: {cfg['ko']} {chapter}장\n"
            "## 2. 핵심 구절\n## 3. 구조 분석\n## 4. 해석\n"
            "## 5. 삶 적용\n## 6. 묵상/기도\n## 7. 한눈에 보는 요약\n"
        )
        return path

    def import_source(self):
        subprocess.run(
            [
                sys.executable, str(ROOT / 'scripts/import_studies.py'),
                '--source', str(self.source),
                '--output', str(self.root / '_studies'),
                '--manifest', str(self.root / '_data/source-manifest.json'),
            ],
            check=True, capture_output=True, text=True,
        )
        self.books = json.loads((self.root / '_data/books.json').read_text())
        manifest = json.loads((self.root / '_data/source-manifest.json').read_text())
        self.counts = dict(Counter(item['book_slug'] for item in manifest['published_files']))

    def run_gate(self):
        output = StringIO()
        with redirect_stdout(output):
            status = SITE['main'](root=self.root, source=self.source)
        return status, output.getvalue()

    def test_colossians_chapter_passes_full_gate(self):
        status, output = self.run_gate()
        self.assertEqual(status, 0, output)
        self.assertIn('SOURCE_AND_CONTENT_TESTS_PASS', output)
        self.assertIn(f'books={len(REGISTRY)}', output)
        self.assertEqual(self.counts['colossians'], 1)

    def test_fake_colossians_study_count_mismatch_fails(self):
        study = self.root / '_studies/2026-01-01-colossians-1.md'
        fake = self.root / '_studies/2026-01-02-colossians-2.md'
        fake.write_text(study.read_text().replace('chapter: 1\n', 'chapter: 2\n'))
        status, output = self.run_gate()
        self.assertEqual(status, 1, output)
        self.assertIn('FAIL: counts=', output)
        self.assertIn("'colossians': 2", output.split('; expected=')[0])
        self.assertIn("'colossians': 1", output.split('; expected=')[1])
        # Confirm that the counts check itself rejects the extra fixture study.
        self.counts['colossians'] = 2
        errors = SITE['check_books'](self.source, self.books, self.counts)
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].startswith('counts='), errors)

    def test_next_colossians_chapter_passes_after_import(self):
        self.write_source('Colossians', REGISTRY['Colossians'], date(2026, 1, 2), 2)
        self.import_source()
        status, output = self.run_gate()
        self.assertEqual(status, 0, output)
        self.assertEqual(self.counts['colossians'], 2)

    def test_unimported_colossians_chapter_fails_with_missing_path(self):
        self.write_source('Colossians', REGISTRY['Colossians'], date(2026, 1, 2), 2)
        status, output = self.run_gate()
        self.assertEqual(status, 1, output)
        self.assertIn('FAIL: source_count=', output)
        self.assertIn('FAIL: unimported source:Colossians/2026-01-02-colossians-2.md', output)
        self.assertIn('FAIL: public study missing:_studies/2026-01-02-colossians-2.md', output)
        self.assertEqual(self.counts['colossians'], 1)
        colossians = next(book for book in self.books if book['slug'] == 'colossians')
        self.assertEqual(colossians['records'], 1)

    def test_colossians_zero_record_state_passes(self):
        (self.source / 'Colossians/2026-01-01-colossians-1.md').unlink()
        self.import_source()
        status, output = self.run_gate()
        self.assertEqual(status, 0, output)
        self.assertNotIn('colossians', self.counts)

    def test_populated_metadata_checked_for_every_book(self):
        # Include books that are empty in the fixture and the two-series John case.
        for folder, cfg in REGISTRY.items():
            if cfg['slug'] not in self.counts:
                self.write_source(folder, cfg, date(2026, 1, 1), 1)
        self.import_source()
        for book in self.books:
            for field in ['records', 'latest_chapter']:
                with self.subTest(slug=book['slug'], field=field):
                    original = book[field]
                    book[field] = original + 1
                    errors = SITE['check_books'](self.source, self.books, self.counts)
                    self.assertEqual(errors, [f"{book['slug']} populated state mismatch"])
                    book[field] = original

    def test_zero_record_metadata_checked_for_every_book(self):
        empty_source = self.source / 'empty'
        books = [
            dict(book, records=0, latest_chapter=0, status='준비 중')
            for book in self.books
        ]
        for book in books:
            for field, value in [('records', 1), ('latest_chapter', 1), ('status', '완독')]:
                with self.subTest(slug=book['slug'], field=field):
                    original = book[field]
                    book[field] = value
                    errors = SITE['check_books'](empty_source, books, SITE['FIXED_COUNTS'])
                    self.assertEqual(errors, [f"{book['slug']} zero-record state mismatch"])
                    book[field] = original

    def test_missing_book_definition_fails(self):
        books = [book for book in self.books if book['slug'] != 'colossians']
        errors = SITE['check_books'](self.source, books, self.counts)
        self.assertIn(f'books data count={len(books)}/{len(REGISTRY)}', errors)
        self.assertIn('colossians book data missing', errors)

    def test_unregistered_book_definition_fails(self):
        books = self.books + [dict(self.books[-1], slug='unregistered')]
        errors = SITE['check_books'](self.source, books, self.counts)
        self.assertIn('unknown book data:unregistered', errors)

    def test_future_registered_book_uses_same_checks_and_count(self):
        cfg = dict(REGISTRY['Colossians'], slug='future-book')
        self.write_source('FutureBook', cfg, date(2026, 1, 1), 1)
        books = self.books + [dict(self.books[-1], slug='future-book')]
        counts = dict(self.counts, **{'future-book': 1})
        with patch.dict(SITE['BOOK_SOURCE_DIRS'], {'future-book': 'FutureBook'}):
            self.assertEqual(SITE['check_books'](self.source, books, counts), [])
            counts['future-book'] = 2
            errors = SITE['check_books'](self.source, books, counts)
            self.assertEqual(len(errors), 1, errors)
            self.assertTrue(errors[0].startswith('counts='), errors)

    def test_fixed_book_source_deletion_still_fails(self):
        for slug, count in SITE['FIXED_COUNTS'].items():
            with self.subTest(slug=slug):
                folder = SITE['BOOK_SOURCE_DIRS'][slug]
                # Remove every copy of the last chapter, including both John series.
                paths = list((self.source / folder).glob(f'*-{slug}-{21 if slug == "john" else count}.md'))
                originals = {path: path.read_text() for path in paths}
                for path in paths:
                    path.unlink()
                counts = dict(self.counts)
                counts[slug] -= len(paths)
                errors = SITE['check_books'](self.source, self.books, counts)
                self.assertTrue(any(error.startswith('counts=') for error in errors), errors)
                for path, text in originals.items():
                    path.write_text(text)


if __name__ == '__main__':
    unittest.main()
