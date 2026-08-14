---
layout: page
title: "성경별"
permalink: /books/
---
<p class="page-lead">지금까지 함께 읽은 성경을 책별·읽기 시리즈별로 모았습니다.</p>
<div class="book-grid book-index">{% for book in site.data.books %}<a class="book-card" href="{{ book.url | relative_url }}"><span class="book-en">{{ book.en }}</span><h2>{{ book.name }}</h2><p>{{ book.description }}</p><div class="book-meta"><span>{{ book.records }}개 기록</span><strong>{{ book.status }}</strong></div></a>{% endfor %}</div>
