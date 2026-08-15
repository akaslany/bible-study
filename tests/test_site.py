#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,os,re,sys
ROOT=Path(__file__).resolve().parents[1];SOURCE=Path(os.environ.get('BIBLE_STUDY_SOURCE',Path.home()/'bible/2026'));errors=[]
studies=sorted((ROOT/'_studies').glob('*.md'));manifest=json.loads((ROOT/'_data/source-manifest.json').read_text());books=json.loads((ROOT/'_data/books.json').read_text())
source_files=manifest.get('source_files',[]);published_files=manifest.get('published_files',[]);omitted=manifest.get('omitted',[])
actual_sources=sorted(SOURCE.glob('*/*.md'))
if manifest.get('source_count')!=len(source_files) or len(source_files)!=len(actual_sources):errors.append(f"source_count={manifest.get('source_count')}/{len(source_files)}/{len(actual_sources)}")
if manifest.get('published_count')!=len(published_files):errors.append(f"published_count={manifest.get('published_count')}/{len(published_files)}")
if len(studies)!=len(published_files):errors.append(f"study files={len(studies)}/{len(published_files)}")
if len(published_files)+len(omitted)!=len(source_files):errors.append('source/public/omitted count mismatch')
if len(manifest.get('omitted',[]))!=1 or '2026-04-30-john-1.md' not in manifest['omitted'][0]['source_file']:errors.append('expected John duplicate omission missing')
counts={}
for p in studies:
 text=p.read_text();slug=re.search(r'^book_slug:\s*"(.*?)"$',text,re.M);ch=re.search(r'^chapter:\s*(\d+)$',text,re.M)
 if not slug or not ch:errors.append(f"metadata missing:{p.name}");continue
 counts[slug.group(1)]=counts.get(slug.group(1),0)+1
 for i,label in [(1,'오늘의 본문'),(2,'핵심 구절'),(3,'구조 분석'),(4,'해석'),(5,'삶 적용'),(6,'묵상/기도'),(7,'한눈에 보는 요약')]:
  if not re.search(r'^## '+str(i)+r'\..*'+re.escape(label),text,re.M):errors.append(f"{p.name}:missing section {i}")
 if '저장 파일명:' in text or '다음에는 성경 어느 장' in text:errors.append(f"automation leak:{p.name}")
 if re.search(r'^#\s+',text,re.M):errors.append(f"duplicate source H1:{p.name}")
 for line in text.splitlines():
  if ('NKRV:' in line or 'ESV:' in line) and len(line)>500:errors.append(f"overlong quotation:{p.name}")
acts_chapters=[int(p.stem.rsplit('-',1)[1]) for p in (SOURCE/'Acts').glob('*-acts-*.md')]
expected={'proverbs':31,'ecclesiastes':12,'job':42,'john':41,'acts':max(acts_chapters)}
if counts!=expected:errors.append(f"counts={counts}")
for item in manifest['source_files']:
 p=SOURCE/item['source_file']
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['source_sha256']:errors.append(f"source hash:{p}")
if len(books)!=5:errors.append('books data count')
for required in ['books.md','proverbs.md','ecclesiastes.md','job.md','john.md','acts.md','_layouts/book.html','_layouts/study.html','_layouts/home-bible.html']:
 if not (ROOT/required).exists():errors.append('missing:'+required)
if errors:print('\\n'.join('FAIL: '+x for x in errors[:80]));sys.exit(1)
print(f"SOURCE_AND_CONTENT_TESTS_PASS source={len(source_files)} published={len(published_files)} books=5 duplicate_omitted=1")
