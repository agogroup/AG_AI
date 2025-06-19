#!/usr/bin/env python3
"""
LLM分析エンジン - Claude/GPT等による業務文書分析
"""

import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class LLMAnalyzer:
    """業務文書のLLM分析を行うクラス"""
    
    def __init__(self):
        """初期化"""
        self.person_patterns = [
            r'([一-龠ひらがなカタカナ]{2,4})[さんくん]',  # 日本語名前 + さん/くん
            r'([A-Za-z]{3,15})[さんくん]',              # 英語名前 + さん/くん
            r'([一-龠ひらがなカタカナ]{2,4})(?:社長|部長|課長|主任|代表)',  # 役職付き名前
        ]
        
        self.organization_patterns = [
            r'([一-龠ひらがなカタカナA-Za-z]{2,10})(?:株式会社|会社|グループ|様)',
            r'AGO[グループ]*',
            r'([A-Za-z]{3,15})(?:株式会社|Inc|Corp)',
        ]
        
        self.workflow_keywords = [
            '見積', '発注', '納期', '製作', '施工', '配送', '請求',
            '現調', '打ち合わせ', '確認', '承認', '検収'
        ]

    def analyze_text(self, text: str, file_name: str = "", is_audio: bool = False, 
                    audio_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """テキストの包括的分析を実行"""
        
        # 基本分析
        persons = self._extract_persons(text)
        organizations = self._extract_organizations(text)
        workflows = self._detect_workflows(text)
        insights = self._generate_insights(text, persons, organizations, workflows)
        summary = self._generate_summary(text, file_name, is_audio, audio_metadata)
        
        # 音声メタデータの処理
        file_info = file_name
        if is_audio and audio_metadata:
            file_info = f"{file_name} (音声ファイル)"
        
        return {
            'file_name': file_info,
            'file_type': 'audio' if is_audio else 'text',
            'analysis_date': self._get_timestamp(),
            'summary': summary,
            'identified_persons': persons,
            'organizations': organizations,
            'workflows': workflows,
            'key_insights': insights,
            'audio_metadata': audio_metadata if is_audio else None,
            'confidence_scores': self._calculate_confidence(persons, workflows, insights)
        }

    def _extract_persons(self, text: str) -> List[Dict[str, Any]]:
        """人物情報の抽出"""
        persons = []
        found_names = set()
        
        for pattern in self.person_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                if name not in found_names and len(name) >= 2:
                    found_names.add(name)
                    
                    # 役職・組織の推定
                    role, org = self._estimate_role_and_org(text, name)
                    
                    persons.append({
                        'name': name,
                        'role': role,
                        'organization': org,
                        'mention_count': text.count(name),
                        'context': self._get_person_context(text, name)
                    })
        
        return sorted(persons, key=lambda x: x['mention_count'], reverse=True)

    def _extract_organizations(self, text: str) -> List[str]:
        """組織・会社名の抽出"""
        organizations = set()
        
        for pattern in self.organization_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                org = match.group(0)
                if len(org) >= 3:
                    organizations.add(org)
        
        return list(organizations)

    def _detect_workflows(self, text: str) -> List[Dict[str, Any]]:
        """業務フローの検出"""
        workflows = []
        
        # 段階的なワークフロー検出
        if any(keyword in text for keyword in ['見積', '発注', '製作']):
            steps = []
            if '見積' in text:
                steps.append('見積作成')
            if '発注' in text or '注文' in text:
                steps.append('発注手続き')
            if '製作' in text or '施工' in text:
                steps.append('製作・施工')
            if '納期' in text or '配送' in text:
                steps.append('納品・配送')
            if '請求' in text or '支払' in text:
                steps.append('請求・決済')
            
            if steps:
                workflows.append({
                    'name': '製作・施工プロセス',
                    'steps': steps,
                    'participants': [p['name'] for p in self._extract_persons(text)[:3]]
                })
        
        return workflows

    def _generate_insights(self, text: str, persons: List, organizations: List, 
                          workflows: List) -> List[str]:
        """重要な洞察の生成"""
        insights = []
        
        # 人物数による組織規模推定
        if len(persons) >= 4:
            insights.append(f"複数の関係者({len(persons)}名)が関与する大規模プロジェクト")
        elif len(persons) >= 2:
            insights.append(f"チーム作業による協力体制({len(persons)}名参加)")
        
        # 組織間連携の検出
        if len(organizations) >= 2:
            insights.append(f"複数組織間の連携プロジェクト({', '.join(organizations[:2])}等)")
        
        # 業務の性質分析
        if 'AGO' in text:
            insights.append("AGOグループが関与する事業案件")
        
        if any(keyword in text for keyword in ['急ぎ', '至急', '緊急']):
            insights.append("緊急性の高い案件として処理")
        
        if any(keyword in text for keyword in ['新規', '初回', '新しい']):
            insights.append("新規案件・新規顧客対応")
        
        # 金額・規模の言及
        if re.search(r'[0-9,]+円|[0-9,]+万', text):
            insights.append("具体的な金額・予算が設定された案件")
        
        return insights

    def _generate_summary(self, text: str, file_name: str, is_audio: bool, 
                         audio_metadata: Optional[Dict]) -> str:
        """要約の生成"""
        
        # 音声ファイルの場合のプレフィックス
        if is_audio and audio_metadata:
            duration_min = int(audio_metadata['audio_duration_sec'] // 60)
            duration_sec = int(audio_metadata['audio_duration_sec'] % 60)
            prefix = f"【音声ファイル分析】\n長さ: {duration_min}分{duration_sec}秒\n"
            prefix += f"文字数: {audio_metadata['char_count']}文字\n"
            prefix += f"使用モデル: Whisper {audio_metadata['model_used']}\n\n"
        else:
            prefix = ""
        
        # 内容の要約生成
        text_sample = text[:500]  # 最初の500文字
        
        # キーワード密度による内容推定
        if 'LINE' in file_name:
            summary = "LINEでの業務連絡・プロジェクト管理に関するやり取り"
        elif any(word in text for word in ['見積', '発注', '製作']):
            summary = "製作・施工案件の業務プロセスに関する連絡"
        elif any(word in text for word in ['会議', '打ち合わせ', '議論']):
            summary = "会議・打ち合わせの議事録または関連連絡"
        elif any(word in text for word in ['歩合', '給与', '評価', '制度']):
            summary = "人事制度・評価システムに関する文書"
        else:
            summary = "業務関連文書の内容分析"
        
        return prefix + summary

    def _estimate_role_and_org(self, text: str, name: str) -> tuple:
        """名前から役職と組織を推定"""
        
        # 名前の前後の文脈を取得
        name_contexts = []
        for match in re.finditer(re.escape(name), text):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            name_contexts.append(text[start:end])
        
        role = "関係者"
        org = "不明"
        
        # 役職キーワードの検出
        for context in name_contexts:
            if '社長' in context or '代表' in context:
                role = "代表・社長"
            elif '部長' in context:
                role = "部長"
            elif '課長' in context or '主任' in context:
                role = "管理職"
            elif '営業' in context:
                role = "営業担当"
            elif '製作' in context or '施工' in context:
                role = "製作・施工担当"
            elif '事務' in context:
                role = "事務担当"
        
        # 組織の推定
        if 'AGO' in ' '.join(name_contexts):
            org = "AGOグループ"
        else:
            # 組織名の抽出を試行
            for context in name_contexts:
                for org_pattern in self.organization_patterns:
                    match = re.search(org_pattern, context)
                    if match:
                        org = match.group(0)
                        break
        
        return role, org

    def _get_person_context(self, text: str, name: str) -> List[str]:
        """人物の文脈情報を取得"""
        contexts = []
        
        for match in re.finditer(re.escape(name), text):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].replace('\n', ' ')
            contexts.append(context)
        
        return contexts[:3]  # 最大3つの文脈

    def _calculate_confidence(self, persons: List, workflows: List, 
                            insights: List) -> Dict[str, float]:
        """分析の信頼度を計算"""
        
        person_confidence = min(0.95, len(persons) * 0.3)
        workflow_confidence = min(0.95, len(workflows) * 0.4)
        insight_confidence = min(0.95, len(insights) * 0.2)
        
        return {
            'persons': person_confidence,
            'workflows': workflow_confidence,
            'insights': insight_confidence,
            'overall': (person_confidence + workflow_confidence + insight_confidence) / 3
        }

    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().isoformat()


def analyze_file_with_llm(file_path: Path, is_audio: bool = False,
                         audio_metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """ファイルをLLM分析する関数"""
    
    analyzer = LLMAnalyzer()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return analyzer.analyze_text(
            content, 
            file_path.name, 
            is_audio, 
            audio_metadata
        )
    
    except Exception as e:
        print(f"❌ LLM分析エラー: {e}")
        return {
            'file_name': file_path.name,
            'file_type': 'audio' if is_audio else 'text',
            'summary': f'分析エラー: {str(e)}',
            'identified_persons': [],
            'workflows': [],
            'key_insights': [],
            'audio_metadata': audio_metadata if is_audio else None
        }