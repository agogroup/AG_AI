import pytest
from datetime import datetime, timedelta
from scripts.analyzers.department_analyzer import DepartmentAnalyzer
from scripts.models import Activity, Person, ActivityType
from scripts.exceptions import AnalysisError


class TestDepartmentAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        """DepartmentAnalyzerのインスタンスを作成"""
        return DepartmentAnalyzer(min_interaction_count=2)
    
    @pytest.fixture
    def sample_persons(self):
        """複数部門のサンプル人物データを作成"""
        return {
            'sales1': Person(
                id='p001',
                name='山田太郎',
                department='営業部',
                role='課長',
                email='yamada@example.com'
            ),
            'sales2': Person(
                id='p002',
                name='田中花子',
                department='営業部',
                role='主任',
                email='tanaka@example.com'
            ),
            'planning1': Person(
                id='p003',
                name='鈴木一郎',
                department='企画部',
                role='課長',
                email='suzuki@example.com'
            ),
            'planning2': Person(
                id='p004',
                name='佐藤次郎',
                department='企画部',
                role='担当',
                email='sato@example.com'
            ),
            'dev1': Person(
                id='p005',
                name='高橋三郎',
                department='開発部',
                role='主任',
                email='takahashi@example.com'
            ),
            'hr1': Person(
                id='p006',
                name='伊藤四郎',
                department='人事部',
                role='担当',
                email='ito@example.com'
            ),
            'finance1': Person(
                id='p007',
                name='渡辺五郎',
                department='経理部',
                role='課長',
                email='watanabe@example.com'
            )
        }
    
    @pytest.fixture
    def department_activities(self, sample_persons):
        """部門間インタラクションを含む活動データを作成"""
        activities = []
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        # 営業部と企画部の頻繁なやり取り（5回）
        for i in range(5):
            activity = Activity(
                id=f'sales_planning_{i}',
                type=ActivityType.MEETING,
                timestamp=base_time + timedelta(days=i*2),
                content=f'営業企画会議 {i+1}',
                tags=['営業企画', '定例']
            )
            activity.add_participant(sample_persons['sales1'])
            activity.add_participant(sample_persons['planning1'])
            activities.append(activity)
        
        # 営業部と開発部のやり取り（3回）
        for i in range(3):
            activity = Activity(
                id=f'sales_dev_{i}',
                type=ActivityType.EMAIL,
                timestamp=base_time + timedelta(days=i*3, hours=2),
                content=f'製品仕様確認 {i+1}',
                tags=['製品', '仕様']
            )
            activity.add_participant(sample_persons['sales2'])
            activity.add_participant(sample_persons['dev1'])
            activities.append(activity)
        
        # 3部門合同会議（企画・開発・営業）（2回）
        for i in range(2):
            activity = Activity(
                id=f'three_dept_{i}',
                type=ActivityType.MEETING,
                timestamp=base_time + timedelta(days=i*7, hours=15),
                content=f'製品開発会議 {i+1}',
                tags=['製品開発', 'クロスファンクショナル']
            )
            activity.add_participant(sample_persons['sales1'])
            activity.add_participant(sample_persons['planning1'])
            activity.add_participant(sample_persons['dev1'])
            activities.append(activity)
        
        # 全部門会議（1回）
        all_dept_meeting = Activity(
            id='all_dept_1',
            type=ActivityType.MEETING,
            timestamp=base_time + timedelta(days=30),
            content='全社会議',
            tags=['全社', '経営']
        )
        for person in sample_persons.values():
            all_dept_meeting.add_participant(person)
        activities.append(all_dept_meeting)
        
        # 営業部内の活動（2回）
        for i in range(2):
            activity = Activity(
                id=f'sales_internal_{i}',
                type=ActivityType.MEETING,
                timestamp=base_time + timedelta(days=i*5, hours=10),
                content=f'営業部定例会 {i+1}',
                tags=['部内', '定例']
            )
            activity.add_participant(sample_persons['sales1'])
            activity.add_participant(sample_persons['sales2'])
            activities.append(activity)
        
        # 孤立した人事部の活動（1回だけ）
        hr_activity = Activity(
            id='hr_isolated',
            type=ActivityType.DOCUMENT,
            timestamp=base_time + timedelta(days=10),
            content='人事評価資料',
            tags=['人事', '評価']
        )
        hr_activity.add_participant(sample_persons['hr1'])
        activities.append(hr_activity)
        
        return activities
    
    def test_analyze_department_interactions(self, analyzer, department_activities):
        """部門間インタラクション分析のテスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        
        assert 'department_interactions' in result
        assert 'communication_flows' in result
        assert 'cross_functional_activities' in result
        assert 'centrality_metrics' in result
        assert 'information_paths' in result
        assert 'bottleneck_departments' in result
        assert 'graph_metrics' in result
        
        # 部門間インタラクションが検出されているか
        interactions = result['department_interactions']
        assert len(interactions) > 0
        
        # 営業部と企画部の強い連携が検出されているか
        # 双方向のキーをチェック
        sales_planning_key1 = ('営業部', '企画部')
        sales_planning_key2 = ('企画部', '営業部')
        
        assert sales_planning_key1 in interactions or sales_planning_key2 in interactions
        
        if sales_planning_key1 in interactions:
            assert interactions[sales_planning_key1]['count'] >= 5
        else:
            assert interactions[sales_planning_key2]['count'] >= 5
    
    def test_analyze_department_interactions_empty(self, analyzer):
        """空の活動リストでの分析テスト"""
        result = analyzer.analyze_department_interactions([])
        
        assert result['department_interactions'] == {}
        assert result['communication_flows'] == []
        assert result['cross_functional_activities'] == []
    
    def test_visualize_department_network(self, analyzer, department_activities):
        """部門ネットワーク可視化のテスト"""
        analyzer.analyze_department_interactions(department_activities)
        mermaid_diagram = analyzer.visualize_department_network()
        
        assert "```mermaid" in mermaid_diagram
        assert "graph LR" in mermaid_diagram
        assert "営業部" in mermaid_diagram
        assert "企画部" in mermaid_diagram
        assert "開発部" in mermaid_diagram
    
    def test_visualize_department_network_empty(self, analyzer):
        """データなしでの可視化テスト"""
        mermaid_diagram = analyzer.visualize_department_network()
        
        assert "```mermaid" in mermaid_diagram
        assert "NoData[データなし]" in mermaid_diagram
    
    def test_generate_collaboration_matrix(self, analyzer, department_activities):
        """コラボレーションマトリクス生成のテスト"""
        analyzer.analyze_department_interactions(department_activities)
        matrix_data = analyzer.generate_collaboration_matrix()
        
        assert 'matrix' in matrix_data
        assert 'departments' in matrix_data
        assert 'total_interactions' in matrix_data
        
        matrix = matrix_data['matrix']
        assert '営業部' in matrix
        
        # 少なくとも何らかのインタラクションが記録されているか
        total_interactions = 0
        for dept1 in matrix:
            for dept2 in matrix[dept1]:
                total_interactions += matrix[dept1][dept2]
        
        assert total_interactions > 0, "マトリクスに全くインタラクションが記録されていません"
        
        # 全体のインタラクション数も確認
        assert matrix_data['total_interactions'] > 0
    
    def test_identify_collaboration_patterns(self, analyzer, department_activities):
        """コラボレーションパターン特定のテスト"""
        analyzer.analyze_department_interactions(department_activities)
        patterns = analyzer.identify_collaboration_patterns()
        
        assert len(patterns) > 0
        
        # パターンタイプの確認
        pattern_types = [p['type'] for p in patterns]
        assert any(t in pattern_types for t in ['ハブ部門', '孤立部門', '強連携ペア', '三角連携'])
        
        # 人事部が孤立部門として検出されるか
        # 人事部は他の活動が全社会議のみなので、度数1以下の場合に孤立部門となる
        isolated_patterns = [p for p in patterns if p['type'] == '孤立部門']
        isolated_depts = [p['department'] for p in isolated_patterns]
        
        # 人事部のインタラクションを確認
        graph_metrics = analyzer._get_graph_metrics()
        if graph_metrics['node_count'] > 0:
            # 人事部がグラフに含まれていて、孤立している場合
            if analyzer.department_graph.has_node('人事部'):
                hr_degree = analyzer.department_graph.degree('人事部')
                if hr_degree <= 1:
                    assert '人事部' in isolated_depts
    
    def test_communication_flows(self, analyzer, department_activities):
        """コミュニケーションフロー分析のテスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        flows = result['communication_flows']
        
        # フローが検出されているか
        assert isinstance(flows, list)
        
        if flows:  # フローが存在する場合
            flow = flows[0]
            assert 'source_activity' in flow
            assert 'target_activity' in flow
            assert 'time_difference_hours' in flow
            assert 'flow_type' in flow
    
    def test_cross_functional_activities(self, analyzer, department_activities):
        """クロスファンクショナル活動の特定テスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        cross_functional = result['cross_functional_activities']
        
        assert len(cross_functional) > 0
        
        # 全部門会議が最も複雑な活動として検出されるか
        top_activity = cross_functional[0]
        assert len(top_activity['departments']) >= 3
        assert top_activity['complexity_score'] > 0
    
    def test_centrality_metrics(self, analyzer, department_activities):
        """中心性メトリクス計算のテスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        centrality = result['centrality_metrics']
        
        assert '営業部' in centrality
        assert '企画部' in centrality
        
        # メトリクスの存在確認
        sales_metrics = centrality['営業部']
        assert 'degree_centrality' in sales_metrics
        assert 'betweenness_centrality' in sales_metrics
        assert 'eigenvector_centrality' in sales_metrics
        assert 'total_interactions' in sales_metrics
    
    def test_information_paths(self, analyzer, department_activities):
        """情報伝達経路分析のテスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        paths = result['information_paths']
        
        assert isinstance(paths, list)
        
        # 直接連携していない部門間のパスが検出されるか
        if paths:
            # パスは長さでソートされているはず
            assert all(
                paths[i]['length'] <= paths[i+1]['length'] 
                for i in range(len(paths)-1)
                if paths[i]['length'] != float('inf') and paths[i+1]['length'] != float('inf')
            )
    
    def test_bottleneck_departments(self, analyzer, department_activities):
        """ボトルネック部門特定のテスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        bottlenecks = result['bottleneck_departments']
        
        assert isinstance(bottlenecks, list)
        
        if bottlenecks:
            bottleneck = bottlenecks[0]
            assert 'department' in bottleneck
            assert 'bottleneck_score' in bottleneck
            assert 'reasons' in bottleneck
            assert 'recommendations' in bottleneck
            assert len(bottleneck['recommendations']) > 0
    
    def test_graph_metrics(self, analyzer, department_activities):
        """グラフメトリクスのテスト"""
        result = analyzer.analyze_department_interactions(department_activities)
        graph_metrics = result['graph_metrics']
        
        assert graph_metrics['node_count'] > 0
        assert graph_metrics['edge_count'] > 0
        assert 0 <= graph_metrics['density'] <= 1
        assert 'is_connected' in graph_metrics
        assert graph_metrics['average_degree'] > 0
    
    def test_error_handling(self, analyzer):
        """エラーハンドリングのテスト"""
        # 不正な入力でエラーが発生するか
        with pytest.raises(AnalysisError):
            # Noneを渡してエラーを誘発
            analyzer.analyze_department_interactions(None)