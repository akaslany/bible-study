# 우리 성경 공부

잠언 1–31장을 한 장씩 읽고 문맥, 핵심 구절, 해석, 적용과 기도를 정리한 Jekyll 정적 사이트입니다.

- 공개 주소: https://akaslany.github.io/bible-study/
- 구성: Jekyll `studies` collection
- 현재 시리즈: 잠언 1–31장(완독)

## 원본 갱신

원본 묵상 보고서는 이 저장소 밖의 비공개 아카이브에 보존합니다. 공개 사본은 다음 명령으로 다시 생성합니다.

```bash
BIBLE_PROVERBS_SOURCE="$HOME/bible/2026/Proverbs" python3 scripts/import_proverbs.py
python3 tests/test_site.py
```

변환 과정은 31개 장의 연속성, 필수 섹션, 원본 SHA-256 불변성을 검사하고 공개 페이지에서 자동화용 파일명 문구를 제거합니다.

## 로컬 빌드 검증

```bash
docker run --rm -v "$PWD:/srv/jekyll" -w /srv/jekyll \
  jekyll/jekyll:4.2.2 \
  sh -lc 'jekyll build --trace --baseurl /bible-study'
python3 tests/check_built_site.py
```
