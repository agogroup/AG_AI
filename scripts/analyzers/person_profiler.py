import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import networkx as nx
import spacy
from pathlib import Path

from scripts.models import Person, Activity, ActivityType
from scripts.exceptions import ProfileGenerationError
from scripts.utils import sanitize_filename


logger = logging.getLogger(__name__)


class PersonProfiler:
    """人物プロファイリング機能を提供するクラス"""
    
    def __init__(self, nlp_model: str = "ja_core_news_sm"):
        """
        Args:
            nlp_model: spaCyの言語モデル名
        """
        try:
            self.nlp = spacy.load(nlp_model)
        except OSError:
            logger.warning(f"言語モデル {nlp_model} が見つかりません。基本的な分析のみ実行します。")
            self.nlp = None
        
        self.collaboration_network = nx.Graph()
        
    def extract_persons(self, activities: List[Activity]) -> Dict[str, Person]:
        """アクティビティから人物を抽出
        
        Args:
            activities: アクティビティのリスト
            
        Returns:
            メールアドレスをキーとする人物の辞書
        """
        persons = {}
        
        for activity in activities:
            for participant in activity.participants:
                if participant.email not in persons:
                    persons[participant.email] = participant
                    
        logger.info(f"{len(persons)}人の人物を抽出しました")
        return persons
    
    def analyze_activities(self, person: Person) -> Dict[str, any]:
        """人物の活動を分析
        
        Args:
            person: 分析対象の人物
            
        Returns:
            活動分析結果
        """
        if not person.activities:
            return {
                'total_activities': 0,
                'activity_types': {},
                'active_hours': [],
                'active_days': [],
                'keywords': [],
                'main_topics': []
            }
        
        # 活動タイプ別の集計
        activity_types = Counter(activity.type.value for activity in person.activities)
        
        # 活動時間帯の分析
        active_hours = Counter(activity.timestamp.hour for activity in person.activities)
        
        # 活動曜日の分析
        active_days = Counter(activity.timestamp.weekday() for activity in person.activities)
        
        # キーワード抽出
        all_content = " ".join(activity.content for activity in person.activities)
        keywords = self._extract_keywords(all_content)
        
        # 主要トピックの推定
        main_topics = self._identify_topics(person.activities)
        
        # 活動頻度の計算
        if len(person.activities) > 1:
            timestamps = sorted(activity.timestamp for activity in person.activities)
            duration = (timestamps[-1] - timestamps[0]).days + 1
            daily_average = len(person.activities) / duration if duration > 0 else 0
        else:
            daily_average = 0
        
        return {
            'total_activities': len(person.activities),
            'activity_types': dict(activity_types),
            'active_hours': dict(active_hours.most_common(5)),
            'active_days': self._format_weekdays(active_days),
            'keywords': keywords[:10],
            'main_topics': main_topics[:5],
            'daily_average': round(daily_average, 2),
            'first_activity': min(a.timestamp for a in person.activities),
            'last_activity': max(a.timestamp for a in person.activities)
        }
    
    def analyze_collaboration_network(self, persons: Dict[str, Person]) -> nx.Graph:
        """協働ネットワークを分析
        
        Args:
            persons: 人物の辞書
            
        Returns:
            協働ネットワークグラフ
        """
        # ネットワークの構築
        for email, person in persons.items():
            self.collaboration_network.add_node(email, name=person.name, department=person.department)
            
            for collaborator in person.collaborators:
                if collaborator.email in persons:
                    if self.collaboration_network.has_edge(email, collaborator.email):
                        # エッジの重みを増加
                        self.collaboration_network[email][collaborator.email]['weight'] += 1
                    else:
                        self.collaboration_network.add_edge(email, collaborator.email, weight=1)
        
        # ネットワーク指標の計算
        for email in self.collaboration_network.nodes():
            if email in persons:
                person = persons[email]
                
                # 次数中心性（接続数の重要度）
                person.metrics = {
                    'degree_centrality': nx.degree_centrality(self.collaboration_network).get(email, 0),
                    'betweenness_centrality': nx.betweenness_centrality(self.collaboration_network).get(email, 0),
                    'collaboration_count': self.collaboration_network.degree(email),
                    'strongest_collaborations': self._get_strongest_collaborations(email)
                }
        
        return self.collaboration_network
    
    def estimate_expertise(self, person: Person) -> List[str]:
        """専門領域を推定
        
        Args:
            person: 分析対象の人物
            
        Returns:
            推定された専門領域のリスト
        """
        expertise = []
        
        # タグから専門領域を推定
        all_tags = []
        for activity in person.activities:
            all_tags.extend(activity.tags)
        
        tag_counter = Counter(all_tags)
        
        # 頻出タグを専門領域として扱う
        for tag, count in tag_counter.most_common(5):
            if count >= 3:  # 3回以上出現したタグ
                expertise.append(tag)
        
        # 活動内容から専門用語を抽出
        if self.nlp:
            all_content = " ".join(activity.content for activity in person.activities)
            doc = self.nlp(all_content[:1000000])  # 文字数制限
            
            # 固有表現から専門領域を推定
            entities = Counter(ent.text for ent in doc.ents if ent.label_ in ['ORG', 'PRODUCT', 'EVENT'])
            for entity, count in entities.most_common(3):
                if count >= 2 and entity not in expertise:
                    expertise.append(entity)
        
        # スキルリストに追加
        person.skills = expertise
        
        return expertise
    
    def generate_markdown(self, person: Person, activity_analysis: Dict[str, any]) -> str:
        """プロファイルのMarkdown生成
        
        Args:
            person: 人物オブジェクト
            activity_analysis: 活動分析結果
            
        Returns:
            Markdown形式のプロファイル
        """
        try:
            md_lines = [
                f"# {person.name}",
                "",
                "## 基本情報",
                f"- 部門: {person.department}",
                f"- 役職: {person.role}",
                f"- メール: {person.email}",
                "",
                "## 活動サマリー",
                f"- 総活動数: {activity_analysis['total_activities']}件",
                f"- 日平均活動数: {activity_analysis['daily_average']}件",
                f"- 活動期間: {activity_analysis['first_activity'].strftime('%Y-%m-%d')} 〜 {activity_analysis['last_activity'].strftime('%Y-%m-%d')}",
                ""
            ]
            
            # 活動タイプの分布
            if activity_analysis['activity_types']:
                md_lines.extend([
                    "### 活動タイプ",
                    "| タイプ | 件数 |",
                    "|--------|------|"
                ])
                for activity_type, count in sorted(activity_analysis['activity_types'].items(), key=lambda x: x[1], reverse=True):
                    md_lines.append(f"| {activity_type} | {count} |")
                md_lines.append("")
            
            # 活動時間帯
            if activity_analysis['active_hours']:
                md_lines.extend([
                    "### 主な活動時間帯",
                    "```"
                ])
                for hour, count in sorted(activity_analysis['active_hours'].items()):
                    md_lines.append(f"{hour}時: {'█' * min(count, 20)} ({count}件)")
                md_lines.extend(["```", ""])
            
            # 協働者
            if hasattr(person, 'metrics') and person.metrics and person.metrics.get('strongest_collaborations'):
                md_lines.extend([
                    "## 主要協働者",
                    ""
                ])
                for collab_email, weight in person.metrics['strongest_collaborations'][:5]:
                    if collab_email in self.collaboration_network.nodes:
                        collab_name = self.collaboration_network.nodes[collab_email].get('name', collab_email)
                        md_lines.append(f"- [[{collab_name}]] ({weight}回)")
                md_lines.append("")
            
            # 専門領域
            if person.skills:
                md_lines.extend([
                    "## 専門領域・スキル",
                    ""
                ])
                for skill in person.skills:
                    md_lines.append(f"- {skill}")
                md_lines.append("")
            
            # キーワード
            if activity_analysis['keywords']:
                md_lines.extend([
                    "## 頻出キーワード",
                    ""
                ])
                for keyword, count in activity_analysis['keywords']:
                    md_lines.append(f"- {keyword} ({count}回)")
                md_lines.append("")
            
            # ネットワーク指標
            if hasattr(person, 'metrics') and person.metrics:
                md_lines.extend([
                    "## ネットワーク分析",
                    f"- 協働者数: {person.metrics.get('collaboration_count', 0)}人",
                    f"- 次数中心性: {person.metrics.get('degree_centrality', 0):.3f}",
                    f"- 媒介中心性: {person.metrics.get('betweenness_centrality', 0):.3f}",
                    ""
                ])
            
            # タグ
            all_tags = set()
            for activity in person.activities:
                all_tags.update(activity.tags)
            
            if all_tags:
                md_lines.extend([
                    "## タグ",
                    ""
                ])
                for tag in sorted(all_tags)[:10]:
                    md_lines.append(f"#{tag} ")
            
            return "\n".join(md_lines)
            
        except Exception as e:
            raise ProfileGenerationError(f"Markdownの生成に失敗しました: {str(e)}")
    
    def _extract_keywords(self, text: str) -> List[Tuple[str, int]]:
        """テキストからキーワードを抽出"""
        if not text:
            return []
        
        # 簡易的なキーワード抽出（実際の実装ではより高度な手法を使用）
        words = text.split()
        
        # ストップワードの除外（簡易版）
        stopwords = {'の', 'に', 'は', 'を', 'が', 'と', 'で', 'て', 'た', 'し', 'です', 'ます', 'こと', 'これ', 'それ', 'あれ'}
        
        # 2文字以上の単語をカウント
        word_counts = Counter(word for word in words if len(word) >= 2 and word not in stopwords)
        
        return word_counts.most_common(20)
    
    def _identify_topics(self, activities: List[Activity]) -> List[str]:
        """活動からトピックを識別"""
        topics = []
        
        # タグベースのトピック抽出
        all_tags = []
        for activity in activities:
            all_tags.extend(activity.tags)
        
        tag_counter = Counter(all_tags)
        for tag, count in tag_counter.most_common(5):
            if count >= 2:
                topics.append(tag)
        
        return topics
    
    def _format_weekdays(self, weekday_counter: Counter) -> Dict[str, int]:
        """曜日カウンターを読みやすい形式に変換"""
        weekday_names = ['月', '火', '水', '木', '金', '土', '日']
        formatted = {}
        
        for weekday, count in weekday_counter.items():
            if 0 <= weekday <= 6:
                formatted[weekday_names[weekday]] = count
        
        return formatted
    
    def _get_strongest_collaborations(self, email: str) -> List[Tuple[str, int]]:
        """最も強い協働関係を取得"""
        collaborations = []
        
        for neighbor in self.collaboration_network.neighbors(email):
            weight = self.collaboration_network[email][neighbor]['weight']
            collaborations.append((neighbor, weight))
        
        return sorted(collaborations, key=lambda x: x[1], reverse=True)
    
    def save_profile(self, person: Person, profile_markdown: str, output_dir: Path) -> Path:
        """プロファイルをファイルに保存
        
        Args:
            person: 人物オブジェクト
            profile_markdown: Markdown形式のプロファイル
            output_dir: 出力ディレクトリ
            
        Returns:
            保存されたファイルのパス
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名をサニタイズ
        filename = f"{sanitize_filename(person.name)}.md"
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(profile_markdown)
        
        logger.info(f"プロファイルを保存しました: {file_path}")
        return file_path