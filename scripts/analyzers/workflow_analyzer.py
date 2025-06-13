import logging
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx
from itertools import groupby
from operator import attrgetter

from scripts.models import Activity, Workflow, WorkflowStep, Person, ActivityType
from scripts.exceptions import WorkflowAnalysisError
from scripts.utils import generate_id, calculate_similarity


logger = logging.getLogger(__name__)


class WorkflowAnalyzer:
    """業務フロー抽出と分析機能を提供するクラス"""
    
    def __init__(self, min_pattern_frequency: int = 2, time_window_hours: int = 24):
        """
        Args:
            min_pattern_frequency: パターンとして認識する最小出現回数
            time_window_hours: 関連する活動と見なす時間ウィンドウ（時間）
        """
        self.min_pattern_frequency = min_pattern_frequency
        self.time_window = timedelta(hours=time_window_hours)
        self.workflow_graph = nx.DiGraph()
        self.detected_patterns = []
        
    def detect_patterns(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """活動からパターンを検出
        
        Args:
            activities: 活動のリスト
            
        Returns:
            検出されたパターンのリスト
        """
        if not activities:
            return []
        
        # 活動を時系列でソート
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        
        # 人物ごとに活動をグループ化
        person_activities = defaultdict(list)
        for activity in sorted_activities:
            for participant in activity.participants:
                person_activities[participant.email].append(activity)
        
        patterns = []
        
        # 各人物の活動パターンを分析
        for person_email, person_acts in person_activities.items():
            # 活動シーケンスを抽出
            sequences = self._extract_activity_sequences(person_acts)
            
            # 頻出シーケンスを検出
            frequent_sequences = self._find_frequent_sequences(sequences)
            
            for seq, count in frequent_sequences.items():
                if count >= self.min_pattern_frequency:
                    pattern = {
                        'id': generate_id('pattern', f"{person_email}_{seq}"),
                        'person_email': person_email,
                        'sequence': seq,
                        'frequency': count,
                        'activities': self._get_activities_for_sequence(person_acts, seq),
                        'type': self._classify_pattern_type(seq)
                    }
                    patterns.append(pattern)
        
        # チーム間のパターンも検出
        team_patterns = self._detect_team_patterns(sorted_activities)
        patterns.extend(team_patterns)
        
        self.detected_patterns = patterns
        logger.info(f"{len(patterns)}個のパターンを検出しました")
        
        return patterns
    
    def build_workflow(self, pattern: Dict[str, Any]) -> Workflow:
        """パターンからワークフローを構築
        
        Args:
            pattern: 検出されたパターン
            
        Returns:
            構築されたワークフロー
        """
        try:
            # ワークフローの基本情報を設定
            workflow_id = generate_id('workflow', pattern['id'])
            workflow_name = self._generate_workflow_name(pattern)
            
            # オーナーを特定
            if 'person_email' in pattern:
                # 個人のパターンの場合
                owner_email = pattern['person_email']
                activities = pattern.get('activities', [])
                if activities and activities[0].participants:
                    owner = activities[0].participants[0]
                else:
                    # ダミーのオーナーを作成
                    owner = Person(
                        id=generate_id('p', owner_email),
                        name=owner_email.split('@')[0].replace('.', ' ').title(),
                        department="未設定",
                        role="未設定",
                        email=owner_email
                    )
            else:
                # チームパターンの場合、最も頻繁に参加している人物をオーナーに
                participant_counts = Counter()
                participant_map = {}
                
                for activity in pattern.get('activities', []):
                    for participant in activity.participants:
                        participant_counts[participant.email] += 1
                        participant_map[participant.email] = participant
                
                if participant_counts:
                    most_common_email = participant_counts.most_common(1)[0][0]
                    owner = participant_map[most_common_email]
                else:
                    raise WorkflowAnalysisError("ワークフローのオーナーを特定できません")
            
            # ワークフローを作成
            workflow = Workflow(
                id=workflow_id,
                name=workflow_name,
                owner=owner,
                frequency=self._estimate_frequency(pattern),
                priority=self._estimate_priority(pattern)
            )
            
            # ステップを構築
            steps = self._build_workflow_steps(pattern)
            for step in steps:
                workflow.add_step(step)
            
            # 依存関係を設定
            self._set_step_dependencies(workflow.steps)
            
            return workflow
            
        except Exception as e:
            raise WorkflowAnalysisError(f"ワークフローの構築に失敗しました: {str(e)}")
    
    def visualize_flow(self, workflow: Workflow) -> str:
        """ワークフローをMermaid形式で可視化
        
        Args:
            workflow: ワークフローオブジェクト
            
        Returns:
            Mermaid形式のダイアグラム
        """
        mermaid_lines = [
            "```mermaid",
            "graph LR"
        ]
        
        # ノードの定義
        for i, step in enumerate(workflow.steps):
            node_id = f"S{i}"
            label = step.name.replace('"', '\\"')
            if step.responsible:
                label += f"\\n({step.responsible.name})"
            if step.duration_hours:
                label += f"\\n{step.duration_hours}h"
            
            mermaid_lines.append(f'    {node_id}["{label}"]')
        
        # エッジの定義（依存関係）
        for i, step in enumerate(workflow.steps):
            node_id = f"S{i}"
            for dep_step in step.dependencies:
                # 依存ステップのインデックスを見つける
                dep_index = next((j for j, s in enumerate(workflow.steps) if s.id == dep_step.id), None)
                if dep_index is not None:
                    dep_node_id = f"S{dep_index}"
                    mermaid_lines.append(f"    {dep_node_id} --> {node_id}")
        
        # 依存関係がないステップ同士を並列表示
        root_steps = [i for i, step in enumerate(workflow.steps) if not step.dependencies]
        if len(root_steps) > 1:
            for i in range(len(root_steps) - 1):
                mermaid_lines.append(f"    S{root_steps[i]} -.-> S{root_steps[i+1]}")
        
        mermaid_lines.append("```")
        
        return "\n".join(mermaid_lines)
    
    def analyze_bottlenecks(self, workflows: List[Workflow]) -> List[Dict[str, Any]]:
        """ワークフローのボトルネックを分析
        
        Args:
            workflows: ワークフローのリスト
            
        Returns:
            ボトルネック分析結果
        """
        bottlenecks = []
        
        for workflow in workflows:
            # クリティカルパスを計算
            critical_path = self._calculate_critical_path(workflow)
            
            # 各ステップの負荷を分析
            step_loads = self._analyze_step_loads(workflow)
            
            # ボトルネックを特定
            for step in workflow.steps:
                load = step_loads.get(step.id, {})
                
                if self._is_bottleneck(step, load, critical_path):
                    bottleneck = {
                        'workflow_id': workflow.id,
                        'workflow_name': workflow.name,
                        'step_id': step.id,
                        'step_name': step.name,
                        'responsible': step.responsible.name if step.responsible else "未割当",
                        'duration_hours': step.duration_hours or 0,
                        'is_critical': step.id in critical_path,
                        'load_factor': load.get('load_factor', 0),
                        'recommendations': self._generate_recommendations(step, load)
                    }
                    bottlenecks.append(bottleneck)
        
        return sorted(bottlenecks, key=lambda x: x['load_factor'], reverse=True)
    
    def _extract_activity_sequences(self, activities: List[Activity]) -> List[Tuple[str, ...]]:
        """活動からシーケンスを抽出"""
        sequences = []
        
        for i in range(len(activities)):
            # 時間ウィンドウ内の活動をグループ化
            sequence = []
            current_time = activities[i].timestamp
            
            for j in range(i, len(activities)):
                if activities[j].timestamp - current_time <= self.time_window:
                    # 活動タイプとタグを組み合わせて識別子を作成
                    activity_id = f"{activities[j].type.value}"
                    if activities[j].tags:
                        activity_id += f"_{activities[j].tags[0]}"
                    sequence.append(activity_id)
                else:
                    break
            
            if len(sequence) >= 2:  # 2つ以上の活動からなるシーケンスのみ
                sequences.append(tuple(sequence[:5]))  # 最大5つまで
        
        return sequences
    
    def _find_frequent_sequences(self, sequences: List[Tuple[str, ...]]) -> Dict[Tuple[str, ...], int]:
        """頻出シーケンスを検出"""
        sequence_counts = Counter(sequences)
        
        # 部分シーケンスも考慮
        for seq in sequences:
            for length in range(2, len(seq)):
                for i in range(len(seq) - length + 1):
                    subsequence = seq[i:i+length]
                    sequence_counts[subsequence] += 0.5  # 部分シーケンスは重みを下げる
        
        return {seq: count for seq, count in sequence_counts.items() if count >= self.min_pattern_frequency}
    
    def _get_activities_for_sequence(self, activities: List[Activity], sequence: Tuple[str, ...]) -> List[Activity]:
        """シーケンスに対応する活動を取得"""
        matching_activities = []
        
        for i in range(len(activities) - len(sequence) + 1):
            match = True
            for j, seq_item in enumerate(sequence):
                activity = activities[i + j]
                activity_id = f"{activity.type.value}"
                if activity.tags:
                    activity_id += f"_{activity.tags[0]}"
                
                if not activity_id.startswith(seq_item.split('_')[0]):
                    match = False
                    break
            
            if match:
                matching_activities.extend(activities[i:i+len(sequence)])
        
        return matching_activities
    
    def _classify_pattern_type(self, sequence: Tuple[str, ...]) -> str:
        """パターンのタイプを分類"""
        # シーケンスの内容に基づいてパターンタイプを判定
        sequence_str = ' '.join(sequence)
        
        if 'email' in sequence_str and 'document' in sequence_str:
            return "文書作成フロー"
        elif 'meeting' in sequence_str:
            return "会議フロー"
        elif 'email' in sequence_str:
            return "メールコミュニケーションフロー"
        elif 'document' in sequence_str:
            return "文書管理フロー"
        else:
            return "一般業務フロー"
    
    def _detect_team_patterns(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """チーム間のパターンを検出"""
        team_patterns = []
        
        # 複数人が参加する活動のシーケンスを分析
        multi_person_activities = [a for a in activities if len(a.participants) > 1]
        
        if len(multi_person_activities) < self.min_pattern_frequency:
            return team_patterns
        
        # 参加者の組み合わせでグループ化
        participant_groups = defaultdict(list)
        for activity in multi_person_activities:
            participant_key = tuple(sorted(p.email for p in activity.participants))
            participant_groups[participant_key].append(activity)
        
        # 頻出する組み合わせをパターンとして抽出
        for participants, group_activities in participant_groups.items():
            if len(group_activities) >= self.min_pattern_frequency:
                pattern = {
                    'id': generate_id('team_pattern', str(participants)),
                    'participants': participants,
                    'frequency': len(group_activities),
                    'activities': group_activities,
                    'type': 'チーム協働パターン'
                }
                team_patterns.append(pattern)
        
        return team_patterns
    
    def _generate_workflow_name(self, pattern: Dict[str, Any]) -> str:
        """パターンからワークフロー名を生成"""
        pattern_type = pattern.get('type', '業務フロー')
        
        if 'sequence' in pattern:
            # シーケンスの最初と最後の活動タイプから名前を生成
            sequence = pattern['sequence']
            start_activity = sequence[0].split('_')[0]
            end_activity = sequence[-1].split('_')[0]
            
            if start_activity == end_activity:
                return f"{start_activity}処理{pattern_type}"
            else:
                return f"{start_activity}から{end_activity}への{pattern_type}"
        elif 'participants' in pattern:
            # チームパターンの場合
            participant_count = len(pattern['participants'])
            return f"{participant_count}名での{pattern_type}"
        else:
            return pattern_type
    
    def _estimate_frequency(self, pattern: Dict[str, Any]) -> str:
        """パターンの頻度を推定"""
        frequency = pattern.get('frequency', 0)
        activities = pattern.get('activities', [])
        
        if not activities:
            return "不定期"
        
        # 活動の時間間隔を分析
        timestamps = sorted(a.timestamp for a in activities)
        if len(timestamps) < 2:
            return "不定期"
        
        intervals = [(timestamps[i+1] - timestamps[i]).days for i in range(len(timestamps)-1)]
        avg_interval = sum(intervals) / len(intervals)
        
        if avg_interval <= 1:
            return "日次"
        elif avg_interval <= 7:
            return "週次"
        elif avg_interval <= 30:
            return "月次"
        else:
            return "不定期"
    
    def _estimate_priority(self, pattern: Dict[str, Any]) -> str:
        """パターンの優先度を推定"""
        from scripts.models import Priority
        
        frequency = pattern.get('frequency', 0)
        pattern_type = pattern.get('type', '')
        
        # 頻度とタイプに基づいて優先度を決定
        if frequency >= 10 or '重要' in pattern_type or '会議' in pattern_type:
            return Priority.HIGH
        elif frequency >= 5:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _build_workflow_steps(self, pattern: Dict[str, Any]) -> List[WorkflowStep]:
        """パターンからワークフローステップを構築"""
        steps = []
        activities = pattern.get('activities', [])
        
        if 'sequence' in pattern:
            # シーケンスベースのステップ生成
            sequence = pattern['sequence']
            
            # 同じタイプの活動をグループ化
            activity_groups = []
            for activity_type in sequence:
                matching_activities = [a for a in activities if f"{a.type.value}" in activity_type]
                if matching_activities:
                    activity_groups.append((activity_type, matching_activities))
            
            # 各グループからステップを生成
            for i, (activity_type, group_activities) in enumerate(activity_groups):
                step = WorkflowStep(
                    id=generate_id('step', f"{pattern['id']}_{i}"),
                    name=self._generate_step_name(activity_type, group_activities),
                    description=self._generate_step_description(group_activities),
                    responsible=self._determine_step_responsible(group_activities),
                    duration_hours=self._estimate_step_duration(group_activities)
                )
                steps.append(step)
        else:
            # チームパターンの場合は、活動タイプごとにステップを生成
            activity_types = defaultdict(list)
            for activity in activities:
                activity_types[activity.type].append(activity)
            
            for activity_type, type_activities in activity_types.items():
                step = WorkflowStep(
                    id=generate_id('step', f"{pattern['id']}_{activity_type.value}"),
                    name=f"{activity_type.value}活動",
                    description=f"{len(type_activities)}回の{activity_type.value}活動",
                    responsible=self._determine_step_responsible(type_activities),
                    duration_hours=self._estimate_step_duration(type_activities)
                )
                steps.append(step)
        
        return steps
    
    def _generate_step_name(self, activity_type: str, activities: List[Activity]) -> str:
        """ステップ名を生成"""
        base_name = activity_type.replace('_', ' ')
        
        # 活動内容から共通キーワードを抽出
        common_tags = Counter()
        for activity in activities:
            common_tags.update(activity.tags)
        
        if common_tags:
            most_common_tag = common_tags.most_common(1)[0][0]
            return f"{most_common_tag}の{base_name}"
        
        return base_name
    
    def _generate_step_description(self, activities: List[Activity]) -> str:
        """ステップの説明を生成"""
        if not activities:
            return "詳細なし"
        
        # 活動内容のサンプルを含める
        sample_contents = [a.content[:50] for a in activities[:3]]
        description = f"{len(activities)}回の活動を含む。"
        
        if sample_contents:
            description += " 例: " + "; ".join(sample_contents)
        
        return description
    
    def _determine_step_responsible(self, activities: List[Activity]) -> Optional[Person]:
        """ステップの責任者を決定"""
        if not activities:
            return None
        
        # 最も頻繁に参加している人物を責任者とする
        participant_counts = Counter()
        participant_map = {}  # emailからPersonへのマッピング
        
        for activity in activities:
            for participant in activity.participants:
                participant_counts[participant.email] += 1
                participant_map[participant.email] = participant
        
        if participant_counts:
            most_common_email = participant_counts.most_common(1)[0][0]
            return participant_map[most_common_email]
        
        return None
    
    def _estimate_step_duration(self, activities: List[Activity]) -> float:
        """ステップの所要時間を推定（時間単位）"""
        if len(activities) < 2:
            return 1.0  # デフォルト1時間
        
        # 連続する活動間の時間差の平均を計算
        durations = []
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        
        for i in range(len(sorted_activities) - 1):
            duration = (sorted_activities[i+1].timestamp - sorted_activities[i].timestamp).total_seconds() / 3600
            if 0 < duration < 24:  # 24時間以内の場合のみ考慮
                durations.append(duration)
        
        if durations:
            return round(sum(durations) / len(durations), 1)
        
        return 1.0
    
    def _set_step_dependencies(self, steps: List[WorkflowStep]) -> None:
        """ステップ間の依存関係を設定"""
        # 簡単な実装：前のステップに依存
        for i in range(1, len(steps)):
            steps[i].add_dependency(steps[i-1])
    
    def _calculate_critical_path(self, workflow: Workflow) -> Set[str]:
        """ワークフローのクリティカルパスを計算"""
        # グラフを構築
        G = nx.DiGraph()
        
        for step in workflow.steps:
            G.add_node(step.id, duration=step.duration_hours or 0)
            for dep in step.dependencies:
                G.add_edge(dep.id, step.id)
        
        # トポロジカルソートして最長パスを計算
        if not G.nodes():
            return set()
        
        try:
            # 開始ノードを特定（依存関係がないノード）
            start_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            
            # 各ノードへの最長パスを計算
            longest_paths = {}
            for node in nx.topological_sort(G):
                if node in start_nodes:
                    longest_paths[node] = G.nodes[node]['duration']
                else:
                    max_pred_path = max(longest_paths[pred] for pred in G.predecessors(node))
                    longest_paths[node] = max_pred_path + G.nodes[node]['duration']
            
            # クリティカルパスを逆算
            critical_path = set()
            if longest_paths:
                max_duration = max(longest_paths.values())
                end_nodes = [n for n, d in longest_paths.items() if d == max_duration]
                
                # 終了ノードから逆向きにたどる
                to_visit = end_nodes.copy()
                while to_visit:
                    node = to_visit.pop()
                    critical_path.add(node)
                    for pred in G.predecessors(node):
                        if longest_paths[pred] + G.nodes[node]['duration'] == longest_paths[node]:
                            to_visit.append(pred)
            
            return critical_path
            
        except nx.NetworkXError:
            logger.warning("クリティカルパスの計算に失敗しました")
            return set()
    
    def _analyze_step_loads(self, workflow: Workflow) -> Dict[str, Dict[str, Any]]:
        """各ステップの負荷を分析"""
        step_loads = {}
        
        for step in workflow.steps:
            load = {
                'duration': step.duration_hours or 0,
                'dependency_count': len(step.dependencies),
                'is_assigned': step.responsible is not None
            }
            
            # 負荷係数を計算（時間 × 依存関係数）
            load['load_factor'] = load['duration'] * (load['dependency_count'] + 1)
            
            step_loads[step.id] = load
        
        return step_loads
    
    def _is_bottleneck(self, step: WorkflowStep, load: Dict[str, Any], critical_path: Set[str]) -> bool:
        """ステップがボトルネックかどうかを判定"""
        # クリティカルパス上にあり、負荷が高い場合
        if step.id in critical_path and load.get('load_factor', 0) > 5:
            return True
        
        # 担当者が未割当で、所要時間が長い場合
        if not step.responsible and (step.duration_hours or 0) > 2:
            return True
        
        # 多くの依存関係を持つ場合
        if load.get('dependency_count', 0) > 3:
            return True
        
        return False
    
    def _generate_recommendations(self, step: WorkflowStep, load: Dict[str, Any]) -> List[str]:
        """ボトルネック解消の推奨事項を生成"""
        recommendations = []
        
        if not step.responsible:
            recommendations.append("担当者を割り当ててください")
        
        if (step.duration_hours or 0) > 4:
            recommendations.append("タスクを分割することを検討してください")
        
        if load.get('dependency_count', 0) > 2:
            recommendations.append("並列処理可能なタスクがないか確認してください")
        
        if not recommendations:
            recommendations.append("プロセスの自動化を検討してください")
        
        return recommendations