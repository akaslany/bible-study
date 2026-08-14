#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
import hashlib, json, os, re, sys

ROOT=Path(__file__).resolve().parents[1]
STUDIES=sorted((ROOT/"_studies").glob("*.md"))
errors=[]
if len(STUDIES)!=31: errors.append(f"expected 31 studies, got {len(STUDIES)}")
chapters=[]
for p in STUDIES:
    text=p.read_text()
    m=re.search(r"^chapter:\s*(\d+)$",text,re.M)
    if not m: errors.append(f"{p.name}: missing chapter"); continue
    ch=int(m.group(1)); chapters.append(ch)
    for marker in ["layout: study", "public: true", "## 1. 오늘의 본문", "## 7. 한눈에 보는 요약"]:
        if marker not in text: errors.append(f"{p.name}: missing {marker}")
    if "저장 파일명:" in text or "다음에는 성경 어느 장" in text: errors.append(f"{p.name}: automation metadata leaked")
if chapters != list(range(1,32)): errors.append(f"chapter sequence invalid: {chapters}")
manifest=json.loads((ROOT/"_data/source-manifest.json").read_text())
if manifest.get('count')!=31: errors.append('manifest count is not 31')
SOURCE=Path(os.environ.get('BIBLE_PROVERBS_SOURCE', Path.home()/'bible/2026/Proverbs'))
for item in manifest['files']:
    p=SOURCE/item['source_file']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=item['source_sha256']: errors.append(f"source hash mismatch: {p}")
for required in ["index.md","proverbs.md","archive.md","about.md","_layouts/study.html","_layouts/home-bible.html","assets/main.scss"]:
    if not (ROOT/required).exists(): errors.append(f"missing site file: {required}")
if (ROOT/'.nojekyll').exists(): errors.append('.nojekyll must not exist for Jekyll site')
if errors:
    print("\n".join("FAIL: "+e for e in errors));sys.exit(1)
print("SOURCE_AND_CONTENT_TESTS_PASS studies=31 chapters=1..31")
