---
layout: page
title: "잠언"
permalink: /proverbs/
---

{% assign studies = site.studies | sort: "chapter" %}

<div class="series-intro">
  <span class="eyebrow">완독 시리즈</span>
  <h2>잠언 1–31장</h2>
  <p>지혜의 시작부터 하나님을 경외하는 삶의 열매까지, 매일 한 장씩 읽은 기록입니다.</p>
  <div class="progress" role="progressbar" aria-label="잠언 읽기 진행률" aria-valuemin="0" aria-valuemax="31" aria-valuenow="31"><span style="width:100%"></span></div>
  <p class="progress-label">31 / 31장 · 완독</p>
</div>

<div class="chapter-list">
{% for study in studies %}
  <article class="chapter-row">
    <a class="chapter-number" href="{{ study.url | relative_url }}">{{ study.chapter }}</a>
    <div>
      <h3><a href="{{ study.url | relative_url }}">{{ study.title }}</a></h3>
      <p>{{ study.summary }}</p>
      <time datetime="{{ study.date | date_to_xmlschema }}">{{ study.date | date: "%Y.%m.%d" }}</time>
    </div>
  </article>
{% endfor %}
</div>
