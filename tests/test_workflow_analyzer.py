import pytest
from datetime import datetime, timedelta
from scripts.analyzers.workflow_analyzer import WorkflowAnalyzer
from scripts.models import Activity, Person, ActivityType, Workflow, WorkflowStep, Priority


class TestWorkflowAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        """WorkflowAnalyzerのインスタンスを作成"""
        return WorkflowAnalyzer(min_pattern_frequency=2, time_window_hours=4)
    
    @pytest.fixture
    def sample_persons(self):
        """サンプルの人物データを作成"""
        return {
            'yamada': Person(
                id='p001',
                name='山田太郎',
                department='営業部',
                role='課長',
                email='yamada@example.com'
            ),
            'tanaka': Person(
                id='p002',
                name='田中花子',
                department='営業部',
                role='主任',
                email='tanaka@example.com'
            ),
            'suzuki': Person(
                id='p003',
                name='鈴木一郎',
                department='企画部',
                role='担当',
                email='suzuki@example.com'
            )
        }
    
    @pytest.fixture
    def sample_activities(self, sample_persons):
        """サンプルの活動データを作成（パターンを含む）"""
        activities = []
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        # パターン1: メール→文書作成→会議（3回繰り返し）
        for day in [0, 7, 14]:  # 週次パターン
            # メール活動
            email_activity = Activity(
                id=f'a{day}_1',
                type=ActivityType.EMAIL,
                timestamp=base_time + timedelta(days=day, hours=0),
                content="提案書について相談",
                tags=['提案書', '相談']
            )
            email_activity.add_participant(sample_persons['yamada'])
            email_activity.add_participant(sample_persons['tanaka'])
            activities.append(email_activity)
            
            # 文書作成活動
            doc_activity = Activity(
                id=f'a{day}_2',
                type=ActivityType.DOCUMENT,
                timestamp=base_time + timedelta(days=day, hours=2),
                content="提案書作成",
                tags=['提案書', '作成']
            )
            doc_activity.add_participant(sample_persons['yamada'])
            activities.append(doc_activity)
            
            # 会議活動
            meeting_activity = Activity(
                id=f'a{day}_3',
                type=ActivityType.MEETING,
                timestamp=base_time + timedelta(days=day, hours=3),
                content="提案書レビュー会議",
                tags=['提案書', 'レビュー']
            )
            meeting_activity.add_participant(sample_persons['yamada'])
            meeting_activity.add_participant(sample_persons['tanaka'])
            meeting_activity.add_participant(sample_persons['suzuki'])
            activities.append(meeting_activity)
        
        # パターン2: チーム会議（2回）
        for day in [3, 10]:
            team_meeting = Activity(
                id=f'team_{day}',
                type=ActivityType.MEETING,
                timestamp=base_time + timedelta(days=day, hours=15),
                content="定例チーム会議",
                tags=['定例', 'チーム']
            )
            team_meeting.add_participant(sample_persons['yamada'])
            team_meeting.add_participant(sample_persons['tanaka'])
            team_meeting.add_participant(sample_persons['suzuki'])
            activities.append(team_meeting)
        
        return activities
    
    def test_detect_patterns(self, analyzer, sample_activities):
        """パターン検出のテスト"""
        patterns = analyzer.detect_patterns(sample_activities)
        
        assert len(patterns) > 0
        
        # 個人のパターンが検出されているか
        person_patterns = [p for p in patterns if 'person_email' in p]
        assert len(person_patterns) > 0
        
        # チームパターンが検出されているか
        team_patterns = [p for p in patterns if 'participants' in p]
        assert len(team_patterns) > 0
        
        # 頻度が正しく計算されているか
        for pattern in patterns:
            assert pattern['frequency'] >= analyzer.min_pattern_frequency
    
    def test_detect_patterns_empty(self, analyzer):
        """空の活動リストでのパターン検出テスト"""
        patterns = analyzer.detect_patterns([])
        assert patterns == []
    
    def test_build_workflow(self, analyzer, sample_activities):
        """ワークフロー構築のテスト"""
        patterns = analyzer.detect_patterns(sample_activities)
        assert len(patterns) > 0
        
        # 最初のパターンからワークフローを構築
        pattern = patterns[0]
        workflow = analyzer.build_workflow(pattern)
        
        assert isinstance(workflow, Workflow)
        assert workflow.id
        assert workflow.name
        assert workflow.owner
        assert len(workflow.steps) > 0
        assert workflow.frequency in ["日次", "週次", "月次", "不定期"]
        assert workflow.priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
    
    def test_visualize_flow(self, analyzer, sample_activities):
        """フロー可視化のテスト"""
        patterns = analyzer.detect_patterns(sample_activities)
        workflow = analyzer.build_workflow(patterns[0])
        
        mermaid_diagram = analyzer.visualize_flow(workflow)
        
        assert "```mermaid" in mermaid_diagram
        assert "graph LR" in mermaid_diagram
        assert "```" in mermaid_diagram
        
        # ステップが含まれているか
        for step in workflow.steps:
            assert step.name.replace('"', '\\"') in mermaid_diagram
    
    def test_analyze_bottlenecks(self, analyzer):
        """ボトルネック分析のテスト"""
        # テスト用のワークフローを作成
        owner = Person(id='p001', name='山田', department='営業', role='課長', email='yamada@example.com')
        workflow = Workflow(
            id='w001',
            name='テストワークフロー',
            owner=owner,
            frequency='週次'
        )
        
        # ステップを追加（ボトルネックを含む）
        step1 = WorkflowStep(
            id='s001',
            name='データ収集',
            description='データを収集する',
            responsible=owner,
            duration_hours=1.0
        )
        
        step2 = WorkflowStep(
            id='s002',
            name='分析処理',
            description='データを分析する',
            duration_hours=8.0  # 長時間のステップ
        )
        
        step3 = WorkflowStep(
            id='s003',
            name='レポート作成',
            description='レポートを作成する',
            responsible=owner,
            duration_hours=2.0
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        
        # 依存関係を設定
        step2.add_dependency(step1)
        step3.add_dependency(step2)
        
        bottlenecks = analyzer.analyze_bottlenecks([workflow])
        
        assert len(bottlenecks) > 0
        
        # 最も負荷の高いステップ（step2）がボトルネックとして検出されるか
        top_bottleneck = bottlenecks[0]
        assert top_bottleneck['step_id'] == 's002'
        assert top_bottleneck['recommendations']
    
    def test_extract_activity_sequences(self, analyzer, sample_activities):
        """活動シーケンス抽出のテスト"""
        # 山田の活動のみを抽出
        yamada_activities = [a for a in sample_activities if any(p.email == 'yamada@example.com' for p in a.participants)]
        sequences = analyzer._extract_activity_sequences(yamada_activities)
        
        assert len(sequences) > 0
        assert all(isinstance(seq, tuple) for seq in sequences)
        assert all(len(seq) >= 2 for seq in sequences)
    
    def test_find_frequent_sequences(self, analyzer):
        """頻出シーケンス検出のテスト"""
        sequences = [
            ('email_提案書', 'document_提案書', 'meeting_提案書'),
            ('email_提案書', 'document_提案書', 'meeting_提案書'),
            ('email_提案書', 'document_提案書'),
            ('meeting_定例', 'email_報告'),
        ]
        
        frequent = analyzer._find_frequent_sequences(sequences)
        
        assert len(frequent) > 0
        # 完全に一致するシーケンスが頻出として検出される
        assert ('email_提案書', 'document_提案書', 'meeting_提案書') in frequent
        assert frequent[('email_提案書', 'document_提案書', 'meeting_提案書')] >= 2
    
    def test_classify_pattern_type(self, analyzer):
        """パターンタイプ分類のテスト"""
        assert analyzer._classify_pattern_type(('email', 'document')) == "文書作成フロー"
        assert analyzer._classify_pattern_type(('meeting', 'email')) == "会議フロー"
        assert analyzer._classify_pattern_type(('email', 'email')) == "メールコミュニケーションフロー"
        assert analyzer._classify_pattern_type(('document', 'document')) == "文書管理フロー"
        assert analyzer._classify_pattern_type(('other',)) == "一般業務フロー"
    
    def test_estimate_frequency(self, analyzer, sample_activities):
        """頻度推定のテスト"""
        # 週次パターンのテスト
        weekly_pattern = {
            'activities': sample_activities[:3]  # 最初の3つの活動
        }
        
        # 日付を調整して週次パターンを作成
        for i, activity in enumerate(weekly_pattern['activities']):
            activity.timestamp = datetime(2024, 1, 1 + i * 7, 9, 0, 0)
        
        frequency = analyzer._estimate_frequency(weekly_pattern)
        assert frequency == "週次"
    
    def test_generate_workflow_name(self, analyzer):
        """ワークフロー名生成のテスト"""
        # シーケンスパターンの場合
        pattern1 = {
            'type': '文書作成フロー',
            'sequence': ('email', 'document', 'meeting')
        }
        name1 = analyzer._generate_workflow_name(pattern1)
        assert 'email' in name1
        assert 'meeting' in name1
        assert '文書作成フロー' in name1
        
        # チームパターンの場合
        pattern2 = {
            'type': 'チーム協働パターン',
            'participants': ('yamada@example.com', 'tanaka@example.com')
        }
        name2 = analyzer._generate_workflow_name(pattern2)
        assert '2名' in name2
        assert 'チーム協働パターン' in name2
    
    def test_calculate_critical_path(self, analyzer):
        """クリティカルパス計算のテスト"""
        owner = Person(id='p001', name='山田', department='営業', role='課長', email='yamada@example.com')
        workflow = Workflow(id='w001', name='テスト', owner=owner, frequency='日次')
        
        # 並列パスを持つワークフローを作成
        # S1 -> S2 -> S4
        #    -> S3 ->
        steps = [
            WorkflowStep(id='s1', name='開始', description='', duration_hours=1.0),
            WorkflowStep(id='s2', name='処理A', description='', duration_hours=3.0),
            WorkflowStep(id='s3', name='処理B', description='', duration_hours=2.0),
            WorkflowStep(id='s4', name='完了', description='', duration_hours=1.0)
        ]
        
        for step in steps:
            workflow.add_step(step)
        
        steps[1].add_dependency(steps[0])  # S2 depends on S1
        steps[2].add_dependency(steps[0])  # S3 depends on S1
        steps[3].add_dependency(steps[1])  # S4 depends on S2
        steps[3].add_dependency(steps[2])  # S4 depends on S3
        
        critical_path = analyzer._calculate_critical_path(workflow)
        
        # S1 -> S2 -> S4 がクリティカルパス（合計5時間）
        assert 's1' in critical_path
        assert 's2' in critical_path
        assert 's4' in critical_path