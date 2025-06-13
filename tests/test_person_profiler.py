import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
import networkx as nx

from scripts.analyzers.person_profiler import PersonProfiler
from scripts.models import Person, Activity, ActivityType


class TestPersonProfiler:
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用の一時ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def profiler(self):
        """PersonProfilerのインスタンスを作成"""
        return PersonProfiler()
    
    @pytest.fixture
    def sample_persons(self):
        """サンプルの人物データを作成"""
        persons = {
            'yamada@example.com': Person(
                id='p001',
                name='山田太郎',
                department='営業部',
                role='課長',
                email='yamada@example.com'
            ),
            'tanaka@example.com': Person(
                id='p002',
                name='田中花子',
                department='営業部',
                role='主任',
                email='tanaka@example.com'
            ),
            'suzuki@example.com': Person(
                id='p003',
                name='鈴木一郎',
                department='開発部',
                role='エンジニア',
                email='suzuki@example.com'
            )
        }
        
        # 協働者の追加
        persons['yamada@example.com'].add_collaborator(persons['tanaka@example.com'])
        persons['yamada@example.com'].add_collaborator(persons['suzuki@example.com'])
        persons['tanaka@example.com'].add_collaborator(persons['yamada@example.com'])
        persons['tanaka@example.com'].add_collaborator(persons['suzuki@example.com'])
        persons['suzuki@example.com'].add_collaborator(persons['yamada@example.com'])
        persons['suzuki@example.com'].add_collaborator(persons['tanaka@example.com'])
        
        return persons
    
    @pytest.fixture
    def sample_activities(self, sample_persons):
        """サンプルの活動データを作成"""
        activities = []
        base_time = datetime(2024, 1, 1, 9, 0, 0)
        
        # 山田の活動
        for i in range(10):
            activity = Activity(
                id=f'a{i:03d}',
                type=ActivityType.EMAIL if i % 2 == 0 else ActivityType.MEETING,
                timestamp=base_time + timedelta(days=i, hours=i % 8),
                content=f"活動内容{i}: 営業活動に関する報告 #営業 #報告",
                tags=['営業', '報告']
            )
            activity.add_participant(sample_persons['yamada@example.com'])
            if i % 3 == 0:
                activity.add_participant(sample_persons['tanaka@example.com'])
                if i % 2 == 0:  # 協働の重みを増やすため
                    activity.add_participant(sample_persons['tanaka@example.com'])
            activities.append(activity)
            sample_persons['yamada@example.com'].add_activity(activity)
            if i % 3 == 0:
                sample_persons['tanaka@example.com'].add_activity(activity)
        
        # 田中の活動
        for i in range(5):
            activity = Activity(
                id=f'a1{i:02d}',
                type=ActivityType.DOCUMENT,
                timestamp=base_time + timedelta(days=i*2, hours=10),
                content=f"提案書作成{i} #提案書 #営業",
                tags=['提案書', '営業']
            )
            activity.add_participant(sample_persons['tanaka@example.com'])
            activities.append(activity)
            sample_persons['tanaka@example.com'].add_activity(activity)
        
        return activities
    
    def test_extract_persons(self, profiler, sample_activities):
        """人物抽出のテスト"""
        persons = profiler.extract_persons(sample_activities)
        
        assert len(persons) == 2  # 山田と田中
        assert 'yamada@example.com' in persons
        assert 'tanaka@example.com' in persons
    
    def test_analyze_activities(self, profiler, sample_persons, sample_activities):
        """活動分析のテスト"""
        # sample_activitiesを呼び出して活動データを作成
        yamada = sample_persons['yamada@example.com']
        analysis = profiler.analyze_activities(yamada)
        
        assert analysis['total_activities'] == 10
        assert 'email' in analysis['activity_types']
        assert 'meeting' in analysis['activity_types']
        assert analysis['activity_types']['email'] == 5
        assert analysis['activity_types']['meeting'] == 5
        assert analysis['daily_average'] > 0
        assert len(analysis['keywords']) > 0
        assert isinstance(analysis['first_activity'], datetime)
        assert isinstance(analysis['last_activity'], datetime)
    
    def test_analyze_activities_empty(self, profiler):
        """活動がない人物の分析テスト"""
        person = Person(
            id='p999',
            name='空太郎',
            department='総務部',
            role='一般',
            email='empty@example.com'
        )
        
        analysis = profiler.analyze_activities(person)
        
        assert analysis['total_activities'] == 0
        assert analysis['activity_types'] == {}
        assert analysis['keywords'] == []
    
    def test_analyze_collaboration_network(self, profiler, sample_persons):
        """協働ネットワーク分析のテスト"""
        network = profiler.analyze_collaboration_network(sample_persons)
        
        assert network.number_of_nodes() == 3
        assert network.number_of_edges() == 3  # 完全グラフ
        
        # ネットワーク指標の確認
        for email, person in sample_persons.items():
            assert hasattr(person, 'metrics')
            assert 'degree_centrality' in person.metrics
            assert 'betweenness_centrality' in person.metrics
            assert 'collaboration_count' in person.metrics
            assert person.metrics['collaboration_count'] == 2  # 各人2人と協働
    
    def test_estimate_expertise(self, profiler, sample_persons, sample_activities):
        """専門領域推定のテスト"""
        # sample_activitiesを呼び出して活動データを作成
        yamada = sample_persons['yamada@example.com']
        expertise = profiler.estimate_expertise(yamada)
        
        assert '営業' in expertise
        assert '報告' in expertise
        assert yamada.skills == expertise
    
    def test_generate_markdown(self, profiler, sample_persons, sample_activities):
        """Markdown生成のテスト"""
        # sample_activitiesを呼び出して活動データを作成
        yamada = sample_persons['yamada@example.com']
        analysis = profiler.analyze_activities(yamada)
        
        # ネットワーク分析を実行してメトリクスを追加
        profiler.analyze_collaboration_network(sample_persons)
        
        markdown = profiler.generate_markdown(yamada, analysis)
        
        assert '# 山田太郎' in markdown
        assert '営業部' in markdown
        assert '課長' in markdown
        assert 'yamada@example.com' in markdown
        assert '総活動数: 10件' in markdown
        assert 'email' in markdown
        assert 'meeting' in markdown
    
    def test_save_profile(self, profiler, sample_persons, sample_activities, temp_dir):
        """プロファイル保存のテスト"""
        # sample_activitiesを呼び出して活動データを作成
        yamada = sample_persons['yamada@example.com']
        analysis = profiler.analyze_activities(yamada)
        markdown = profiler.generate_markdown(yamada, analysis)
        
        file_path = profiler.save_profile(yamada, markdown, temp_dir / 'profiles')
        
        assert file_path.exists()
        assert file_path.name == '山田太郎.md'
        
        # ファイル内容の確認
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert '# 山田太郎' in content
    
    def test_extract_keywords(self, profiler):
        """キーワード抽出のテスト"""
        text = "営業部の山田です。本日の営業報告を送ります。新規顧客との商談が成功しました。営業目標を達成できそうです。"
        keywords = profiler._extract_keywords(text)
        
        assert len(keywords) > 0
        assert any('営業' in kw[0] for kw in keywords)
    
    def test_format_weekdays(self, profiler):
        """曜日フォーマットのテスト"""
        from collections import Counter
        weekday_counter = Counter({0: 5, 1: 3, 2: 4, 3: 2, 4: 6})
        
        formatted = profiler._format_weekdays(weekday_counter)
        
        assert formatted['月'] == 5
        assert formatted['火'] == 3
        assert formatted['水'] == 4
        assert formatted['木'] == 2
        assert formatted['金'] == 6
    
    def test_get_strongest_collaborations(self, profiler, sample_persons):
        """強い協働関係の取得テスト"""
        # ネットワークを構築
        profiler.analyze_collaboration_network(sample_persons)
        
        # 山田の強い協働関係を取得
        collaborations = profiler._get_strongest_collaborations('yamada@example.com')
        
        assert len(collaborations) == 2  # 田中と鈴木
        assert all(isinstance(c[1], int) for c in collaborations)
    
    def test_identify_topics(self, profiler, sample_activities):
        """トピック識別のテスト"""
        topics = profiler._identify_topics(sample_activities[:5])
        
        assert '営業' in topics
        assert '報告' in topics