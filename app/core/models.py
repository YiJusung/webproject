"""
데이터베이스 모델 정의
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, DateTime, JSON, ARRAY
from sqlalchemy.sql import func
from datetime import datetime
from app.core.database import Base


class CollectedItem(Base):
    """
    수집된 데이터 아이템
    """
    __tablename__ = "collected_items"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False, index=True)  # 소스 이름 (예: "Reddit", "BBC News")
    source_type = Column(String, nullable=False, index=True)  # 소스 타입 (예: "reddit", "news", "github")
    title = Column(Text, nullable=False)
    content = Column(Text)  # 설명/내용
    url = Column(Text, index=True)  # 원본 URL
    extra_data = Column(JSON)  # 추가 데이터 (upvotes, likes, stars 등)
    collected_at = Column(DateTime(timezone=True), default=func.now(), index=True)


class AnalysisResult(Base):
    """
    AI 분석 결과
    """
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String, default="comprehensive")  # 분석 타입
    topic = Column(String, nullable=False, index=True)  # 토픽/이슈
    summary = Column(Text)  # 요약
    keywords = Column(JSON)  # 키워드 리스트 (JSON 배열로 저장)
    sentiment = Column(String, default="neutral")  # 감정 (positive, negative, neutral)
    importance_score = Column(Float, default=0.0)  # 중요도 점수
    source_count = Column(Integer, default=0)  # 관련 소스 개수
    collected_item_ids = Column(JSON)  # 관련 수집 아이템 ID 리스트 (JSON 배열로 저장)
    analyzed_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    # 새로운 필드: 맥락과 설명
    what = Column(Text)  # 이슈가 무엇인지 설명
    why_now = Column(Text)  # 왜 지금 이슈가 되고 있는지 설명
    context = Column(Text)  # 배경 맥락 설명


class IssueRanking(Base):
    """
    이슈 랭킹
    """
    __tablename__ = "issue_rankings"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False, index=True)  # 토픽/이슈
    rank = Column(Integer, nullable=False)  # 랭킹 순위
    score = Column(Float, nullable=False)  # 종합 점수
    mention_count = Column(BigInteger, default=0)  # 언급 횟수 (관심도 점수로 사용, BIGINT로 변경)
    source_diversity = Column(Integer, default=0)  # 소스 다양성
    trend_direction = Column(String, default="stable")  # 트렌드 방향 (up, down, stable)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)  # 랭킹 기간 시작
    period_end = Column(DateTime(timezone=True), nullable=False)  # 랭킹 기간 종료
    # 새로운 필드: 이슈 내용 설명
    description = Column(Text)  # 이슈 설명 (why_now 우선, 없으면 what, 없으면 summary)
    what = Column(Text)  # 이슈가 무엇인지
    why_now = Column(Text)  # 왜 지금 이슈가 되고 있는지
    context = Column(Text)  # 배경 맥락

