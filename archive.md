---
layout: page
title: "날짜별"
permalink: /archive/
---
{% assign studies = site.studies | sort: "date" | reverse %}
<p class="page-lead">모든 공부 기록을 최근 날짜부터 확인할 수 있습니다.</p>
<div class="archive-list">{% for study in studies %}<a class="archive-item" href="{{ study.url | relative_url }}"><time datetime="{{ study.date | date_to_xmlschema }}">{{ study.date | date: "%Y.%m.%d" }}</time><span><strong>{{ study.book }} {{ study.chapter }}장</strong> · {{ study.series }}</span></a>{% endfor %}</div>
