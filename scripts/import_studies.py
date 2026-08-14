#!/usr/bin/env python3
"""Build public Jekyll study copies from the immutable local Bible archive."""
from pathlib import Path
from datetime import date
import argparse, hashlib, json, os, re

SOURCE_ROOT=Path(os.environ.get("BIBLE_STUDY_SOURCE",Path.home()/"bible/2026"))
BOOKS={
 "Proverbs":{"slug":"proverbs","ko":"잠언","en":"PROVERBS","chapters":31,"description":"지혜의 시작부터 하나님을 경외하는 삶의 열매까지"},
 "Ecclesiastes":{"slug":"ecclesiastes","ko":"전도서","en":"ECCLESIASTES","chapters":12,"description":"헛됨을 직면하며 하나님이 주신 오늘을 살아가는 지혜"},
 "Job":{"slug":"job","ko":"욥기","en":"JOB","chapters":42,"description":"설명되지 않는 고난 속에서 하나님을 신뢰하는 길"},
 "John":{"slug":"john","ko":"요한복음","en":"JOHN","chapters":21,"description":"말씀이 육신이 되어 오신 예수 그리스도를 만나는 기록"},
 "Acts":{"slug":"acts","ko":"사도행전","en":"ACTS","chapters":28,"description":"성령 안에서 복음이 예루살렘에서 땅끝으로 확장되는 여정"},
}
SECTION_TERMS={1:"오늘의 본문",2:"핵심 구절",3:"구조 분석",4:"해석",5:"삶 적용",6:"묵상/기도",7:"한눈에 보는 요약"}
AUTOMATION_LINES=("저장 파일명:","다음에는 성경 어느 장을 읽을까요?","까지 완료했습니다. 다음에는 성경 어느 장을 읽을까요?")


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def clean_md(s): return re.sub(r"[*_`]+","",s).strip()

def normalize_section(line):
 candidate=re.sub(r"^\s*#{1,6}\s*","",line).strip()
 candidate=clean_md(candidate)
 m=re.match(r"^([1-7])\.\s+",candidate)
 if m and SECTION_TERMS[int(m.group(1))] in candidate:
  return "## "+candidate
 return line.rstrip()

def public_body(text):
 out=[];current_reference="해당 장·절"
 for line in text.splitlines():
  plain=clean_md(re.sub(r"^\s*#{1,6}\s*","",line))
  if any(plain.startswith(x) or x in plain for x in AUTOMATION_LINES): continue
  # The page layout already supplies the canonical H1. Remove source report
  # banners such as "📖 ... 일일 묵상 리포트" to avoid duplicate headings.
  if re.match(r"^\s*#\s+",line) and not re.match(r"^[1-7]\.\s+",plain): continue
  if plain.startswith("- 구절:") or plain.startswith("구절:"):
   current_reference=plain.split(":",1)[1].strip()
  # Keep public quotations concise. The analysis is retained, while unusually
  # long multi-verse blocks point readers to the licensed Bible text.
  if len(plain)>500 and (plain.startswith("- NKRV:") or plain.startswith("- ESV:")):
   label="NKRV" if "NKRV:" in plain else "ESV"
   line=f"- {label}: *긴 본문 인용은 {current_reference}에서 확인하세요.*"
  out.append(normalize_section(line))
 return "\n".join(out).strip()+"\n"

def summary_from(text,book,chapter):
 lines=text.splitlines()
 for idx,line in enumerate(lines):
  plain=clean_md(line)
  if "장 전체 한 줄 요약" not in plain: continue
  same=plain.split(":",1)[1].strip() if ":" in plain else ""
  if len(same)>=20:return same
  for candidate in lines[idx+1:idx+7]:
   if not candidate.strip(): break
   cleaned=clean_md(re.sub(r"^\s*(?:[-*]|\d+[.)])\s*","",candidate))
   if len(cleaned)>=20:return cleaned
 for line in lines:
  plain=clean_md(line)
  if "오늘의 결론:" in plain:
   value=plain.split("오늘의 결론:",1)[1].strip()
   if len(value)>=20 and value!="한 문장":return value
 return f"{book} {chapter}장을 문맥 안에서 읽고 오늘의 삶에 적용합니다."

def has_sections(text):
 found=set()
 for line in text.splitlines():
  candidate=clean_md(re.sub(r"^\s*#{1,6}\s*","",line).strip())
  m=re.match(r"^([1-7])\.\s+",candidate)
  if m and SECTION_TERMS[int(m.group(1))] in candidate:found.add(int(m.group(1)))
 return found==set(range(1,8)),found

def body_chapter(text,book):
 for line in text.splitlines():
  plain=clean_md(re.sub(r"^\s*#{1,6}\s*","",line))
  m=re.search(r"오늘의 장:\s*"+re.escape(book)+r"\s*(\d+)장",plain)
  if m:return int(m.group(1))
 return None

def duplicate_signature(item):
 body=item['body']
 body="\n".join(line for line in body.splitlines() if "날짜:" not in clean_md(line))
 return hashlib.sha256((item['slug']+str(item['chapter'])+body).encode()).hexdigest()

def ordinal(n): return ["첫 번째","두 번째","세 번째","네 번째","다섯 번째"][n-1] if n<=5 else f"{n}번째"

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--source",type=Path,default=SOURCE_ROOT);ap.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[1]/"_studies");ap.add_argument("--manifest",type=Path,default=Path(__file__).resolve().parents[1]/"_data"/"source-manifest.json");args=ap.parse_args()
 source_files=[];items=[];source_manifest=[]
 for folder,cfg in BOOKS.items():
  for p in sorted((args.source/folder).glob("*.md")):
   source_files.append(p);m=re.fullmatch(r"(\d{4}-\d{2}-\d{2})-([a-z]+)-(\d+)\.md",p.name)
   if not m:raise SystemExit(f"Unexpected filename: {p.name}")
   day,slug,ch=m.group(1),m.group(2),int(m.group(3));text=p.read_text();ok,found=has_sections(text)
   if slug!=cfg['slug']:raise SystemExit(f"Slug mismatch: {p.name}")
   if not ok:raise SystemExit(f"{p.name}: section set {sorted(found)}")
   body_ch=body_chapter(text,cfg['ko'])
   if body_ch!=ch:raise SystemExit(f"{p.name}: body chapter {body_ch}, filename chapter {ch}")
   item={'path':p,'folder':folder,'slug':slug,'book':cfg['ko'],'book_en':cfg['en'],'expected':cfg['chapters'],'date':day,'chapter':ch,'text':text,'body':public_body(text),'summary':summary_from(text,cfg['ko'],ch)}
   items.append(item);source_manifest.append({'source_file':f"{folder}/{p.name}",'source_sha256':sha(p)})
 before={p:sha(p) for p in source_files}
 # Suppress only near-date exact duplicate reruns. The 2026-04-30 John 1
 # report is identical to the canonical 2026-05-01 report except for date.
 kept=[];omitted=[];by_sig={}
 for item in items:
  sig=duplicate_signature(item);prior=by_sig.get(sig)
  if prior and abs((date.fromisoformat(item['date'])-date.fromisoformat(prior['date'])).days)<=2:
   kept.remove(prior);omitted.append({'source_file':f"{prior['folder']}/{prior['path'].name}",'reason':f"near-date exact duplicate of {item['path'].name}"});kept.append(item);by_sig[sig]=item
  else:kept.append(item);by_sig[sig]=item
 # Create reading series after deduplication; a chapter reset starts a new series.
 for folder,cfg in BOOKS.items():
  rows=[x for x in kept if x['folder']==folder];series=[];cur=[]
  for item in rows:
   if cur and item['chapter']<=cur[-1]['chapter']:series.append(cur);cur=[]
   cur.append(item)
  if cur:series.append(cur)
  for num,group in enumerate(series,1):
   chapters=[x['chapter'] for x in group];complete=chapters==list(range(1,cfg['chapters']+1));missing=sorted(set(range(1,cfg['chapters']+1))-set(chapters))
   sid=f"{cfg['slug']}-2026-s{num}";label=f"{cfg['ko']} {ordinal(num)} 읽기"
   for idx,item in enumerate(group):
    item.update(series_id=sid,series=label,series_number=num,series_complete=complete,series_closed=num<len(series),series_missing=missing,previous=group[idx-1] if idx else None,next=group[idx+1] if idx+1<len(group) else None)
 args.output.mkdir(parents=True,exist_ok=True)
 for stale in args.output.glob("*.md"):stale.unlink()
 public_manifest=[]
 for item in kept:
  p=item['path'];meta=["---","layout: study",f"title: {json.dumps(item['book']+' '+str(item['chapter'])+'장 묵상',ensure_ascii=False)}",f"date: {item['date']} 04:00:00 +0900",f"book: {json.dumps(item['book'],ensure_ascii=False)}",f"book_slug: {json.dumps(item['slug'])}",f"book_en: {json.dumps(item['book_en'])}",f"chapter: {item['chapter']}",f"expected_chapters: {item['expected']}",f"series: {json.dumps(item['series'],ensure_ascii=False)}",f"series_id: {json.dumps(item['series_id'])}",f"series_number: {item['series_number']}",f"series_complete: {str(item['series_complete']).lower()}",f"series_closed: {str(item['series_closed']).lower()}",f"series_missing: {json.dumps(item['series_missing'])}",f"passage: {json.dumps(item['book']+' '+str(item['chapter'])+'장',ensure_ascii=False)}",f"summary: {json.dumps(item['summary'],ensure_ascii=False)}",f"book_url: {json.dumps('/proverbs/' if item['slug']=='proverbs' else '/books/'+item['slug']+'/')}","public: true"]
  if item['previous']:meta += [f"previous_chapter: {item['previous']['chapter']}",f"previous_url: {json.dumps('/studies/'+item['previous']['path'].stem+'/')}"]
  if item['next']:meta += [f"next_chapter: {item['next']['chapter']}",f"next_url: {json.dumps('/studies/'+item['next']['path'].stem+'/')}"]
  else:meta += ["series_end: true",f"series_end_label: {json.dumps(item['book']+' '+str(item['expected'])+'장 완독 ✓' if item['series_complete'] else '현재까지 기록',ensure_ascii=False)}"]
  meta += ["---",""]
  out=args.output/p.name;out.write_text("\n".join(meta)+item['body'])
  public_manifest.append({'source_file':f"{item['folder']}/{p.name}",'public_file':f"_studies/{p.name}",'book_slug':item['slug'],'chapter':item['chapter'],'date':item['date'],'series_id':item['series_id']})
 after={p:sha(p) for p in source_files}
 if before!=after:raise SystemExit("Source archive changed during import")
 book_data=[]
 for folder,cfg in BOOKS.items():
  rows=[x for x in kept if x['folder']==folder];series_ids=[]
  for x in rows:
   if x['series_id'] not in series_ids:series_ids.append(x['series_id'])
  complete_count=sum(1 for sid in series_ids if next(x for x in rows if x['series_id']==sid)['series_complete'])
  latest_group=[x for x in rows if x['series_id']==series_ids[-1]];latest_ch=latest_group[-1]['chapter']
  if latest_group[-1]['series_complete']:status="완독" if len(series_ids)==1 else f"완독 {complete_count}회 · 총 {len(rows)}개 기록"
  else:status=f"진행 중 · {latest_ch} / {cfg['chapters']}장"
  url="/proverbs/" if cfg['slug']=="proverbs" else f"/books/{cfg['slug']}/"
  book_data.append({'name':cfg['ko'],'slug':cfg['slug'],'en':cfg['en'],'description':cfg['description'],'expected_chapters':cfg['chapters'],'records':len(rows),'series_count':len(series_ids),'complete_series':complete_count,'status':status,'url':url,'latest_chapter':latest_ch})
 args.manifest.parent.mkdir(parents=True,exist_ok=True);args.manifest.write_text(json.dumps({'source_root':'private Bible archive','source_count':len(source_manifest),'published_count':len(public_manifest),'omitted':omitted,'public_transformations':['automation metadata removed','quotation lines over 500 characters replaced by chapter-and-verse reference'],'source_files':source_manifest,'published_files':public_manifest},ensure_ascii=False,indent=2)+"\n")
 (args.manifest.parent/'books.json').write_text(json.dumps(book_data,ensure_ascii=False,indent=2)+"\n")
 print(f"IMPORTED source={len(source_manifest)} published={len(public_manifest)} omitted={len(omitted)} books={len(BOOKS)} SOURCE_UNCHANGED")

if __name__=="__main__":main()
