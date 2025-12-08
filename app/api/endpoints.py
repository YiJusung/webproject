"""
API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.services.storage import get_recent_items
from app.services.ranking import get_top_rankings, calculate_item_interest_score, detect_surge_trends
from app.core.models import CollectedItem, IssueRanking, AnalysisResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import AsyncSessionLocal

logger = logging.getLogger("hourly_pulse")
router = APIRouter()


@router.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Hourly Pulse API",
        "version": "0.1.0",
        "endpoints": {
            "/rankings": "이슈 랭킹 조회",
            "/recent": "최근 수집 데이터 조회",
            "/analysis": "최근 분석 결과 조회",
            "/stats": "통계 정보"
        }
    }


@router.get("/rankings")
async def get_rankings(
    limit: int = Query(10, ge=1, le=10, description="가져올 최대 개수 (최대 10개)"),
    lang: Optional[str] = Query("ko", description="언어 (ko 또는 en)")
) -> List[dict]:
    """
    최신 이슈 랭킹을 조회합니다.
    
    Args:
        limit: 가져올 최대 개수 (1-50)
    
    Returns:
        이슈 랭킹 리스트
    """
    try:
        from app.services.translator import translate_text
        
        rankings = await get_top_rankings(limit=limit)
        
        result = []
        async with AsyncSessionLocal() as session:
            for r in rankings:
                # 출처 정보 실시간 계산 (관련 아이템에서 소스 정보 추출)
                source_info = {"types": [], "names": []}
                try:
                    # AnalysisResult에서 collected_item_ids 가져오기
                    analysis_query = select(AnalysisResult).where(
                        AnalysisResult.topic == r.topic
                    ).order_by(desc(AnalysisResult.analyzed_at)).limit(5)
                    
                    analysis_result = await session.execute(analysis_query)
                    analyses = list(analysis_result.scalars().all())
                    
                    collected_item_ids = set()
                    for analysis in analyses:
                        if analysis.collected_item_ids:
                            if isinstance(analysis.collected_item_ids, list):
                                collected_item_ids.update(analysis.collected_item_ids[:20])  # 최대 20개
                    
                    if collected_item_ids:
                        item_ids_list = [int(id) for id in list(collected_item_ids) if id is not None]
                        if item_ids_list:
                            items_query = select(CollectedItem.source_type, CollectedItem.source).where(
                                CollectedItem.id.in_(item_ids_list)
                            )
                            
                            items_result = await session.execute(items_query)
                            source_data = list(items_result.all())
                            
                            # 소스 타입별 카운트
                            source_type_counts = {}
                            source_name_counts = {}
                            for source_type, source_name in source_data:
                                source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
                                source_name_counts[source_name] = source_name_counts.get(source_name, 0) + 1
                            
                            # 상위 3개씩만
                            source_info["types"] = [{"type": st, "count": cnt} for st, cnt in sorted(source_type_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
                            source_info["names"] = [{"name": sn, "count": cnt} for sn, cnt in sorted(source_name_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
                except Exception as e:
                    # 출처 정보 조회 실패 시 무시
                    pass
                
                # 언어에 따라 번역
                topic = r.topic
                description = r.description or ""
                what = r.what or ""
                why_now = r.why_now or ""
                context = r.context or ""
                
                if lang == "ko":
                    # 한국어로 번역 (필요한 경우)
                    if description and not any('\uac00' <= c <= '\ud7a3' for c in description[:50]):
                        description = await translate_text(description, "ko")
                    if what and not any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                        what = await translate_text(what, "ko")
                    if why_now and not any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                        why_now = await translate_text(why_now, "ko")
                    if context and not any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                        context = await translate_text(context, "ko")
                    if topic and not any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                        topic = await translate_text(topic, "ko")
                elif lang == "en":
                    # 영어로 번역 (필요한 경우)
                    if description and any('\uac00' <= c <= '\ud7a3' for c in description[:50]):
                        description = await translate_text(description, "en")
                    if what and any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                        what = await translate_text(what, "en")
                    if why_now and any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                        why_now = await translate_text(why_now, "en")
                    if context and any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                        context = await translate_text(context, "en")
                    if topic and any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                        topic = await translate_text(topic, "en")
                
                # 감정 정보 가져오기 (AnalysisResult에서)
                sentiment = 'neutral'
                try:
                    analysis_query_sentiment = select(AnalysisResult.sentiment).where(
                        AnalysisResult.topic == r.topic
                    ).order_by(desc(AnalysisResult.analyzed_at)).limit(5)
                    
                    sentiment_result = await session.execute(analysis_query_sentiment)
                    sentiments = [s for s in sentiment_result.scalars().all() if s]
                    
                    if sentiments:
                        # 가장 많이 나타난 감정
                        sentiment_counts = {}
                        for s in sentiments:
                            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
                        sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else 'neutral'
                except Exception:
                    pass
                
                # 출처 정보 가져오기 (IssueRanking에는 저장되지 않으므로, 최신 랭킹 계산 결과에서 가져옴)
                # 실제로는 상세 분석 API에서 제공하지만, 간단한 출처 정보는 여기서도 제공
                result_item = {
                    "rank": r.rank,
                    "topic": topic,
                    "description": description,
                    "what": what,
                    "why_now": why_now,
                    "context": context,
                    "score": r.score,
                    "mention_count": r.mention_count,  # 실제로는 interest_score가 저장됨
                    "interest_score": r.mention_count,  # 관심도 점수 (별도 필드로도 제공)
                    "source_diversity": r.source_diversity,
                    "trend_direction": r.trend_direction,
                    "sentiment": sentiment,  # 감정 정보 추가
                    "period_start": r.period_start.isoformat() if r.period_start else None,
                    "period_end": r.period_end.isoformat() if r.period_end else None,
                    "sources": source_info  # 출처 정보 추가
                }
                
                result.append(result_item)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"랭킹 조회 실패: {str(e)}")


@router.get("/surge-trends")
async def get_surge_trends(
    limit: int = Query(5, ge=1, le=10, description="가져올 최대 개수 (최대 10개)"),
    lang: Optional[str] = Query("ko", description="언어 (ko 또는 en)")
) -> List[dict]:
    """
    급상승 트렌드를 조회합니다.
    
    조건:
    - 관심도가 2배 이상 증가
    - 순위가 5계단 이상 상승
    - 최근 15분 내 급상승
    
    Args:
        limit: 가져올 최대 개수 (1-10)
        lang: 언어 설정
    
    Returns:
        급상승 트렌드 리스트
    """
    try:
        from app.services.translator import translate_text
        
        surge_trends = await detect_surge_trends(limit=limit)
        
        if not surge_trends:
            return []
        
        result = []
        async with AsyncSessionLocal() as session:
            for trend in surge_trends:
                topic = trend['topic']
                
                # 출처 정보 가져오기
                source_info = {"types": [], "names": []}
                try:
                    analysis_query = select(AnalysisResult).where(
                        AnalysisResult.topic == topic
                    ).order_by(desc(AnalysisResult.analyzed_at)).limit(5)
                    
                    analysis_result = await session.execute(analysis_query)
                    analyses = list(analysis_result.scalars().all())
                    
                    collected_item_ids = set()
                    for analysis in analyses:
                        if analysis.collected_item_ids:
                            if isinstance(analysis.collected_item_ids, list):
                                collected_item_ids.update(analysis.collected_item_ids[:20])
                    
                    if collected_item_ids:
                        item_ids_list = [int(id) for id in list(collected_item_ids) if id is not None]
                        if item_ids_list:
                            items_query = select(CollectedItem.source_type, CollectedItem.source).where(
                                CollectedItem.id.in_(item_ids_list)
                            )
                            
                            items_result = await session.execute(items_query)
                            source_data = list(items_result.all())
                            
                            source_type_counts = {}
                            source_name_counts = {}
                            for source_type, source_name in source_data:
                                source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
                                source_name_counts[source_name] = source_name_counts.get(source_name, 0) + 1
                            
                            source_info["types"] = [{"type": st, "count": cnt} for st, cnt in sorted(source_type_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
                            source_info["names"] = [{"name": sn, "count": cnt} for sn, cnt in sorted(source_name_counts.items(), key=lambda x: x[1], reverse=True)[:3]]
                except Exception as e:
                    pass
                
                # 언어에 따라 번역
                topic_translated = topic
                description = trend.get('description', '')
                what = trend.get('what', '')
                why_now = trend.get('why_now', '')
                context = trend.get('context', '')
                
                if lang == "ko":
                    if topic and not any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                        topic_translated = await translate_text(topic, "ko")
                    if description and not any('\uac00' <= c <= '\ud7a3' for c in description[:50]):
                        description = await translate_text(description, "ko")
                    if what and not any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                        what = await translate_text(what, "ko")
                    if why_now and not any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                        why_now = await translate_text(why_now, "ko")
                    if context and not any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                        context = await translate_text(context, "ko")
                elif lang == "en":
                    if topic and any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                        topic_translated = await translate_text(topic, "en")
                    if description and any('\uac00' <= c <= '\ud7a3' for c in description[:50]):
                        description = await translate_text(description, "en")
                    if what and any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                        what = await translate_text(what, "en")
                    if why_now and any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                        why_now = await translate_text(why_now, "en")
                    if context and any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                        context = await translate_text(context, "en")
                
                result.append({
                    "topic": topic_translated,
                    "current_rank": trend['current_rank'],
                    "previous_rank": trend['previous_rank'],
                    "rank_change": trend['rank_change'],
                    "current_interest": trend['current_interest'],
                    "previous_interest": trend['previous_interest'],
                    "interest_change_rate": trend['interest_change_rate'],
                    "interest_multiplier": trend['interest_multiplier'],
                    "surge_reason": trend['surge_reason'],
                    "description": description,
                    "what": what,
                    "why_now": why_now,
                    "context": context,
                    "sources": source_info,
                })
        
        return result
    except Exception as e:
        logger.error(f"❌ 급상승 트렌드 조회 실패: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=f"급상승 트렌드 조회 실패: {str(e)}")


@router.get("/recent")
async def get_recent(
    source_type: Optional[str] = Query(None, description="소스 타입 필터 (news, reddit, github, youtube)"),
    limit: int = Query(10, ge=1, le=100, description="가져올 최대 개수"),
    lang: Optional[str] = Query("ko", description="언어 (ko 또는 en)")
) -> List[dict]:
    """
    최근 수집된 데이터를 조회합니다.
    
    Args:
        source_type: 소스 타입 필터
        limit: 가져올 최대 개수
    
    Returns:
        수집 데이터 리스트
    """
    try:
        from app.services.translator import translate_text
        
        items = await get_recent_items(source_type=source_type, limit=limit)
        
        result = []
        for item in items:
            title = item.title or ""
            content = item.content or ""
            
            # 언어에 따라 번역
            if lang == "ko":
                # 한국어로 번역 (영어인 경우)
                if title and not any('\uac00' <= c <= '\ud7a3' for c in title[:50]):
                    title = await translate_text(title, "ko")
                if content and not any('\uac00' <= c <= '\ud7a3' for c in content[:100]):
                    content = await translate_text(content, "ko")
            elif lang == "en":
                # 영어로 번역 (한국어인 경우)
                if title and any('\uac00' <= c <= '\ud7a3' for c in title[:50]):
                    title = await translate_text(title, "en")
                if content and any('\uac00' <= c <= '\ud7a3' for c in content[:100]):
                    content = await translate_text(content, "en")
            
            result.append({
                "id": item.id,
                "source": item.source,
                "source_type": item.source_type,
                "title": title,
                "content": content,
                "url": item.url,
                "extra_data": item.extra_data,
                "collected_at": item.collected_at.isoformat() if item.collected_at else None,
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 실패: {str(e)}")


@router.get("/analysis")
async def get_analysis(
    limit: int = Query(10, ge=1, le=50, description="가져올 최대 개수"),
    lang: Optional[str] = Query("ko", description="언어 (ko 또는 en)")
) -> List[dict]:
    """
    최근 분석 결과를 조회합니다.
    
    Args:
        limit: 가져올 최대 개수
    
    Returns:
        분석 결과 리스트
    """
    async with AsyncSessionLocal() as session:
        try:
            query = select(AnalysisResult).order_by(
                desc(AnalysisResult.analyzed_at)
            ).limit(limit)
            
            result = await session.execute(query)
            analyses = list(result.scalars().all())
            
            from app.services.translator import translate_text
            
            translated_analyses = []
            for a in analyses:
                topic = a.topic or ""
                summary = a.summary or ""
                what = a.what or ""
                why_now = a.why_now or ""
                context = a.context or ""
                
                # 언어에 따라 번역
                if lang == "ko":
                    if topic and not any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                        topic = await translate_text(topic, "ko")
                    if summary and not any('\uac00' <= c <= '\ud7a3' for c in summary[:50]):
                        summary = await translate_text(summary, "ko")
                    if what and not any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                        what = await translate_text(what, "ko")
                    if why_now and not any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                        why_now = await translate_text(why_now, "ko")
                    if context and not any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                        context = await translate_text(context, "ko")
                elif lang == "en":
                    if topic and any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                        topic = await translate_text(topic, "en")
                    if summary and any('\uac00' <= c <= '\ud7a3' for c in summary[:50]):
                        summary = await translate_text(summary, "en")
                    if what and any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                        what = await translate_text(what, "en")
                    if why_now and any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                        why_now = await translate_text(why_now, "en")
                    if context and any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                        context = await translate_text(context, "en")
                
                translated_analyses.append({
                    "id": a.id,
                    "topic": topic,
                    "summary": summary,
                    "keywords": a.keywords,
                    "sentiment": a.sentiment,
                    "importance_score": a.importance_score,
                    "source_count": a.source_count,
                    "analyzed_at": a.analyzed_at.isoformat() if a.analyzed_at else None,
                    "what": what,
                    "why_now": why_now,
                    "context": context,
                })
            
            return translated_analyses
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"분석 결과 조회 실패: {str(e)}")


@router.get("/trends/{topic}/detail")
async def get_trend_detail(
    topic: str,
    lang: Optional[str] = Query("ko", description="언어 (ko 또는 en)")
) -> dict:
    """
    특정 트렌드의 상세 분석 정보를 조회합니다.
    
    Args:
        topic: 트렌드 토픽명
        lang: 언어 설정
    
    Returns:
        상세 분석 정보
    """
    async with AsyncSessionLocal() as session:
        try:
            from app.services.translator import translate_text
            from datetime import timezone, timedelta
            
            # URL 디코딩된 토픽명 사용 (FastAPI가 자동 디코딩하지만, 안전을 위해)
            decoded_topic = topic
            
            # 1. 해당 토픽의 최신 랭킹 정보 (정확한 매칭 시도)
            ranking_query = select(IssueRanking).where(
                IssueRanking.topic == decoded_topic
            ).order_by(desc(IssueRanking.period_start)).limit(1)
            
            ranking_result = await session.execute(ranking_query)
            ranking = ranking_result.scalar_one_or_none()
            
            # 랭킹을 찾지 못한 경우, 토픽명에 포함된 경우도 검색 (유연한 매칭)
            if not ranking:
                # LIKE 검색으로 유사한 토픽 찾기
                from sqlalchemy import or_
                try:
                    ranking_query_fuzzy = select(IssueRanking).where(
                        IssueRanking.topic.contains(decoded_topic)
                    ).order_by(desc(IssueRanking.period_start)).limit(1)
                    ranking_result_fuzzy = await session.execute(ranking_query_fuzzy)
                    ranking = ranking_result_fuzzy.scalar_one_or_none()
                except Exception:
                    ranking = None
            
            # 2. 관련 분석 결과들 (정확한 매칭 시도)
            analysis_query = select(AnalysisResult).where(
                AnalysisResult.topic == decoded_topic
            ).order_by(desc(AnalysisResult.analyzed_at)).limit(10)
            
            analysis_result = await session.execute(analysis_query)
            analyses = list(analysis_result.scalars().all())
            
            # 분석 결과가 없으면 유사한 토픽 검색
            if not analyses:
                try:
                    analysis_query_fuzzy = select(AnalysisResult).where(
                        AnalysisResult.topic.contains(decoded_topic)
                    ).order_by(desc(AnalysisResult.analyzed_at)).limit(10)
                    analysis_result_fuzzy = await session.execute(analysis_query_fuzzy)
                    analyses = list(analysis_result_fuzzy.scalars().all())
                except Exception:
                    analyses = []
            
            # 3. 관련 수집 아이템들
            collected_item_ids = set()
            for analysis in analyses:
                if analysis.collected_item_ids:
                    if isinstance(analysis.collected_item_ids, list):
                        collected_item_ids.update(analysis.collected_item_ids)
                    elif isinstance(analysis.collected_item_ids, (int, str)):
                        # 단일 ID인 경우
                        try:
                            collected_item_ids.add(int(analysis.collected_item_ids))
                        except (ValueError, TypeError):
                            pass
            
            logger.info(f"📊 AnalysisResult에서 수집한 collected_item_ids: {len(collected_item_ids)}개")
            if collected_item_ids:
                sample_ids = list(collected_item_ids)[:5]
                logger.info(f"📊 collected_item_ids 샘플: {sample_ids}")
            
            items = []
            if collected_item_ids:
                try:
                    item_ids_list = [int(id) for id in list(collected_item_ids)[:50] if id is not None]  # 최대 50개, None 제거
                    if item_ids_list:  # 빈 리스트 체크
                        items_query = select(CollectedItem).where(
                            CollectedItem.id.in_(item_ids_list)
                        ).order_by(desc(CollectedItem.collected_at))
                        
                        items_result = await session.execute(items_query)
                        items = list(items_result.scalars().all())
                except Exception as e:
                    logger.error(f"❌ 수집 아이템 조회 실패: {e}")
                    items = []
            
            # 4. 시간대별 관심도 추이 (이전 1시간, 5분 간격, 총 12개 구간)
            time_series = []
            now = datetime.now(timezone.utc)
            
            # 관련 아이템 찾기: collected_item_ids 우선 사용, 없으면 토픽 키워드로 검색
            all_related_items = []
            
            # 방법 1: AnalysisResult의 collected_item_ids 사용 (가장 정확)
            # 시간 필터 없이 모든 관련 아이템을 가져온 후, 시간대별 그룹화 시 최근 1시간만 사용
            if collected_item_ids:
                try:
                    item_ids_list = [int(id) for id in list(collected_item_ids) if id is not None]
                    if item_ids_list:
                        # 시간 필터 없이 모든 관련 아이템 조회 (시간대별 그룹화에서 필터링)
                        related_items_query = select(CollectedItem).where(
                            CollectedItem.id.in_(item_ids_list)
                        )
                        related_items_result = await session.execute(related_items_query)
                        all_related_items = list(related_items_result.scalars().all())
                        logger.info(f"📊 collected_item_ids로 {len(all_related_items)}개 아이템 찾음 (전체, 시간 필터 없음)")
                        
                        # 최근 1시간 내 아이템만 필터링 (그래프 표시용)
                        time_start = now - timedelta(hours=1)
                        all_related_items = [item for item in all_related_items 
                                           if item.collected_at and item.collected_at >= time_start]
                        logger.info(f"📊 최근 1시간 내 아이템: {len(all_related_items)}개")
                except Exception as e:
                    logger.error(f"❌ collected_item_ids 조회 실패: {e}")
            
            # 방법 2: collected_item_ids가 없거나 결과가 적으면 토픽 키워드로 검색
            # collected_item_ids가 없거나 최근 1시간 내 아이템이 없으면 더 넓은 범위에서 검색
            if len(all_related_items) == 0:
                topic_lower = decoded_topic.lower()
                # 특수문자 제거 및 키워드 추출
                import re
                # 마크다운 형식 제거 (** 등)
                topic_clean = re.sub(r'\*+', '', topic_lower).strip()
                topic_keywords = [kw.strip() for kw in topic_clean.split() if len(kw.strip()) > 2]
                if not topic_keywords:
                    topic_keywords = [topic_clean] if topic_clean else []
                
                logger.info(f"📊 토픽 키워드 추출: {topic_keywords}")
                
                if topic_keywords:
                    # 최근 7일 내에서 검색 (더 넓은 범위로 확장)
                    time_start = now - timedelta(days=7)
                    from sqlalchemy import or_
                    related_items_query = select(CollectedItem).where(
                        CollectedItem.collected_at >= time_start
                    )
                    
                    # 제목이나 내용에 토픽 키워드가 포함된 아이템 찾기
                    title_conditions = [CollectedItem.title.ilike(f"%{kw}%") for kw in topic_keywords]
                    content_conditions = [CollectedItem.content.ilike(f"%{kw}%") for kw in topic_keywords]
                    related_items_query = related_items_query.where(
                        or_(*title_conditions, *content_conditions)
                    )
                    
                    related_items_result = await session.execute(related_items_query)
                    keyword_items = list(related_items_result.scalars().all())
                    
                    logger.info(f"📊 토픽 키워드로 {len(keyword_items)}개 아이템 찾음 (최근 7일 내)")
                    
                    # 최근 1시간 내 아이템만 필터링 (그래프 표시용)
                    time_start_1h = now - timedelta(hours=1)
                    all_related_items = [item for item in keyword_items 
                                       if item.collected_at and item.collected_at >= time_start_1h]
                    logger.info(f"📊 최근 1시간 내 아이템: {len(all_related_items)}개")
                    
                    # 최근 1시간 내 아이템이 없으면, 최근 24시간 내 아이템도 사용 (그래프에 표시)
                    if len(all_related_items) == 0:
                        time_start_24h = now - timedelta(hours=24)
                        all_related_items = [item for item in keyword_items 
                                           if item.collected_at and item.collected_at >= time_start_24h]
                        logger.info(f"📊 최근 1시간 내 아이템이 없어 최근 24시간 내 아이템 사용: {len(all_related_items)}개")
                        # 시간 범위도 24시간으로 확장
                        time_start = time_start_24h
            
            logger.info(f"📊 시간대별 관심도 추이 계산: 총 {len(all_related_items)}개 관련 아이템")
            
            # 시간대별로 그룹화 (5분 단위)
            # 항상 현재 시간을 기준으로 최근 1시간을 표시
            # 각 구간은 5분 동안 수집된 데이터를 포함하며, 관심도 점수를 합산
            
            # 현재 시간을 기준으로 최근 1시간 범위 설정
            time_range_end = now
            time_range_start = now - timedelta(hours=1)
            
            logger.info(f"📊 그래프 시간 범위: {time_range_start} ~ {time_range_end} (현재 시간 기준 최근 1시간)")
            
            # 시간 범위를 5분 단위로 조정
            # 현재 시간을 5분 단위로 내림 (예: 21:47 -> 21:45)
            end_minute = time_range_end.minute
            end_floored_minute = (end_minute // 5) * 5
            time_range_end_floored = time_range_end.replace(minute=end_floored_minute, second=0, microsecond=0)
            
            # 시작 시간 계산: 종료 시간에서 정확히 1시간 전 (12개 구간, 5분 간격)
            time_range_start_floored = time_range_end_floored - timedelta(hours=1)
            
            # 정확히 12개 구간 생성 (5분 * 12 = 60분 = 1시간)
            minute_buckets = {}
            for i in range(12):
                # 시작 시간부터 5분 간격으로 구간 생성
                bucket_start = time_range_start_floored + timedelta(minutes=i * 5)
                bucket_end = bucket_start + timedelta(minutes=5)
                minute_buckets[bucket_start] = {
                    'start': bucket_start,
                    'end': bucket_end,
                    'items': []
                }
            
            logger.info(f"📊 5분 구간 생성: {len(minute_buckets)}개 구간, 첫 구간: {min(list(minute_buckets.keys()))}, 마지막 구간: {max(list(minute_buckets.keys()))}")
            
            # 아이템을 5분 단위 시간대별로 분류
            items_matched = 0
            items_not_matched = []
            for item in all_related_items:
                if item.collected_at:
                    # 아이템의 수집 시간이 속하는 5분 구간 찾기
                    matched = False
                    for bucket_start, bucket in minute_buckets.items():
                        if bucket['start'] <= item.collected_at < bucket['end']:
                            bucket['items'].append(item)
                            items_matched += 1
                            matched = True
                            break
                    
                    if not matched:
                        # 디버깅: 매칭되지 않은 아이템 로깅
                        items_not_matched.append({
                            'id': item.id,
                            'collected_at': item.collected_at.isoformat() if item.collected_at else None,
                            'title': item.title[:50] if item.title else None
                        })
            
            logger.info(f"📊 시간대별 분류 완료: {items_matched}/{len(all_related_items)}개 아이템이 구간에 매칭됨")
            
            # 매칭되지 않은 아이템이 있으면 상세 로깅
            if items_not_matched:
                logger.warning(f"⚠️ {len(items_not_matched)}개 아이템이 구간에 매칭되지 않음")
                logger.warning(f"⚠️ 첫 3개 미매칭 아이템: {items_not_matched[:3]}")
                logger.warning(f"⚠️ 구간 범위: {min(list(minute_buckets.keys()))} ~ {max(list(minute_buckets.keys()))}")
            
            # 각 구간별 아이템 수 로깅
            for bucket_start in sorted(minute_buckets.keys())[:3]:
                bucket = minute_buckets[bucket_start]
                logger.info(f"📊 구간 {bucket_start}: {len(bucket['items'])}개 아이템")
            
            # 각 5분 구간별 관심도 점수 계산
            total_items_in_buckets = 0
            sorted_bucket_starts = sorted(minute_buckets.keys())
            last_bucket_start = sorted_bucket_starts[-1] if sorted_bucket_starts else None  # 마지막 구간(현재 시간대)
            
            for bucket_start in sorted_bucket_starts:
                bucket = minute_buckets[bucket_start]
                bucket_interest_score = 0
                
                for item in bucket['items']:
                    # calculate_item_interest_score 함수 사용
                    item_score = await calculate_item_interest_score(item)
                    bucket_interest_score += item_score
                    total_items_in_buckets += 1
                    
                    # 디버깅: 첫 번째 아이템의 상세 정보 로깅
                    if total_items_in_buckets == 1:
                        logger.info(f"📊 첫 번째 아이템 상세: id={item.id}, source_type={item.source_type}, extra_data={item.extra_data}, score={item_score}")
                
                time_series.append({
                    "time": bucket_start.isoformat(),
                    "count": bucket_interest_score
                })
            
            # 모든 구간이 포함되었는지 확인 (12개 구간)
            if len(time_series) != 12:
                logger.warning(f"⚠️ 시간대별 데이터 개수 불일치: {len(time_series)}개 (예상: 12개)")
            
            # 로깅: 시간대별 데이터 요약
            non_zero_buckets = sum(1 for ts in time_series if ts['count'] > 0)
            total_interest = sum(ts['count'] for ts in time_series)
            max_interest = max((ts['count'] for ts in time_series), default=0)
            logger.info(f"📊 5분 간격 관심도 추이: {non_zero_buckets}/12 구간에 데이터 있음, 총 관심도: {total_interest}, 최대 관심도: {max_interest}, 버킷 내 아이템: {total_items_in_buckets}개")
            
            # 디버깅: 처음 3개와 마지막 3개 구간 데이터 로깅
            if time_series:
                logger.info(f"📊 처음 3개 5분 구간: {time_series[:3]}")
                logger.info(f"📊 마지막 3개 5분 구간: {time_series[-3:]}")
            
            # 데이터가 전혀 없는 경우 경고
            if total_interest == 0 and len(all_related_items) > 0:
                logger.warning(f"⚠️ 관련 아이템은 {len(all_related_items)}개 있지만 관심도 점수가 모두 0입니다. calculate_item_interest_score 함수를 확인하세요.")
            elif len(all_related_items) == 0:
                logger.warning(f"⚠️ 최근 1시간 내 관련 아이템이 없습니다. 토픽: {decoded_topic}, collected_item_ids: {len(collected_item_ids) if collected_item_ids else 0}개")
            
            # 전체 관심도 점수 계산 (순위표와 일치시키기 위해)
            # collected_item_ids로 찾은 모든 아이템의 관심도 합산 (시간 필터 없이)
            total_interest_score = 0
            if collected_item_ids:
                try:
                    item_ids_list = [int(id) for id in list(collected_item_ids) if id is not None]
                    if item_ids_list:
                        # 시간 필터 없이 모든 관련 아이템 조회
                        all_items_query = select(CollectedItem).where(
                            CollectedItem.id.in_(item_ids_list)
                        )
                        all_items_result = await session.execute(all_items_query)
                        all_items_for_total = list(all_items_result.scalars().all())
                        
                        # 전체 아이템의 관심도 점수 합산
                        for item in all_items_for_total:
                            item_score = await calculate_item_interest_score(item)
                            total_interest_score += item_score
                        
                        logger.info(f"📊 전체 관심도 점수 계산: {len(all_items_for_total)}개 아이템, 총 {total_interest_score}점")
                except Exception as e:
                    logger.error(f"❌ 전체 관심도 점수 계산 실패: {e}")
                    # Fallback: ranking의 mention_count 사용
                    total_interest_score = ranking.mention_count if ranking else 0
            else:
                # collected_item_ids가 없으면 ranking의 값 사용
                total_interest_score = ranking.mention_count if ranking else 0
            
            # 그래프의 마지막 구간(현재 시간대) 값을 전체 관심도 점수로 업데이트
            # 웹사이트에 표시되는 관심도 값과 일치시키기 위해
            if time_series and total_interest_score > 0:
                # 마지막 구간의 값을 전체 관심도 점수로 설정
                time_series[-1]['count'] = total_interest_score
                logger.info(f"📊 그래프의 현재 시간대 값 업데이트: {time_series[-1]['time']} -> {total_interest_score} (웹사이트 표시값과 일치)")
            
            # 5. 소스별 분포
            source_distribution = {}
            if items:
                source_stats_query = select(
                    CollectedItem.source_type,
                    func.count(CollectedItem.id)
                ).where(
                    CollectedItem.id.in_([item.id for item in items])
                ).group_by(CollectedItem.source_type)
                
                source_stats_result = await session.execute(source_stats_query)
                source_distribution = {source: count for source, count in source_stats_result}
            
            # 6. 감정 분석 통계
            sentiment_stats = {}
            for analysis in analyses:
                sentiment = analysis.sentiment or 'neutral'
                sentiment_stats[sentiment] = sentiment_stats.get(sentiment, 0) + 1
            
            # 7. 키워드 추출 (모든 분석 결과에서)
            all_keywords = []
            keyword_counts = {}
            for analysis in analyses:
                if analysis.keywords:
                    for keyword in analysis.keywords:
                        if isinstance(keyword, str):
                            keyword_lower = keyword.lower().strip()
                            if len(keyword_lower) > 2:
                                keyword_counts[keyword_lower] = keyword_counts.get(keyword_lower, 0) + 1
                                if keyword not in all_keywords:
                                    all_keywords.append(keyword)
            
            # 상위 키워드 정렬
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 8. AI 심층 분석 정보 가져오기 (ranking 우선, 없으면 analyses에서)
            topic_translated = topic
            description = ranking.description if ranking else ""
            what = ranking.what if ranking else ""
            why_now = ranking.why_now if ranking else ""
            context = ranking.context if ranking else ""
            
            # ranking에 정보가 없으면 analyses에서 가장 최신 분석 결과 사용
            if not what and not why_now and not context and analyses:
                latest_analysis = analyses[0]  # 가장 최신 분석 결과
                if not what and latest_analysis.what:
                    what = latest_analysis.what
                if not why_now and latest_analysis.why_now:
                    why_now = latest_analysis.why_now
                if not context and latest_analysis.context:
                    context = latest_analysis.context
                if not description and latest_analysis.summary:
                    description = latest_analysis.summary
            
            # 번역 처리
            if lang == "ko":
                if topic and not any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                    topic_translated = await translate_text(topic, "ko")
                if description and not any('\uac00' <= c <= '\ud7a3' for c in description[:50]):
                    description = await translate_text(description, "ko")
                if what and not any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                    what = await translate_text(what, "ko")
                if why_now and not any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                    why_now = await translate_text(why_now, "ko")
                if context and not any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                    context = await translate_text(context, "ko")
            elif lang == "en":
                if topic and any('\uac00' <= c <= '\ud7a3' for c in topic[:50]):
                    topic_translated = await translate_text(topic, "en")
                if description and any('\uac00' <= c <= '\ud7a3' for c in description[:50]):
                    description = await translate_text(description, "en")
                if what and any('\uac00' <= c <= '\ud7a3' for c in what[:50]):
                    what = await translate_text(what, "en")
                if why_now and any('\uac00' <= c <= '\ud7a3' for c in why_now[:50]):
                    why_now = await translate_text(why_now, "en")
                if context and any('\uac00' <= c <= '\ud7a3' for c in context[:50]):
                    context = await translate_text(context, "en")
            
            # 9. 관련 아이템 정리
            related_items = []
            for item in items[:20]:  # 최대 20개
                title = item.title or ""
                content = item.content or ""
                
                if lang == "ko":
                    if title and not any('\uac00' <= c <= '\ud7a3' for c in title[:50]):
                        title = await translate_text(title, "ko")
                    if content and not any('\uac00' <= c <= '\ud7a3' for c in content[:100]):
                        content = await translate_text(content, "ko")
                elif lang == "en":
                    if title and any('\uac00' <= c <= '\ud7a3' for c in title[:50]):
                        title = await translate_text(title, "en")
                    if content and any('\uac00' <= c <= '\ud7a3' for c in content[:100]):
                        content = await translate_text(content, "en")
                
                related_items.append({
                    "id": item.id,
                    "source": item.source,
                    "source_type": item.source_type,
                    "title": title,
                    "content": content[:200] if content else "",  # 내용 요약
                    "url": item.url,
                    "collected_at": item.collected_at.isoformat() if item.collected_at else None,
                    "extra_data": item.extra_data
                })
            
            return {
                "topic": topic_translated,
                "ranking": {
                    "rank": ranking.rank if ranking else None,
                    "score": ranking.score if ranking else None,
                    "mention_count": ranking.mention_count if ranking else 0,
                    "interest_score": total_interest_score if total_interest_score > 0 else (ranking.mention_count if ranking else 0), # 전체 관심도 점수 (순위표와 동일)
                    "source_diversity": ranking.source_diversity if ranking else 0,
                    "trend_direction": ranking.trend_direction if ranking else "stable",
                    "period_start": ranking.period_start.isoformat() if ranking and ranking.period_start else None,
                    "period_end": ranking.period_end.isoformat() if ranking and ranking.period_end else None,
                },
                "analysis": {
                    "description": description,
                    "what": what,
                    "why_now": why_now,
                    "context": context,
                    "total_analyses": len(analyses),
                },
                "statistics": {
                    "total_items": len(items),
                    "total_mentions": ranking.mention_count if ranking else (sum(len(analysis.collected_item_ids) if isinstance(analysis.collected_item_ids, list) else 0 for analysis in analyses) if analyses else 0),  # 실제로는 interest_score
                    "total_interest_score": total_interest_score,  # 전체 관심도 점수 (collected_item_ids 기반 계산)
                    "source_distribution": source_distribution,
                    "sentiment_distribution": sentiment_stats,
                    "top_keywords": [kw for kw, count in top_keywords],
                },
                "time_series": time_series,
                "keywords": [{"keyword": k, "count": c} for k, c in top_keywords],
                "related_items": related_items,
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"상세 분석 조회 실패: {str(e)}")


@router.get("/stats")
async def get_stats() -> dict:
    """
    통계 정보를 조회합니다.
    
    Returns:
        통계 정보 딕셔너리
    """
    async with AsyncSessionLocal() as session:
        try:
            # 수집 데이터 통계
            collected_count = await session.execute(
                select(func.count(CollectedItem.id))
            )
            total_collected = collected_count.scalar() or 0
            
            # 소스 타입별 통계
            source_stats = await session.execute(
                select(
                    CollectedItem.source_type,
                    func.count(CollectedItem.id)
                ).group_by(CollectedItem.source_type)
            )
            source_counts = {source: count for source, count in source_stats}
            
            # 분석 결과 통계
            analysis_count = await session.execute(
                select(func.count(AnalysisResult.id))
            )
            total_analysis = analysis_count.scalar() or 0
            
            # 랭킹 통계
            ranking_count = await session.execute(
                select(func.count(IssueRanking.id))
            )
            total_rankings = ranking_count.scalar() or 0
            
            # 최근 수집 시간
            latest_collected = await session.execute(
                select(func.max(CollectedItem.collected_at))
            )
            latest_collected_time = latest_collected.scalar()
            
            return {
                "total_collected": total_collected,
                "source_counts": source_counts,
                "total_analysis": total_analysis,
                "total_rankings": total_rankings,
                "latest_collected": latest_collected_time.isoformat() if latest_collected_time else None,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


