#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import sys

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"_site"
errors=[]
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag in ('a','link') and d.get('href'): self.links.append(d['href'])

htmls=list(SITE.rglob('*.html'))
if len(htmls)<35: errors.append(f"too few html files: {len(htmls)}")
for p in htmls:
    text=p.read_text(errors='replace')
    if 'Liquid error' in text: errors.append(f"Liquid error in {p}")
    if '{&quot;name&quot;=&gt;' in text: errors.append(f"bad author rendering in {p}")
    parser=Links();parser.feed(text)
    for href in parser.links:
        if href.startswith(('http:','https:','mailto:','#','javascript:')): continue
        path=urlparse(href).path
        if path.startswith('/bible-study'): path=path[len('/bible-study'):]
        elif path.startswith('/'): errors.append(f"missing baseurl in {p}: {href}");continue
        target=(SITE/path.lstrip('/'))
        if path.endswith('/') or not target.suffix: target=target/'index.html'
        if not target.exists(): errors.append(f"broken link in {p}: {href} -> {target}")
post=SITE/'studies/2026-04-28-proverbs-31/index.html'
if not post.exists(): errors.append('chapter 31 page missing')
else:
    s=post.read_text()
    for marker in ['잠언 31장 묵상','잠언 31장 완독','인용 안내']:
        if marker not in s: errors.append(f"chapter 31 missing rendered marker: {marker}")
home=(SITE/'index.html').read_text()
for marker in ['우리 성경 공부','최근 공부','31 <small>/ 31장</small>','2026-04-28-proverbs-31']:
    if marker not in home: errors.append(f"home missing: {marker}")
if errors:
    print("\n".join("FAIL: "+e for e in errors[:50]));sys.exit(1)
print(f"BUILT_SITE_TESTS_PASS html={len(htmls)} internal_links=verified")
