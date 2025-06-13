---
tags: [department, {{ department_name }}]
created: {{ generated_at.strftime('%Y-%m-%d') }}
---

# {{ department_name }}

## メンバー

{% for link in member_links %}
- {{ link }}
{% endfor %}

## 連携部門

{% for link in partner_links %}
- {{ link }}
{% endfor %}

## 部門間ネットワーク

{{ network_diagram }}

{% if data.metrics %}
## メトリクス

- **中心性**: {{ data.metrics.centrality }}
- **連携部門数**: {{ data.metrics.connected_departments }}
- **総インタラクション数**: {{ data.metrics.total_interactions }}
{% endif %}

{% if data.patterns %}
## コラボレーションパターン

{% for pattern in data.patterns %}
- {{ pattern.type }}: {{ pattern.description }}
{% endfor %}
{% endif %}

---
*Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}*
