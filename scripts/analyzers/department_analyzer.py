import logging
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx
from itertools import combinations

from scripts.models import Person, Activity, ActivityType, Department
from scripts.exceptions import AnalysisError
from scripts.utils import generate_id


logger = logging.getLogger(__name__)


class DepartmentAnalyzer:
    """部門間連携とコミュニケーションフローを分析するクラス"""
    
    def __init__(self, min_interaction_count: int = 3):
        """
        Args:
            min_interaction_count: 有意な連携として認識する最小インタラクション数
        """
        self.min_interaction_count = min_interaction_count
        self.department_graph = nx.DiGraph()
        self.communication_flows = []
        self.cross_functional_activities = []
        
    def analyze_department_interactions(self, activities: List[Activity]) -> Dict[str, Any]:
        """部門間のインタラクションを分析
        
        Args:
            activities: 活動のリスト
            
        Returns:
            部門間インタラクションの分析結果
        """
        try:
            # 部門間のやり取りを集計
            dept_interactions = self._collect_department_interactions(activities)
            
            # コミュニケーションフローを分析
            communication_flows = self._analyze_communication_flows(activities)
            
            # クロスファンクショナルな活動を特定
            cross_functional = self._identify_cross_functional_activities(activities)
            
            # 部門グラフを構築
            self._build_department_graph(dept_interactions)
            
            # 中心性メトリクスを計算
            centrality_metrics = self._calculate_centrality_metrics()
            
            # 情報伝達経路を分析
            information_paths = self._analyze_information_paths()
            
            # ボトルネック部門を特定
            bottleneck_departments = self._identify_bottleneck_departments()
            
            analysis_result = {
                'department_interactions': dept_interactions,
                'communication_flows': communication_flows,
                'cross_functional_activities': cross_functional,
                'centrality_metrics': centrality_metrics,
                'information_paths': information_paths,
                'bottleneck_departments': bottleneck_departments,
                'graph_metrics': self._get_graph_metrics()
            }
            
            logger.info(f"部門間分析完了: {len(dept_interactions)}個の部門ペアを分析")
            return analysis_result
            
        except Exception as e:
            raise AnalysisError(f"部門間分析でエラーが発生しました: {str(e)}")
    
    def visualize_department_network(self) -> str:
        """部門間ネットワークをMermaid形式で可視化
        
        Returns:
            Mermaid形式のダイアグラム
        """
        if not self.department_graph.nodes():
            return "```mermaid\ngraph LR\n    NoData[データなし]\n```"
        
        mermaid_lines = [
            "```mermaid",
            "graph LR"
        ]
        
        # ノードのスタイル定義
        for dept in self.department_graph.nodes():
            node_data = self.department_graph.nodes[dept]
            size = node_data.get('size', 1)
            
            # ノードサイズに基づいてスタイルを設定
            if size > 10:
                style = "style {} fill:#ff9999,stroke:#333,stroke-width:4px".format(dept.replace(' ', '_'))
            elif size > 5:
                style = "style {} fill:#ffcc99,stroke:#333,stroke-width:2px".format(dept.replace(' ', '_'))
            else:
                style = "style {} fill:#ccffcc,stroke:#333,stroke-width:1px".format(dept.replace(' ', '_'))
            
            mermaid_lines.append(f"    {dept.replace(' ', '_')}[\"{dept}\\n({size}名)\"]")
            mermaid_lines.append(f"    {style}")
        
        # エッジの定義
        for source, target, data in self.department_graph.edges(data=True):
            weight = data.get('weight', 1)
            source_id = source.replace(' ', '_')
            target_id = target.replace(' ', '_')
            
            # 重みに基づいて線の太さを調整
            if weight > 10:
                arrow = "-->"
                mermaid_lines.append(f"    {source_id} {arrow}|{weight}| {target_id}")
            elif weight > 5:
                arrow = "-->"
                mermaid_lines.append(f"    {source_id} {arrow}|{weight}| {target_id}")
            else:
                arrow = "-->"
                mermaid_lines.append(f"    {source_id} {arrow} {target_id}")
        
        mermaid_lines.append("```")
        
        return "\n".join(mermaid_lines)
    
    def generate_collaboration_matrix(self) -> Dict[str, Any]:
        """部門間のコラボレーションマトリクスを生成
        
        Returns:
            コラボレーションマトリクスデータ
        """
        if not self.department_graph.nodes():
            return {'matrix': {}, 'departments': []}
        
        departments = sorted(self.department_graph.nodes())
        matrix = {}
        
        for dept1 in departments:
            matrix[dept1] = {}
            for dept2 in departments:
                if dept1 == dept2:
                    # 同じ部門内のインタラクション数
                    matrix[dept1][dept2] = self.department_graph.nodes[dept1].get('internal_interactions', 0)
                else:
                    # 部門間のインタラクション数
                    if self.department_graph.has_edge(dept1, dept2):
                        matrix[dept1][dept2] = self.department_graph[dept1][dept2]['weight']
                    else:
                        matrix[dept1][dept2] = 0
        
        return {
            'matrix': matrix,
            'departments': departments,
            'total_interactions': sum(
                self.department_graph[u][v]['weight'] 
                for u, v in self.department_graph.edges()
            )
        }
    
    def identify_collaboration_patterns(self) -> List[Dict[str, Any]]:
        """部門間のコラボレーションパターンを特定
        
        Returns:
            コラボレーションパターンのリスト
        """
        patterns = []
        
        # ハブ部門を特定（多くの部門と連携）
        hub_departments = self._identify_hub_departments()
        for dept, metrics in hub_departments:
            patterns.append({
                'type': 'ハブ部門',
                'department': dept,
                'description': f"{dept}は{metrics['connected_departments']}個の部門と連携し、中心的な役割を果たしている",
                'metrics': metrics
            })
        
        # 孤立部門を特定
        isolated_departments = self._identify_isolated_departments()
        for dept in isolated_departments:
            patterns.append({
                'type': '孤立部門',
                'department': dept,
                'description': f"{dept}は他部門との連携が少ない",
                'recommendation': '他部門との連携強化を検討'
            })
        
        # 強い連携ペアを特定
        strong_pairs = self._identify_strong_collaboration_pairs()
        for pair, metrics in strong_pairs:
            patterns.append({
                'type': '強連携ペア',
                'departments': pair,
                'description': f"{pair[0]}と{pair[1]}は頻繁に連携している",
                'metrics': metrics
            })
        
        # 三角関係（3部門間の強い連携）を特定
        triangles = self._identify_department_triangles()
        for triangle in triangles:
            patterns.append({
                'type': '三角連携',
                'departments': triangle,
                'description': f"{', '.join(triangle)}の3部門は密接に連携している"
            })
        
        return patterns
    
    def _collect_department_interactions(self, activities: List[Activity]) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """部門間のインタラクションを収集"""
        dept_interactions = defaultdict(lambda: {
            'count': 0,
            'activities': [],
            'participants': set(),
            'activity_types': Counter()
        })
        
        for activity in activities:
            # 活動に参加している部門を特定
            departments = set()
            participant_by_dept = defaultdict(list)
            
            for participant in activity.participants:
                dept = participant.department
                departments.add(dept)
                participant_by_dept[dept].append(participant)
            
            # 部門間のペアを生成
            if len(departments) > 1:
                for dept1, dept2 in combinations(sorted(departments), 2):
                    key = (dept1, dept2)
                    dept_interactions[key]['count'] += 1
                    dept_interactions[key]['activities'].append(activity)
                    dept_interactions[key]['participants'].update(
                        p.email for p in participant_by_dept[dept1]
                    )
                    dept_interactions[key]['participants'].update(
                        p.email for p in participant_by_dept[dept2]
                    )
                    dept_interactions[key]['activity_types'][activity.type] += 1
            
            # 同じ部門内のインタラクションも記録
            for dept, participants in participant_by_dept.items():
                if len(participants) > 1:
                    key = (dept, dept)
                    dept_interactions[key]['count'] += 1
                    dept_interactions[key]['activities'].append(activity)
                    dept_interactions[key]['participants'].update(
                        p.email for p in participants
                    )
                    dept_interactions[key]['activity_types'][activity.type] += 1
        
        # set型をリストに変換
        for key in dept_interactions:
            dept_interactions[key]['participants'] = list(dept_interactions[key]['participants'])
        
        return dict(dept_interactions)
    
    def _analyze_communication_flows(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """コミュニケーションフローを分析"""
        flows = []
        
        # 時系列でソート
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        
        # 部門間のメッセージフローを追跡
        for i in range(len(sorted_activities) - 1):
            curr_activity = sorted_activities[i]
            
            # メールやメッセージング活動を対象
            if curr_activity.type in [ActivityType.EMAIL, ActivityType.MEETING]:
                curr_depts = {p.department for p in curr_activity.participants}
                
                # 次の関連活動を探す
                for j in range(i + 1, min(i + 10, len(sorted_activities))):
                    next_activity = sorted_activities[j]
                    next_depts = {p.department for p in next_activity.participants}
                    
                    # 部門が重複していて、時間的に近い場合
                    time_diff = (next_activity.timestamp - curr_activity.timestamp).total_seconds() / 3600
                    if curr_depts & next_depts and time_diff < 24:  # 24時間以内
                        flow = {
                            'id': generate_id('flow', f"{curr_activity.id}_{next_activity.id}"),
                            'source_activity': curr_activity,
                            'target_activity': next_activity,
                            'source_departments': list(curr_depts),
                            'target_departments': list(next_depts),
                            'common_departments': list(curr_depts & next_depts),
                            'time_difference_hours': round(time_diff, 1),
                            'flow_type': self._classify_flow_type(curr_activity, next_activity)
                        }
                        flows.append(flow)
                        break
        
        self.communication_flows = flows
        return flows
    
    def _identify_cross_functional_activities(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """クロスファンクショナルな活動を特定"""
        cross_functional = []
        
        for activity in activities:
            departments = {p.department for p in activity.participants}
            
            if len(departments) >= 3:  # 3部門以上が参加
                cf_activity = {
                    'activity_id': activity.id,
                    'activity_type': activity.type,
                    'timestamp': activity.timestamp,
                    'departments': list(departments),
                    'participant_count': len(activity.participants),
                    'participants_by_dept': self._group_participants_by_dept(activity.participants),
                    'complexity_score': len(departments) * len(activity.participants),
                    'tags': activity.tags
                }
                cross_functional.append(cf_activity)
        
        self.cross_functional_activities = sorted(
            cross_functional, 
            key=lambda x: x['complexity_score'], 
            reverse=True
        )
        return self.cross_functional_activities
    
    def _build_department_graph(self, dept_interactions: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
        """部門グラフを構築"""
        self.department_graph.clear()
        
        # 部門ごとの人数を集計
        dept_people = defaultdict(set)
        
        for (dept1, dept2), interaction in dept_interactions.items():
            if interaction['count'] >= self.min_interaction_count:
                # 部門内インタラクション
                if dept1 == dept2:
                    if not self.department_graph.has_node(dept1):
                        self.department_graph.add_node(dept1)
                    self.department_graph.nodes[dept1]['internal_interactions'] = interaction['count']
                    dept_people[dept1].update(interaction['participants'])
                else:
                    # 部門間インタラクション
                    self.department_graph.add_edge(
                        dept1, dept2,
                        weight=interaction['count'],
                        activities=len(interaction['activities']),
                        main_activity_type=interaction['activity_types'].most_common(1)[0][0].value
                    )
                    dept_people[dept1].update(interaction['participants'])
                    dept_people[dept2].update(interaction['participants'])
        
        # ノードに部門サイズを追加
        for dept, people in dept_people.items():
            if self.department_graph.has_node(dept):
                self.department_graph.nodes[dept]['size'] = len(people)
    
    def _calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """中心性メトリクスを計算"""
        if not self.department_graph.nodes():
            return {}
        
        metrics = {}
        
        # 次数中心性（どれだけ多くの部門と連携しているか）
        degree_centrality = nx.degree_centrality(self.department_graph)
        
        # 媒介中心性（情報伝達の仲介役としての重要性）
        betweenness_centrality = nx.betweenness_centrality(
            self.department_graph, 
            weight='weight'
        )
        
        # 固有ベクトル中心性（重要な部門との連携度）
        try:
            eigenvector_centrality = nx.eigenvector_centrality(
                self.department_graph,
                weight='weight',
                max_iter=1000
            )
        except:
            eigenvector_centrality = {node: 0.0 for node in self.department_graph.nodes()}
        
        # 各部門のメトリクスをまとめる
        for dept in self.department_graph.nodes():
            metrics[dept] = {
                'degree_centrality': round(degree_centrality.get(dept, 0), 3),
                'betweenness_centrality': round(betweenness_centrality.get(dept, 0), 3),
                'eigenvector_centrality': round(eigenvector_centrality.get(dept, 0), 3),
                'in_degree': self.department_graph.in_degree(dept),
                'out_degree': self.department_graph.out_degree(dept),
                'total_interactions': sum(
                    self.department_graph[dept][neighbor]['weight']
                    for neighbor in self.department_graph.neighbors(dept)
                ) if self.department_graph.out_degree(dept) > 0 else 0
            }
        
        return metrics
    
    def _analyze_information_paths(self) -> List[Dict[str, Any]]:
        """情報伝達経路を分析"""
        paths = []
        
        if len(self.department_graph.nodes()) < 2:
            return paths
        
        # 全部門ペア間の最短経路を計算
        for source in self.department_graph.nodes():
            for target in self.department_graph.nodes():
                if source != target:
                    try:
                        # 最短経路を計算
                        shortest_path = nx.shortest_path(
                            self.department_graph,
                            source,
                            target
                        )
                        
                        if len(shortest_path) > 2:  # 直接連携していない場合
                            # 経路の重みを計算
                            path_weight = 0
                            for i in range(len(shortest_path) - 1):
                                if self.department_graph.has_edge(shortest_path[i], shortest_path[i+1]):
                                    path_weight += self.department_graph[shortest_path[i]][shortest_path[i+1]]['weight']
                            
                            paths.append({
                                'source': source,
                                'target': target,
                                'path': shortest_path,
                                'length': len(shortest_path) - 1,
                                'intermediary_departments': shortest_path[1:-1],
                                'total_weight': path_weight
                            })
                    except nx.NetworkXNoPath:
                        # パスが存在しない場合
                        paths.append({
                            'source': source,
                            'target': target,
                            'path': None,
                            'length': float('inf'),
                            'note': '直接的な情報伝達経路が存在しません'
                        })
        
        # 経路長でソート
        return sorted(paths, key=lambda x: x['length'])
    
    def _identify_bottleneck_departments(self) -> List[Dict[str, Any]]:
        """ボトルネック部門を特定"""
        bottlenecks = []
        centrality_metrics = self._calculate_centrality_metrics()
        
        for dept, metrics in centrality_metrics.items():
            bottleneck_score = 0
            reasons = []
            
            # 高い媒介中心性（多くの情報が通過）
            if metrics['betweenness_centrality'] > 0.3:
                bottleneck_score += 3
                reasons.append('多くの部門間コミュニケーションの仲介役')
            
            # 高い次数中心性だが、リソースが限られている場合
            if metrics['degree_centrality'] > 0.5:
                dept_size = self.department_graph.nodes[dept].get('size', 0)
                if dept_size < 5:
                    bottleneck_score += 2
                    reasons.append('少人数で多くの部門と連携')
            
            # インバウンドが多い（多くの部門から依頼を受ける）
            if metrics['in_degree'] > metrics['out_degree'] * 1.5:
                bottleneck_score += 1
                reasons.append('他部門からの依頼が集中')
            
            if bottleneck_score > 0:
                bottlenecks.append({
                    'department': dept,
                    'bottleneck_score': bottleneck_score,
                    'reasons': reasons,
                    'metrics': metrics,
                    'recommendations': self._generate_bottleneck_recommendations(dept, reasons)
                })
        
        return sorted(bottlenecks, key=lambda x: x['bottleneck_score'], reverse=True)
    
    def _get_graph_metrics(self) -> Dict[str, Any]:
        """グラフ全体のメトリクスを取得"""
        if not self.department_graph.nodes():
            return {
                'node_count': 0,
                'edge_count': 0,
                'density': 0,
                'is_connected': False
            }
        
        return {
            'node_count': self.department_graph.number_of_nodes(),
            'edge_count': self.department_graph.number_of_edges(),
            'density': nx.density(self.department_graph),
            'is_connected': nx.is_weakly_connected(self.department_graph),
            'average_degree': sum(dict(self.department_graph.degree()).values()) / self.department_graph.number_of_nodes(),
            'clustering_coefficient': nx.average_clustering(self.department_graph.to_undirected())
        }
    
    def _classify_flow_type(self, source_activity: Activity, target_activity: Activity) -> str:
        """フローのタイプを分類"""
        source_type = source_activity.type
        target_type = target_activity.type
        
        if source_type == ActivityType.EMAIL and target_type == ActivityType.MEETING:
            return "調整フロー"
        elif source_type == ActivityType.MEETING and target_type == ActivityType.DOCUMENT:
            return "決定事項の文書化"
        elif source_type == ActivityType.DOCUMENT and target_type == ActivityType.EMAIL:
            return "文書の共有"
        elif source_type == target_type:
            return f"{source_type.value}の連鎖"
        else:
            return "一般的なフロー"
    
    def _group_participants_by_dept(self, participants: List[Person]) -> Dict[str, List[str]]:
        """参加者を部門ごとにグループ化"""
        dept_participants = defaultdict(list)
        for participant in participants:
            dept_participants[participant.department].append(participant.name)
        return dict(dept_participants)
    
    def _identify_hub_departments(self) -> List[Tuple[str, Dict[str, Any]]]:
        """ハブ部門を特定"""
        hub_departments = []
        
        for dept in self.department_graph.nodes():
            connected_count = self.department_graph.degree(dept)
            if connected_count >= len(self.department_graph.nodes()) * 0.5:  # 50%以上の部門と連携
                metrics = {
                    'connected_departments': connected_count,
                    'total_interactions': sum(
                        self.department_graph[dept][neighbor]['weight']
                        for neighbor in self.department_graph.neighbors(dept)
                    ) if self.department_graph.out_degree(dept) > 0 else 0,
                    'department_size': self.department_graph.nodes[dept].get('size', 0)
                }
                hub_departments.append((dept, metrics))
        
        return sorted(hub_departments, key=lambda x: x[1]['connected_departments'], reverse=True)
    
    def _identify_isolated_departments(self) -> List[str]:
        """孤立部門を特定"""
        isolated = []
        
        for dept in self.department_graph.nodes():
            if self.department_graph.degree(dept) <= 1:
                isolated.append(dept)
        
        return isolated
    
    def _identify_strong_collaboration_pairs(self) -> List[Tuple[Tuple[str, str], Dict[str, Any]]]:
        """強い連携ペアを特定"""
        strong_pairs = []
        
        for source, target, data in self.department_graph.edges(data=True):
            weight = data['weight']
            if weight >= 10:  # 閾値以上のインタラクション
                metrics = {
                    'interaction_count': weight,
                    'main_activity_type': data.get('main_activity_type', 'unknown')
                }
                strong_pairs.append(((source, target), metrics))
        
        return sorted(strong_pairs, key=lambda x: x[1]['interaction_count'], reverse=True)
    
    def _identify_department_triangles(self) -> List[Tuple[str, str, str]]:
        """部門の三角関係を特定"""
        triangles = []
        
        # 無向グラフに変換して三角形を探す
        undirected_graph = self.department_graph.to_undirected()
        
        for dept1, dept2, dept3 in combinations(undirected_graph.nodes(), 3):
            if (undirected_graph.has_edge(dept1, dept2) and
                undirected_graph.has_edge(dept2, dept3) and
                undirected_graph.has_edge(dept1, dept3)):
                triangles.append(tuple(sorted([dept1, dept2, dept3])))
        
        return list(set(triangles))  # 重複を除去
    
    def _generate_bottleneck_recommendations(self, department: str, reasons: List[str]) -> List[str]:
        """ボトルネック解消の推奨事項を生成"""
        recommendations = []
        
        if '少人数で多くの部門と連携' in reasons:
            recommendations.append(f"{department}の人員増強を検討")
        
        if '多くの部門間コミュニケーションの仲介役' in reasons:
            recommendations.append('直接的なコミュニケーションチャネルの確立')
            recommendations.append('定期的な部門横断会議の設定')
        
        if '他部門からの依頼が集中' in reasons:
            recommendations.append('業務の優先順位付けプロセスの確立')
            recommendations.append('セルフサービス型のリソース提供')
        
        if not recommendations:
            recommendations.append('業務プロセスの見直しと最適化')
        
        return recommendations