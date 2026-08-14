#!/usr/bin/env python3
"""Create public Jekyll study copies from the immutable Proverbs archive."""
from pathlib import Path
import argparse, hashlib, json, os, re

SOURCE = Path(os.environ.get("BIBLE_PROVERBS_SOURCE", Path.home()/"bible/2026/Proverbs"))
REQUIRED = ["오늘의 본문", "핵심 구절", "구조 분석", "신학적·지혜문학적 해석", "삶 적용", "묵상/기도", "한눈에 보는 요약"]
AUTOMATION_LINES = ("저장 파일명:", "다음에는 성경 어느 장을 읽을까요?")


def digest_tree(files):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def summary_from(text, chapter):
    # The historical reports used both bullet and numbered forms. Read the
    # first substantive line after the summary label instead of assuming one.
    lines=text.splitlines()
    for idx,line in enumerate(lines):
        if "장 전체 한 줄 요약" not in line:
            continue
        for candidate in lines[idx+1:idx+6]:
            if not candidate.strip():
                break
            cleaned=re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", candidate).strip()
            if len(cleaned) >= 20:
                return cleaned
    conclusion = re.search(r"오늘의 결론:\s*(.+)", text)
    value=conclusion.group(1).strip() if conclusion else ""
    if len(value) >= 20 and value != "한 문장":
        return value
    return f"잠언 {chapter}장을 문맥 안에서 읽고 삶의 지혜를 묵상합니다."


def public_body(text):
    lines=[]
    for line in text.splitlines():
        if any(line.strip().startswith(x) for x in AUTOMATION_LINES):
            continue
        # Reports were generated over time with either no heading marker,
        # '#', or '##'. Normalize only the seven known top-level sections;
        # ordinary numbered lists must remain numbered lists.
        candidate=re.sub(r"^\s*#{1,6}\s*", "", line).strip()
        if re.match(r"^[1-7]\.\s+", candidate) and any(marker in candidate for marker in REQUIRED):
            line="## "+candidate
        lines.append(line.rstrip())
    return "\n".join(lines).strip()+"\n"


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=SOURCE)
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1]/"_studies")
    ap.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parents[1]/"_data"/"source-manifest.json")
    args=ap.parse_args()
    files=sorted(args.source.glob("*.md"))
    before=digest_tree(files)
    parsed=[]
    for p in files:
        m=re.fullmatch(r"(\d{4}-\d{2}-\d{2})-proverbs-(\d+)\.md",p.name)
        if not m: raise SystemExit(f"Unexpected filename: {p.name}")
        date,chapter=m.group(1),int(m.group(2)); text=p.read_text()
        missing=[x for x in REQUIRED if x not in text]
        if missing: raise SystemExit(f"{p.name}: missing sections {missing}")
        body_ch=re.search(r"오늘의 장:\s*잠언\s*(\d+)장",text)
        if not body_ch or int(body_ch.group(1)) != chapter: raise SystemExit(f"{p.name}: chapter mismatch")
        parsed.append((p,date,chapter,text))
    chapters=[x[2] for x in parsed]
    if chapters != list(range(1,32)): raise SystemExit(f"Expected chapters 1..31, got {chapters}")
    args.output.mkdir(parents=True,exist_ok=True)
    for stale in args.output.glob("*.md"): stale.unlink()
    manifest=[]
    for p,date,ch,text in parsed:
        summary=summary_from(text,ch)
        prev_ch=ch-1 if ch>1 else None; next_ch=ch+1 if ch<31 else None
        meta=["---",'layout: study',f'title: "잠언 {ch}장 묵상"',f'date: {date} 04:00:00 +0900','book: "잠언"','book_slug: "proverbs"',f'chapter: {ch}','series: "잠언 첫 번째 읽기"','series_id: "proverbs-2026"',f'session: {ch}',f'passage: "잠언 {ch}장"',f'summary: {json.dumps(summary,ensure_ascii=False)}','public: true']
        if prev_ch: meta += [f'previous_chapter: {prev_ch}',f'previous_url: "/studies/{parsed[ch-2][0].stem}/"']
        if next_ch: meta += [f'next_chapter: {next_ch}',f'next_url: "/studies/{parsed[ch][0].stem}/"']
        meta += ["---",""]
        out=args.output/p.name
        out.write_text("\n".join(meta)+public_body(text))
        manifest.append({'source_file':p.name,'source_sha256':before[p.name],'public_file':str(out.relative_to(args.output.parent)),'chapter':ch,'date':date})
    after=digest_tree(files)
    if before != after: raise SystemExit("Source archive changed during import")
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    # Keep local account paths out of the public repository.
    args.manifest.write_text(json.dumps({'source_root':'private Proverbs archive','count':len(manifest),'files':manifest},ensure_ascii=False,indent=2)+"\n")
    print(f"IMPORTED {len(manifest)} chapters; SOURCE_UNCHANGED; chapters={chapters[0]}..{chapters[-1]}")

if __name__ == "__main__": main()
