---
tags: [index, MOC]
created: {{ generated_at.strftime('%Y-%m-%d') }}
---

# AGO Group プロファイリングシステム

## 概要

このVaultは、AGO Groupの業務プロファイリングシステムによって自動生成されたものです。

{% if summary %}
- **分析期間**: {{ summary.start_date }} 〜 {{ summary.end_date }}
- **総人数**: {{ summary.total_persons }}
- **総活動数**: {{ summary.total_activities }}
- **ワークフロー数**: {{ summary.total_workflows }}
{% endif %}

## 人物プロファイル

{% for link in person_links %}
- {{ link }}
{% endfor %}

## ワークフロー

{% for link in workflow_links %}
- {{ link }}
{% endfor %}

## 部門

{% for link in department_links %}
- {{ link }}
{% endfor %}

## 最近のデイリーノート

{% for link in recent_daily_links %}
- {{ link }}
{% endfor %}

---
*Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}*
