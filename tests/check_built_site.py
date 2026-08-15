#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
import json,sys
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'_site';errors=[]
manifest=json.loads((ROOT/'_data/source-manifest.json').read_text());books=json.loads((ROOT/'_data/books.json').read_text())
study_count=manifest['published_count'];acts=next(x for x in books if x['slug']=='acts');latest_acts=next(x for x in reversed(manifest['published_files']) if x['book_slug']=='acts')
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag in ('a','link') and d.get('href'):self.links.append(d['href'])
htmls=list(SITE.rglob('*.html'))
if len(htmls)<study_count+10:errors.append(f"too few html={len(htmls)}")
for p in htmls:
 text=p.read_text(errors='replace')
 if 'Liquid error' in text:errors.append(f"Liquid:{p}")
 if '{&quot;name&quot;=&gt;' in text:errors.append(f"author:{p}")
 parser=Links();parser.feed(text)
 for href in parser.links:
  if href.startswith(('http:','https:','mailto:','#','javascript:')):continue
  path=urlparse(href).path
  if path.startswith('/bible-study'):path=path[len('/bible-study'):]
  elif path.startswith('/'):errors.append(f"baseurl:{p}:{href}");continue
  target=SITE/path.lstrip('/')
  if path.endswith('/') or not target.suffix:target=target/'index.html'
  if not target.exists():errors.append(f"broken:{p}:{href}")
latest_rel=latest_acts['public_file'].replace('_studies/','studies/').replace('.md','/index.html')
for rel,markers in {'index.html':['성경별 공부','사도행전','최근 공부'],'books/index.html':['잠언','전도서','욥기','요한복음','사도행전'],'proverbs/index.html':['잠언 첫 번째 읽기'],'books/john/index.html':['요한복음 첫 번째 읽기','20개 기록 · 3장 없음','요한복음 두 번째 읽기'],'books/acts/index.html':[f"{acts['latest_chapter']}장까지"],latest_rel:[f"사도행전 {acts['latest_chapter']}장 묵상",'현재까지 기록','인용 안내']}.items():
 p=SITE/rel
 if not p.exists():errors.append('missing page:'+rel);continue
 t=p.read_text()
 for m in markers:
  if m not in t:errors.append(f"{rel}:missing:{m}")
if len(list((SITE/'studies').glob('*/index.html')))!=study_count:errors.append('study html count')
if list(SITE.rglob('*.py')):errors.append('scripts leaked into site')
if errors:print('\\n'.join('FAIL: '+x for x in errors[:80]));sys.exit(1)
print(f"BUILT_SITE_TESTS_PASS html={len(htmls)} studies={study_count} internal_links=verified")
