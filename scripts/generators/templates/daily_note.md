---
tags: [daily]
date: {{ date.strftime('%Y-%m-%d') }}
---

# {{ date|date_format }}

## サマリー

- **活動数**: {{ activity_count }}
- **参加者数**: {{ participant_count }}

## タイムライン

{% for activity in activities %}
### {{ activity.time }} {{ activity.type_emoji }} {{ activity.type }}

{{ activity.content }}

**参加者**: {% for p in activity.participants %}{{ p }}{% if not loop.last %}, {% endif %}{% endfor %}

{% if activity.tags %}
**タグ**: {% for tag in activity.tags %}{{ tag }} {% endfor %}
{% endif %}

---
{% endfor %}

---
*Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}*
