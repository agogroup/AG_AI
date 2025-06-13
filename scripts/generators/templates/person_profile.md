---
tags: [person, {{ person.department }}]
created: {{ generated_at.strftime('%Y-%m-%d') }}
---

# {{ person.name }}

## 基本情報

- **部門**: {{ person.department }}
- **役職**: {{ person.role }}
- **メール**: {{ person.email }}

## スキル・専門領域

{% for tag in skill_tags %}
{{ tag }} 
{%- endfor %}

## 活動サマリー

- **総活動数**: {{ activity_summary.total_count }}
- **活動タイプ別**:
{% for type, count in activity_summary.by_type.items() %}
  - {{ type }}: {{ count }}回
{% endfor %}

### 最近の活動
{% for activity in activity_summary.recent_activities %}
- {{ activity.date }} - {{ activity.type }}: {{ activity.content_preview }}
{% endfor %}

## 協働者ネットワーク

{% for link in collaborator_links %}
- {{ link }}
{% endfor %}

{% if profile %}
## 詳細分析

### 活動パターン
{{ profile.activity_analysis.summary }}

### 専門性
{{ profile.expertise_summary }}

### ネットワーク分析
{{ profile.network_analysis }}
{% endif %}

---
*Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}*
