import pytest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil
from scripts.generators.obsidian_generator import ObsidianGenerator
from scripts.models import Person, Activity, Workflow, WorkflowStep, ActivityType, Priority
from scripts.exceptions import OutputGenerationError


class TestObsidianGenerator:
    
    @pytest.fixture
    def temp_output_dir(self):
        """テスト用の一時出力ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # クリーンアップ
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def generator(self, temp_output_dir):
        """ObsidianGeneratorのインスタンスを作成"""
        return ObsidianGenerator(output_dir=temp_output_dir)
    
    @pytest.fixture
    def sample_person(self):
        """サンプルの人物データを作成"""
        person = Person(
            id='p001',
            name='山田太郎',
            department='営業部',
            role='課長',
            email='yamada@example.com',
            skills=['営業', 'プレゼンテーション', '交渉']
        )
        
        # コラボレーターを追加
        collaborator = Person(
            id='p002',
            name='田中花子',
            department='企画部',
            role='主任',
            email='tanaka@example.com'
        )
        person.add_collaborator(collaborator)
        
        # 活動を追加
        activity = Activity(
            id='a001',
            type=ActivityType.MEETING,
            timestamp=datetime.now(),
            content='営業戦略会議',
            tags=['営業', '戦略']
        )
        activity.add_participant(person)
        person.add_activity(activity)
        
        return person
    
    @pytest.fixture
    def sample_workflow(self, sample_person):
        """サンプルのワークフローデータを作成"""
        workflow = Workflow(
            id='w001',
            name='提案書作成プロセス',
            owner=sample_person,
            frequency='週次',
            priority=Priority.HIGH
        )
        
        # ステップを追加
        step1 = WorkflowStep(
            id='s001',
            name='要件ヒアリング',
            description='顧客の要件をヒアリング',
            responsible=sample_person,
            duration_hours=2.0
        )
        
        step2 = WorkflowStep(
            id='s002',
            name='提案書作成',
            description='ヒアリング内容を基に提案書を作成',
            responsible=sample_person,
            duration_hours=4.0
        )
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        step2.add_dependency(step1)
        
        return workflow
    
    @pytest.fixture
    def sample_activities(self, sample_person):
        """サンプルの活動データを作成"""
        activities = []
        base_time = datetime(2024, 1, 15, 9, 0, 0)
        
        for i in range(3):
            activity = Activity(
                id=f'a{i}',
                type=ActivityType.EMAIL if i % 2 == 0 else ActivityType.MEETING,
                timestamp=base_time + timedelta(hours=i),
                content=f'活動{i+1}の内容',
                tags=[f'タグ{i+1}']
            )
            activity.add_participant(sample_person)
            activities.append(activity)
        
        return activities
    
    def test_generator_initialization(self, generator, temp_output_dir):
        """ジェネレーターの初期化テスト"""
        # 出力ディレクトリの構造を確認
        assert (Path(temp_output_dir) / "persons").exists()
        assert (Path(temp_output_dir) / "workflows").exists()
        assert (Path(temp_output_dir) / "departments").exists()
        assert (Path(temp_output_dir) / "daily").exists()
        
        # テンプレートディレクトリの確認
        template_dir = generator.template_dir
        assert template_dir.exists()
        assert (template_dir / "person_profile.md").exists()
        assert (template_dir / "workflow_document.md").exists()
        assert (template_dir / "department_report.md").exists()
        assert (template_dir / "daily_note.md").exists()
        assert (template_dir / "index.md").exists()
    
    def test_generate_person_profile(self, generator, sample_person):
        """人物プロファイル生成のテスト"""
        profile_data = {
            'activity_analysis': {
                'summary': '営業活動が中心'
            },
            'expertise_summary': '営業のエキスパート',
            'network_analysis': 'ハブとして機能'
        }
        
        filepath = generator.generate_person_profile(sample_person, profile_data)
        
        # ファイルが生成されたか確認
        assert Path(filepath).exists()
        assert "山田太郎.md" in filepath
        
        # 内容を確認
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "山田太郎" in content
        assert "営業部" in content
        assert "[[田中花子]]" in content  # コラボレーターのウィキリンク
        assert "#営業" in content  # スキルタグ
        assert "営業活動が中心" in content
    
    def test_generate_workflow_document(self, generator, sample_workflow):
        """ワークフロー文書生成のテスト"""
        analysis_data = {
            'visualization': '```mermaid\ngraph LR\n    S0["要件ヒアリング"]\n    S1["提案書作成"]\n    S0 --> S1\n```',
            'bottlenecks': '特になし',
            'recommendations': '効率化の余地あり'
        }
        
        filepath = generator.generate_workflow_document(sample_workflow, analysis_data)
        
        # ファイルが生成されたか確認
        assert Path(filepath).exists()
        assert "提案書作成プロセス.md" in filepath
        
        # 内容を確認
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "提案書作成プロセス" in content
        assert "[[山田太郎]]" in content  # オーナーのウィキリンク
        assert "週次" in content
        assert "mermaid" in content
        assert "要件ヒアリング" in content
    
    def test_generate_department_report(self, generator):
        """部門レポート生成のテスト"""
        department_data = {
            'members': ['山田太郎', '田中花子'],
            'partner_departments': ['企画部', '開発部'],
            'network_visualization': '```mermaid\ngraph LR\n    営業部 --> 企画部\n```',
            'metrics': {
                'centrality': 0.8,
                'connected_departments': 3,
                'total_interactions': 50
            },
            'patterns': [
                {'type': 'ハブ部門', 'description': '中心的な役割'}
            ]
        }
        
        filepath = generator.generate_department_report('営業部', department_data)
        
        # ファイルが生成されたか確認
        assert Path(filepath).exists()
        assert "営業部.md" in filepath
        
        # 内容を確認
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "営業部" in content
        assert "[[山田太郎]]" in content
        assert "[[企画部]]" in content
        assert "mermaid" in content
        assert "ハブ部門" in content
    
    def test_generate_daily_note(self, generator, sample_activities):
        """デイリーノート生成のテスト"""
        date = datetime(2024, 1, 15)
        
        filepath = generator.generate_daily_note(date, sample_activities)
        
        # ファイルが生成されたか確認
        assert Path(filepath).exists()
        assert "2024-01-15.md" in filepath
        
        # 内容を確認
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "2024年01月15日" in content
        assert "活動数**: 3" in content  # ボールド付き
        assert "[[山田太郎]]" in content
        assert "#タグ1" in content
    
    def test_generate_index(self, generator, sample_person, sample_workflow):
        """インデックスページ生成のテスト"""
        # 先に他のファイルを生成
        generator.generate_person_profile(sample_person, {})
        generator.generate_workflow_document(sample_workflow, {'visualization': ''})
        
        summary_data = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'total_persons': 10,
            'total_activities': 100,
            'total_workflows': 5
        }
        
        filepath = generator.generate_index(summary_data)
        
        # ファイルが生成されたか確認
        assert Path(filepath).exists()
        assert "index.md" in filepath
        
        # 内容を確認
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "AGO Group プロファイリングシステム" in content
        assert "[[山田太郎]]" in content
        assert "[[提案書作成プロセス]]" in content
        assert "総人数**: 10" in content  # ボールド付き
    
    def test_make_wikilink(self, generator):
        """ウィキリンク作成のテスト"""
        assert generator._make_wikilink("テスト") == "[[テスト]]"
        assert generator._make_wikilink("山田 太郎") == "[[山田 太郎]]"
    
    def test_format_date(self, generator):
        """日付フォーマットのテスト"""
        date = datetime(2024, 1, 15)
        assert generator._format_date(date) == "2024年01月15日"
    
    def test_format_tag(self, generator):
        """タグフォーマットのテスト"""
        assert generator._format_tag("営業") == "#営業"
        assert generator._format_tag("プロジェクト管理") == "#プロジェクト管理"
        assert generator._format_tag("test@123") == "#test123"  # 特殊文字除去
    
    def test_get_activity_emoji(self, generator):
        """活動絵文字取得のテスト"""
        assert generator._get_activity_emoji(ActivityType.EMAIL) == "📧"
        assert generator._get_activity_emoji(ActivityType.MEETING) == "🤝"
        assert generator._get_activity_emoji(ActivityType.DOCUMENT) == "📄"
        assert generator._get_activity_emoji(ActivityType.CHAT) == "💬"
        assert generator._get_activity_emoji(ActivityType.TASK) == "✅"
        assert generator._get_activity_emoji(ActivityType.OTHER) == "📌"
    
    def test_generate_activity_summary(self, generator, sample_activities):
        """活動サマリー生成のテスト"""
        summary = generator._generate_activity_summary(sample_activities)
        
        assert summary['total_count'] == 3
        assert 'email' in summary['by_type']
        assert 'meeting' in summary['by_type']
        assert len(summary['recent_activities']) == 3
        assert summary['recent_activities'][0]['date'] == '2024-01-15'
    
    def test_error_handling(self, generator):
        """エラーハンドリングのテスト"""
        # 無効な人物データで例外が発生するか
        with pytest.raises(OutputGenerationError):
            generator.generate_person_profile(None, {})
        
        # 無効なワークフローデータで例外が発生するか
        with pytest.raises(OutputGenerationError):
            generator.generate_workflow_document(None, {})