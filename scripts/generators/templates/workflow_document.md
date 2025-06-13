---
tags: [workflow, {{ workflow.frequency }}, {{ workflow.priority.value }}]
created: {{ generated_at.strftime('%Y-%m-%d') }}
---

# {{ workflow.name }}

## 概要

- **オーナー**: {{ workflow.owner.name|wikilink }}
- **頻度**: {{ workflow.frequency }}
- **優先度**: {{ workflow.priority.value }}
- **総所要時間**: {{ workflow.get_total_duration() }}時間

## 参加者

{% for link in participant_links %}
- {{ link }}
{% endfor %}

## ワークフローステップ

{% for step in step_details %}
### {{ step.number }}. {{ step.name }}

- **説明**: {{ step.description }}
- **責任者**: {{ step.responsible }}
- **所要時間**: {{ step.duration }}
{% if step.dependencies %}
- **依存関係**: 
  {%- for dep in step.dependencies %} {{ dep }}{%- if not loop.last %}, {% endif %}{%- endfor %}
{% endif %}

{% endfor %}

## フロー図

{{ mermaid_diagram }}

{% if analysis %}
## 分析結果

### ボトルネック
{{ analysis.bottlenecks }}

### 改善提案
{{ analysis.recommendations }}
{% endif %}

---
*Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}*
