import pytest
from datetime import datetime
from scripts.models import Person, Activity, Document, WorkflowStep, Workflow, Priority, ActivityType


class TestPerson:
    def test_person_creation(self):
        person = Person(
            id="p001",
            name="山田太郎",
            department="営業部",
            role="課長",
            email="yamada@example.com"
        )
        assert person.id == "p001"
        assert person.name == "山田太郎"
        assert person.department == "営業部"
        assert person.role == "課長"
        assert person.email == "yamada@example.com"
        assert len(person.activities) == 0
        assert len(person.collaborators) == 0
    
    def test_email_validation(self):
        with pytest.raises(ValueError, match="有効なメールアドレス"):
            Person(
                id="p002",
                name="テスト",
                department="部門",
                role="役職",
                email="invalid_email"
            )
    
    def test_email_lowercase(self):
        person = Person(
            id="p003",
            name="テスト",
            department="部門",
            role="役職",
            email="Test@EXAMPLE.com"
        )
        assert person.email == "test@example.com"
    
    def test_add_collaborator(self):
        person1 = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        person2 = Person(id="p002", name="田中", department="営業", role="部長", email="tanaka@example.com")
        
        person1.add_collaborator(person2)
        assert len(person1.collaborators) == 1
        assert person2 in person1.collaborators
        
        # 重複追加のテスト
        person1.add_collaborator(person2)
        assert len(person1.collaborators) == 1
        
        # 自分自身を追加しようとした場合
        person1.add_collaborator(person1)
        assert len(person1.collaborators) == 1
    
    def test_activity_count(self):
        person = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        
        activity1 = Activity(id="a001", type=ActivityType.EMAIL, timestamp=datetime.now(), content="メール送信")
        activity2 = Activity(id="a002", type=ActivityType.MEETING, timestamp=datetime.now(), content="会議参加")
        activity3 = Activity(id="a003", type=ActivityType.EMAIL, timestamp=datetime.now(), content="メール返信")
        
        person.add_activity(activity1)
        person.add_activity(activity2)
        person.add_activity(activity3)
        
        assert person.get_activity_count() == 3
        assert person.get_activity_count(ActivityType.EMAIL) == 2
        assert person.get_activity_count(ActivityType.MEETING) == 1
        assert person.get_activity_count(ActivityType.DOCUMENT) == 0


class TestActivity:
    def test_activity_creation(self):
        activity = Activity(
            id="a001",
            type=ActivityType.EMAIL,
            timestamp=datetime.now(),
            content="重要な会議の招集メール"
        )
        assert activity.id == "a001"
        assert activity.type == ActivityType.EMAIL
        assert activity.content == "重要な会議の招集メール"
        assert len(activity.participants) == 0
        assert len(activity.tags) == 0
    
    def test_add_participant(self):
        activity = Activity(id="a001", type=ActivityType.MEETING, timestamp=datetime.now(), content="定例会議")
        person1 = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        person2 = Person(id="p002", name="田中", department="営業", role="部長", email="tanaka@example.com")
        
        activity.add_participant(person1)
        activity.add_participant(person2)
        assert len(activity.participants) == 2
        
        # 重複追加のテスト
        activity.add_participant(person1)
        assert len(activity.participants) == 2
    
    def test_add_tag(self):
        activity = Activity(id="a001", type=ActivityType.DOCUMENT, timestamp=datetime.now(), content="提案書作成")
        
        activity.add_tag("営業")
        activity.add_tag("提案書")
        activity.add_tag("営業")  # 重複
        activity.add_tag("URGENT")  # 大文字
        
        assert len(activity.tags) == 3
        assert "営業" in activity.tags
        assert "提案書" in activity.tags
        assert "urgent" in activity.tags
    
    def test_to_dict(self):
        person = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        activity = Activity(
            id="a001",
            type=ActivityType.EMAIL,
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            content="テストコンテンツ"
        )
        activity.add_participant(person)
        activity.add_tag("test")
        
        result = activity.to_dict()
        assert result["id"] == "a001"
        assert result["type"] == "email"
        assert result["participant_ids"] == ["p001"]
        assert result["tags"] == ["test"]


class TestWorkflow:
    def test_workflow_creation(self):
        owner = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        workflow = Workflow(
            id="w001",
            name="顧客提案フロー",
            owner=owner,
            frequency="週次",
            priority=Priority.HIGH
        )
        
        assert workflow.id == "w001"
        assert workflow.name == "顧客提案フロー"
        assert workflow.owner == owner
        assert workflow.frequency == "週次"
        assert workflow.priority == Priority.HIGH
        assert len(workflow.steps) == 0
    
    def test_add_steps(self):
        owner = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        workflow = Workflow(id="w001", name="提案フロー", owner=owner, frequency="週次")
        
        step1 = WorkflowStep(id="s001", name="要件確認", description="顧客要件の確認")
        step2 = WorkflowStep(id="s002", name="提案書作成", description="提案書の作成", duration_hours=4.0)
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        
        assert len(workflow.steps) == 2
        assert workflow.get_total_duration() == 4.0
    
    def test_workflow_participants(self):
        person1 = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        person2 = Person(id="p002", name="田中", department="営業", role="部長", email="tanaka@example.com")
        person3 = Person(id="p003", name="鈴木", department="企画", role="主任", email="suzuki@example.com")
        
        workflow = Workflow(id="w001", name="提案フロー", owner=person1, frequency="週次")
        
        step1 = WorkflowStep(id="s001", name="要件確認", description="顧客要件の確認", responsible=person1)
        step2 = WorkflowStep(id="s002", name="提案書作成", description="提案書の作成", responsible=person2)
        step3 = WorkflowStep(id="s003", name="レビュー", description="提案書のレビュー", responsible=person3)
        step4 = WorkflowStep(id="s004", name="最終確認", description="最終確認", responsible=person1)
        
        workflow.add_step(step1)
        workflow.add_step(step2)
        workflow.add_step(step3)
        workflow.add_step(step4)
        
        participants = workflow.get_participants()
        assert len(participants) == 3
        assert person1 in participants
        assert person2 in participants
        assert person3 in participants
    
    def test_workflow_dependencies(self):
        owner = Person(id="p001", name="山田", department="営業", role="課長", email="yamada@example.com")
        
        workflow1 = Workflow(id="w001", name="見積作成", owner=owner, frequency="都度")
        workflow2 = Workflow(id="w002", name="契約締結", owner=owner, frequency="都度")
        workflow3 = Workflow(id="w003", name="納品", owner=owner, frequency="都度")
        
        workflow2.add_dependency(workflow1)
        workflow3.add_dependency(workflow2)
        
        assert len(workflow2.dependencies) == 1
        assert workflow1 in workflow2.dependencies
        assert len(workflow3.dependencies) == 1
        assert workflow2 in workflow3.dependencies
        
        # 自己参照の防止
        workflow1.add_dependency(workflow1)
        assert len(workflow1.dependencies) == 0