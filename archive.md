---
layout: page
title: "날짜별"
permalink: /archive/
---

{% assign studies = site.studies | sort: "date" | reverse %}
<div class="archive-list">
{% for study in studies %}
  <a class="archive-item" href="{{ study.url | relative_url }}">
    <time datetime="{{ study.date | date_to_xmlschema }}">{{ study.date | date: "%Y.%m.%d" }}</time>
    <span>{{ study.title }}</span>
  </a>
{% endfor %}
</div>
