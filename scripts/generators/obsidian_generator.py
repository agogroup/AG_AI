import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from jinja2 import Environment, FileSystemLoader, Template
import re

from scripts.models import Person, Activity, Workflow, ActivityType
from scripts.exceptions import OutputGenerationError
from scripts.utils import sanitize_filename, ensure_directory


logger = logging.getLogger(__name__)


class ObsidianGenerator:
    """Obsidian用のMarkdownファイルを生成するクラス"""
    
    def __init__(self, output_dir: str = "output/obsidian", template_dir: Optional[str] = None):
        """
        Args:
            output_dir: 出力ディレクトリのパス
            template_dir: テンプレートディレクトリのパス
        """
        self.output_dir = Path(output_dir)
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / "templates"
        
        # 出力ディレクトリの作成
        ensure_directory(self.output_dir)
        ensure_directory(self.output_dir / "persons")
        ensure_directory(self.output_dir / "workflows")
        ensure_directory(self.output_dir / "departments")
        ensure_directory(self.output_dir / "daily")
        
        # Jinja2環境の設定
        self._setup_jinja_env()
        
        # 生成されたファイルの追跡
        self.generated_files = {
            'persons': [],
            'workflows': [],
            'departments': [],
            'daily': [],
            'index': None
        }
        
    def _setup_jinja_env(self) -> None:
        """Jinja2環境をセットアップ"""
        # テンプレートディレクトリが存在しない場合は作成
        ensure_directory(self.template_dir)
        
        # デフォルトテンプレートを作成
        self._create_default_templates()
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # カスタムフィルターの追加
        self.env.filters['wikilink'] = self._make_wikilink
        self.env.filters['date_format'] = self._format_date
        self.env.filters['tag_format'] = self._format_tag
        
    def generate_person_profile(self, person: Person, profile_data: Dict[str, Any]) -> str:
        """人物プロファイルのMarkdownを生成
        
        Args:
            person: 人物オブジェクト
            profile_data: プロファイルデータ（PersonProfilerの出力）
            
        Returns:
            生成されたファイルパス
        """
        try:
            template = self.env.get_template('person_profile.md')
            
            # リンクとタグの生成
            collaborator_links = [
                self._make_wikilink(c.name) for c in person.collaborators
            ]
            
            skill_tags = [self._format_tag(skill) for skill in person.skills]
            
            # 活動サマリーの生成
            activity_summary = self._generate_activity_summary(person.activities)
            
            # テンプレートのレンダリング
            content = template.render(
                person=person,
                profile=profile_data,
                collaborator_links=collaborator_links,
                skill_tags=skill_tags,
                activity_summary=activity_summary,
                generated_at=datetime.now()
            )
            
            # ファイルの保存
            filename = sanitize_filename(person.name) + ".md"
            filepath = self.output_dir / "persons" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.generated_files['persons'].append(str(filepath))
            logger.info(f"人物プロファイルを生成しました: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            raise OutputGenerationError(f"人物プロファイルの生成に失敗しました: {str(e)}")
    
    def generate_workflow_document(self, workflow: Workflow, analysis_data: Dict[str, Any]) -> str:
        """ワークフロー文書のMarkdownを生成
        
        Args:
            workflow: ワークフローオブジェクト
            analysis_data: ワークフロー分析データ
            
        Returns:
            生成されたファイルパス
        """
        try:
            template = self.env.get_template('workflow_document.md')
            
            # 参加者リンクの生成
            participant_links = [
                self._make_wikilink(p.name) for p in workflow.get_participants()
            ]
            
            # ステップの詳細情報を整形
            step_details = []
            for i, step in enumerate(workflow.steps):
                detail = {
                    'number': i + 1,
                    'name': step.name,
                    'description': step.description,
                    'responsible': self._make_wikilink(step.responsible.name) if step.responsible else "未割当",
                    'duration': f"{step.duration_hours}時間" if step.duration_hours else "未定",
                    'dependencies': [self._make_wikilink(d.name) for d in step.dependencies]
                }
                step_details.append(detail)
            
            # Mermaidダイアグラムの生成（analysis_dataから取得）
            mermaid_diagram = analysis_data.get('visualization', '')
            
            # テンプレートのレンダリング
            content = template.render(
                workflow=workflow,
                analysis=analysis_data,
                participant_links=participant_links,
                step_details=step_details,
                mermaid_diagram=mermaid_diagram,
                generated_at=datetime.now()
            )
            
            # ファイルの保存
            filename = sanitize_filename(workflow.name) + ".md"
            filepath = self.output_dir / "workflows" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.generated_files['workflows'].append(str(filepath))
            logger.info(f"ワークフロー文書を生成しました: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            raise OutputGenerationError(f"ワークフロー文書の生成に失敗しました: {str(e)}")
    
    def generate_department_report(self, department_name: str, department_data: Dict[str, Any]) -> str:
        """部門レポートのMarkdownを生成
        
        Args:
            department_name: 部門名
            department_data: 部門分析データ
            
        Returns:
            生成されたファイルパス
        """
        try:
            template = self.env.get_template('department_report.md')
            
            # メンバーリンクの生成
            member_links = []
            if 'members' in department_data:
                member_links = [self._make_wikilink(m) for m in department_data['members']]
            
            # 連携部門リンクの生成
            partner_links = []
            if 'partner_departments' in department_data:
                partner_links = [self._make_wikilink(d) for d in department_data['partner_departments']]
            
            # Mermaidダイアグラムの生成
            network_diagram = department_data.get('network_visualization', '')
            
            # テンプレートのレンダリング
            content = template.render(
                department_name=department_name,
                data=department_data,
                member_links=member_links,
                partner_links=partner_links,
                network_diagram=network_diagram,
                generated_at=datetime.now()
            )
            
            # ファイルの保存
            filename = sanitize_filename(department_name) + ".md"
            filepath = self.output_dir / "departments" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.generated_files['departments'].append(str(filepath))
            logger.info(f"部門レポートを生成しました: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            raise OutputGenerationError(f"部門レポートの生成に失敗しました: {str(e)}")
    
    def generate_daily_note(self, date: datetime, activities: List[Activity]) -> str:
        """デイリーノートのMarkdownを生成
        
        Args:
            date: 日付
            activities: その日の活動リスト
            
        Returns:
            生成されたファイルパス
        """
        try:
            template = self.env.get_template('daily_note.md')
            
            # 活動を時系列でソート
            sorted_activities = sorted(activities, key=lambda a: a.timestamp)
            
            # 活動の詳細情報を整形
            activity_details = []
            for activity in sorted_activities:
                detail = {
                    'time': activity.timestamp.strftime('%H:%M'),
                    'type': activity.type.value,
                    'type_emoji': self._get_activity_emoji(activity.type),
                    'content': activity.content,
                    'participants': [self._make_wikilink(p.name) for p in activity.participants],
                    'tags': [self._format_tag(tag) for tag in activity.tags]
                }
                activity_details.append(detail)
            
            # 参加者の統計
            all_participants = set()
            for activity in activities:
                all_participants.update(p.name for p in activity.participants)
            
            # テンプレートのレンダリング
            content = template.render(
                date=date,
                activity_count=len(activities),
                participant_count=len(all_participants),
                activities=activity_details,
                generated_at=datetime.now()
            )
            
            # ファイルの保存
            filename = date.strftime('%Y-%m-%d') + ".md"
            filepath = self.output_dir / "daily" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.generated_files['daily'].append(str(filepath))
            logger.info(f"デイリーノートを生成しました: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            raise OutputGenerationError(f"デイリーノートの生成に失敗しました: {str(e)}")
    
    def generate_index(self, summary_data: Dict[str, Any]) -> str:
        """インデックスページのMarkdownを生成
        
        Args:
            summary_data: 全体のサマリーデータ
            
        Returns:
            生成されたファイルパス
        """
        try:
            template = self.env.get_template('index.md')
            
            # 生成されたファイルへのリンクを作成
            person_links = [
                self._make_wikilink(Path(f).stem) 
                for f in self.generated_files['persons']
            ]
            
            workflow_links = [
                self._make_wikilink(Path(f).stem) 
                for f in self.generated_files['workflows']
            ]
            
            department_links = [
                self._make_wikilink(Path(f).stem) 
                for f in self.generated_files['departments']
            ]
            
            # 最近のデイリーノートへのリンク
            recent_daily_links = [
                self._make_wikilink(Path(f).stem) 
                for f in sorted(self.generated_files['daily'], reverse=True)[:7]
            ]
            
            # テンプレートのレンダリング
            content = template.render(
                summary=summary_data,
                person_links=person_links,
                workflow_links=workflow_links,
                department_links=department_links,
                recent_daily_links=recent_daily_links,
                generated_at=datetime.now()
            )
            
            # ファイルの保存
            filepath = self.output_dir / "index.md"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.generated_files['index'] = str(filepath)
            logger.info(f"インデックスページを生成しました: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            raise OutputGenerationError(f"インデックスページの生成に失敗しました: {str(e)}")
    
    def _make_wikilink(self, text: str) -> str:
        """Obsidian形式のウィキリンクを作成"""
        return f"[[{text}]]"
    
    def _format_date(self, date: datetime) -> str:
        """日付を日本語形式でフォーマット"""
        return date.strftime('%Y年%m月%d日')
    
    def _format_tag(self, tag: str) -> str:
        """タグをObsidian形式でフォーマット"""
        # 英数字とひらがな、カタカナ、漢字以外を除去
        clean_tag = re.sub(r'[^\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', '', tag)
        return f"#{clean_tag}"
    
    def _get_activity_emoji(self, activity_type: ActivityType) -> str:
        """活動タイプに対応する絵文字を取得"""
        emoji_map = {
            ActivityType.EMAIL: "📧",
            ActivityType.MEETING: "🤝",
            ActivityType.DOCUMENT: "📄",
            ActivityType.CHAT: "💬",
            ActivityType.TASK: "✅",
            ActivityType.OTHER: "📌"
        }
        return emoji_map.get(activity_type, "📌")
    
    def _generate_activity_summary(self, activities: List[Activity]) -> Dict[str, Any]:
        """活動のサマリーを生成"""
        summary = {
            'total_count': len(activities),
            'by_type': {},
            'recent_activities': []
        }
        
        # タイプ別の集計
        for activity in activities:
            activity_type = activity.type.value
            if activity_type not in summary['by_type']:
                summary['by_type'][activity_type] = 0
            summary['by_type'][activity_type] += 1
        
        # 最近の活動（最新5件）
        recent = sorted(activities, key=lambda a: a.timestamp, reverse=True)[:5]
        for activity in recent:
            summary['recent_activities'].append({
                'date': activity.timestamp.strftime('%Y-%m-%d'),
                'type': activity.type.value,
                'content_preview': activity.content[:50] + "..." if len(activity.content) > 50 else activity.content
            })
        
        return summary
    
    def _create_default_templates(self) -> None:
        """デフォルトのテンプレートファイルを作成"""
        templates = {
            'person_profile.md': self._get_person_template(),
            'workflow_document.md': self._get_workflow_template(),
            'department_report.md': self._get_department_template(),
            'daily_note.md': self._get_daily_template(),
            'index.md': self._get_index_template()
        }
        
        for filename, content in templates.items():
            filepath = self.template_dir / filename
            if not filepath.exists():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _get_person_template(self) -> str:
        """人物プロファイルのデフォルトテンプレート"""
        return """---
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
"""
    
    def _get_workflow_template(self) -> str:
        """ワークフロー文書のデフォルトテンプレート"""
        return """---
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
"""
    
    def _get_department_template(self) -> str:
        """部門レポートのデフォルトテンプレート"""
        return """---
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
"""
    
    def _get_daily_template(self) -> str:
        """デイリーノートのデフォルトテンプレート"""
        return """---
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
"""
    
    def _get_index_template(self) -> str:
        """インデックスページのデフォルトテンプレート"""
        return """---
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
"""