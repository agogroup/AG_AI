from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActivityType(str, Enum):
    EMAIL = "email"
    DOCUMENT = "document"
    MEETING = "meeting"
    CHAT = "chat"
    TASK = "task"
    OTHER = "other"


class Person(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(..., description="一意識別子")
    name: str = Field(..., description="氏名")
    department: str = Field(..., description="部門")
    role: str = Field(..., description="役職")
    email: str = Field(..., description="メールアドレス")
    activities: List['Activity'] = Field(default_factory=list, description="活動履歴")
    skills: List[str] = Field(default_factory=list, description="スキル・専門領域")
    collaborators: List['Person'] = Field(default_factory=list, description="協働者リスト")
    metrics: Optional[Dict[str, Any]] = Field(None, description="ネットワーク分析メトリクス")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('有効なメールアドレスを入力してください')
        return v.lower()
    
    def add_activity(self, activity: 'Activity') -> None:
        self.activities.append(activity)
    
    def add_collaborator(self, person: 'Person') -> None:
        if person not in self.collaborators and person.id != self.id:
            self.collaborators.append(person)
    
    def get_activity_count(self, activity_type: Optional[ActivityType] = None) -> int:
        if activity_type:
            return len([a for a in self.activities if a.type == activity_type])
        return len(self.activities)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "role": self.role,
            "email": self.email,
            "skills": self.skills,
            "activity_count": len(self.activities),
            "collaborator_count": len(self.collaborators)
        }


class Activity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(..., description="一意識別子")
    type: ActivityType = Field(..., description="活動タイプ")
    timestamp: datetime = Field(..., description="活動日時")
    participants: List[Person] = Field(default_factory=list, description="参加者")
    content: str = Field(..., description="活動内容")
    tags: List[str] = Field(default_factory=list, description="タグ")
    related_documents: List['Document'] = Field(default_factory=list, description="関連文書")
    
    def add_participant(self, person: Person) -> None:
        if person not in self.participants:
            self.participants.append(person)
    
    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag.lower())
    
    def get_participant_ids(self) -> List[str]:
        return [p.id for p in self.participants]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "participant_ids": self.get_participant_ids(),
            "content_preview": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "tags": self.tags,
            "document_count": len(self.related_documents)
        }


class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(..., description="一意識別子")
    title: str = Field(..., description="文書タイトル")
    path: str = Field(..., description="ファイルパス")
    content: Optional[str] = Field(None, description="文書内容")
    created_at: datetime = Field(..., description="作成日時")
    modified_at: datetime = Field(..., description="更新日時")
    author: Optional[Person] = Field(None, description="作成者")
    tags: List[str] = Field(default_factory=list, description="タグ")
    
    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag.lower())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "path": self.path,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "author_id": self.author.id if self.author else None,
            "tags": self.tags
        }


class WorkflowStep(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(..., description="一意識別子")
    name: str = Field(..., description="ステップ名")
    description: str = Field(..., description="ステップの説明")
    responsible: Optional[Person] = Field(None, description="担当者")
    duration_hours: Optional[float] = Field(None, description="所要時間（時間）")
    dependencies: List['WorkflowStep'] = Field(default_factory=list, description="依存ステップ")
    
    def add_dependency(self, step: 'WorkflowStep') -> None:
        if step not in self.dependencies and step.id != self.id:
            self.dependencies.append(step)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "responsible_id": self.responsible.id if self.responsible else None,
            "duration_hours": self.duration_hours,
            "dependency_ids": [d.id for d in self.dependencies]
        }


class Department(BaseModel):
    """部門情報を表すモデル"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(..., description="一意識別子")
    name: str = Field(..., description="部門名")
    manager: Optional[Person] = Field(None, description="部門長")
    members: List[Person] = Field(default_factory=list, description="部門メンバー")
    parent_department: Optional['Department'] = Field(None, description="親部門")
    sub_departments: List['Department'] = Field(default_factory=list, description="子部門")
    
    def add_member(self, person: Person) -> None:
        if person not in self.members:
            self.members.append(person)
    
    def add_sub_department(self, department: 'Department') -> None:
        if department not in self.sub_departments:
            self.sub_departments.append(department)
            department.parent_department = self
    
    def get_all_members(self) -> List[Person]:
        """子部門を含む全メンバーを取得"""
        members = self.members.copy()
        for sub_dept in self.sub_departments:
            members.extend(sub_dept.get_all_members())
        return members
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "manager_id": self.manager.id if self.manager else None,
            "member_count": len(self.members),
            "sub_department_count": len(self.sub_departments),
            "parent_department_id": self.parent_department.id if self.parent_department else None
        }


class Workflow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str = Field(..., description="一意識別子")
    name: str = Field(..., description="ワークフロー名")
    owner: Person = Field(..., description="オーナー")
    steps: List[WorkflowStep] = Field(default_factory=list, description="ワークフローステップ")
    frequency: str = Field(..., description="実行頻度")
    priority: Priority = Field(Priority.MEDIUM, description="優先度")
    dependencies: List['Workflow'] = Field(default_factory=list, description="依存ワークフロー")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")
    
    def add_step(self, step: WorkflowStep) -> None:
        self.steps.append(step)
        self.updated_at = datetime.now()
    
    def add_dependency(self, workflow: 'Workflow') -> None:
        if workflow not in self.dependencies and workflow.id != self.id:
            self.dependencies.append(workflow)
            self.updated_at = datetime.now()
    
    def get_total_duration(self) -> float:
        return sum(step.duration_hours or 0 for step in self.steps)
    
    def get_participants(self) -> List[Person]:
        participants = []
        for step in self.steps:
            if step.responsible and step.responsible not in participants:
                participants.append(step.responsible)
        return participants
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner.id,
            "step_count": len(self.steps),
            "total_duration_hours": self.get_total_duration(),
            "frequency": self.frequency,
            "priority": self.priority.value,
            "participant_count": len(self.get_participants()),
            "dependency_count": len(self.dependencies),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


# Update forward references
Person.model_rebuild()
Activity.model_rebuild()
WorkflowStep.model_rebuild()
Department.model_rebuild()
Workflow.model_rebuild()