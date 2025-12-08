"""
이슈 랭킹 시스템
분석 결과를 기반으로 주요 이슈를 랭킹하고 저장합니다.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from app.core.database import AsyncSessionLocal
from app.core.models import AnalysisResult, IssueRanking, CollectedItem

logger = logging.getLogger("hourly_pulse")


async def calculate_item_interest_score(item: CollectedItem) -> int:
    """
    단일 아이템의 관심도 점수를 계산합니다.
    
    Args:
        item: CollectedItem 객체
    
    Returns:
        관심도 점수 (추정 조회수)
    """
    if not item.extra_data:
        return 100  # 기본값
    
    extra = item.extra_data if isinstance(item.extra_data, dict) else {}
    source_type = item.source_type or 'unknown'
    
    estimated_views = 0
    
    try:
        if source_type == 'youtube':
            # YouTube: 실제 조회수 사용 (가장 정확)
            estimated_views = int(extra.get('views', 0) or 0)
            
        elif source_type == 'reddit':
            # Reddit: upvotes와 comments를 기반으로 조회수 추정
            # 실제 Reddit의 view:upvote 비율은 약 10:1 ~ 50:1
            # 개선: 80배 → 15배로 조정 (더 현실적인 추정)
            upvotes = max(0, int(extra.get('upvotes', 0) or 0))
            comments = max(0, int(extra.get('comments', 0) or 0))
            estimated_views = (upvotes * 15) + (comments * 5)
            
        elif source_type == 'github':
            # GitHub: stars, forks, watchers를 기반으로 조회수 추정
            # Stars는 "좋아요" 개념이므로 views와 직접적인 상관관계가 낮음
            # 개선: 200배 → 20배로 조정 (더 현실적인 추정)
            stars = max(0, int(extra.get('stars', 0) or 0))
            forks = max(0, int(extra.get('forks', 0) or 0))
            watchers = max(0, int(extra.get('watchers', 0) or 0))
            # GitHub 저장소의 실제 views는 stars의 약 5~10배 정도
            estimated_views = (stars * 20) + (forks * 10) + (watchers * 3)
            
        elif source_type == 'news':
            # News: AI 추정 또는 휴리스틱 사용
            # 주의: AI 추정은 성능 문제로 인해 선택적으로만 사용
            # 현재는 개선된 휴리스틱 사용 (필요시 AI 추정 추가 가능)
            
            comments = max(0, int(extra.get('comments', 0) or 0))
            if comments > 0:
                # 댓글이 있으면 댓글 수 기반 추정
                estimated_views = comments * 50
            else:
                # 개선된 휴리스틱 점수 계산
                estimated_views = _calculate_news_heuristic_score(item)
                
        else:
            estimated_views = 100
        
        # 엣지 케이스 처리
        # 음수 방지
        estimated_views = max(0, estimated_views)
        # 매우 큰 값 제한 (오버플로우 방지, BigInteger 범위 내)
        estimated_views = min(estimated_views, 10_000_000_000)  # 100억 제한
        
    except (ValueError, TypeError) as e:
        logger.warning(f"⚠️ 관심도 계산 중 오류 발생 (item_id={item.id}, source_type={source_type}): {e}")
        estimated_views = 100  # 오류 시 기본값
    
    return int(estimated_views)


def _calculate_news_heuristic_score(item: CollectedItem) -> int:
    """
    News 아이템의 휴리스틱 관심도 점수를 계산합니다.
    
    Args:
        item: CollectedItem 객체
    
    Returns:
        추정 조회수
    """
    title = item.title or ""
    content = item.content or ""
    
    # 1. 제목 길이 점수 (적절한 길이의 제목이 더 높은 점수)
    title_length = len(title)
    if 20 <= title_length <= 100:
        length_score = 30  # 최적 길이
    elif 10 <= title_length < 20 or 100 < title_length <= 150:
        length_score = 20  # 보통 길이
    else:
        length_score = 10  # 너무 짧거나 긴 제목
    
    # 2. 중요 키워드 점수 (중복 제거)
    important_keywords = ['breaking', 'urgent', 'major', 'crisis', 'alert', 'important']
    keyword_score = sum(15 for kw in important_keywords if kw.lower() in title.lower())
    
    # 3. 내용 길이 점수 (내용이 있으면 추가 점수)
    content_length = len(content) if content else 0
    content_score = min(content_length / 100, 20)  # 최대 20점
    
    # 4. 기본 점수
    base_score = 100
    
    estimated_views = base_score + int(length_score) + keyword_score + int(content_score)
    return estimated_views


async def calculate_issue_rankings(hours: int = 1) -> List[Dict[str, Any]]:
    """
    분석 결과를 기반으로 이슈 랭킹을 계산합니다.
    
    Args:
        hours: 분석할 최근 시간 범위
    
    Returns:
        랭킹된 이슈 리스트
    """
    logger.info("📊 이슈 랭킹 계산 시작 (5분마다 수집된 데이터 기반)...")
    
    async with AsyncSessionLocal() as session:
        try:
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # 최근 분석 결과 가져오기
            analysis_query = select(AnalysisResult).where(
                AnalysisResult.analyzed_at >= cutoff_time
            ).order_by(desc(AnalysisResult.analyzed_at))
            
            analysis_result = await session.execute(analysis_query)
            analysis_results = list(analysis_result.scalars().all())
            
            if not analysis_results:
                logger.warning("⚠️ 분석 결과가 없어 랭킹을 계산할 수 없습니다.")
                return []
            
            logger.info(f"📊 분석 결과 {len(analysis_results)}개를 내용 그룹으로 분류 중...")
            
            # 이슈별로 그룹화 및 점수 계산 (내용 기반)
            # 단순 토픽명이 아닌, 실제 이슈 내용(what, why_now, context)을 기반으로 그룹화
            issue_scores = {}
            
            for result in analysis_results:
                # 이슈 식별: 토픽명 + 내용 기반
                topic = result.topic
                what = result.what or ''
                why_now = result.why_now or ''
                context = result.context or ''
                summary = result.summary or ''
                
                # 이슈의 고유 식별자 생성 (내용 기반)
                # why_now가 있으면 그것을 우선 사용, 없으면 what, 없으면 summary
                issue_content = why_now if why_now else (what if what else summary)
                
                # 이슈 키: 토픽명 + 주요 내용 기반 그룹화
                # 유사한 내용을 같은 그룹으로 묶기 위해 토픽명과 주요 키워드 조합 사용
                # 토픽명을 정규화 (소문자, 공백 제거)하여 유사한 토픽을 묶음
                normalized_topic = topic.lower().strip() if topic else ''
                # 주요 키워드 추출 (2글자 이상 단어만)
                topic_words = [w for w in normalized_topic.split() if len(w) > 2]
                # 토픽명의 핵심 키워드로 그룹화 (최대 3개 키워드 사용)
                if topic_words:
                    # 가장 긴 키워드 3개를 선택하여 그룹 키 생성
                    sorted_words = sorted(topic_words, key=len, reverse=True)[:3]
                    issue_key = ' '.join(sorted_words)
                else:
                    issue_key = normalized_topic if normalized_topic else 'unknown'
                
                if issue_key not in issue_scores:
                    issue_scores[issue_key] = {
                        'topic': topic,
                        'what': what,
                        'why_now': why_now,
                        'context': context,
                        'summary': summary,
                        'importance_scores': [],
                        'source_counts': [],
                        'mention_counts': [],
                        'sentiments': [],
                        'collected_item_ids': set(),
                        'analysis_ids': [],
                        'content_quality_score': 0.0,  # 내용 품질 점수
                        'temporal_relevance_score': 0.0  # 시점 관련성 점수
                    }
                
                # 점수 수집
                issue_scores[issue_key]['importance_scores'].append(result.importance_score or 0.0)
                issue_scores[issue_key]['source_counts'].append(result.source_count or 0)
                issue_scores[issue_key]['sentiments'].append(result.sentiment or 'neutral')
                issue_scores[issue_key]['analysis_ids'].append(result.id)
                
                # 내용 품질 점수 계산 (what, why_now, context가 모두 있으면 높은 점수)
                content_score = 0.0
                if what:
                    content_score += 0.3
                if why_now:
                    content_score += 0.5  # why_now가 가장 중요
                if context:
                    content_score += 0.2
                issue_scores[issue_key]['content_quality_score'] = max(
                    issue_scores[issue_key]['content_quality_score'],
                    content_score
                )
                
                # 시점 관련성 점수 (why_now가 있으면 높은 점수)
                if why_now:
                    issue_scores[issue_key]['temporal_relevance_score'] = 1.0
                elif what or context:
                    issue_scores[issue_key]['temporal_relevance_score'] = 0.5
                
                # 가장 상세한 내용으로 업데이트 (why_now 우선)
                if why_now and not issue_scores[issue_key]['why_now']:
                    issue_scores[issue_key]['why_now'] = why_now
                if what and not issue_scores[issue_key]['what']:
                    issue_scores[issue_key]['what'] = what
                if context and not issue_scores[issue_key]['context']:
                    issue_scores[issue_key]['context'] = context
                
                # 관련 아이템 ID 수집
                if result.collected_item_ids:
                    issue_scores[issue_key]['collected_item_ids'].update(result.collected_item_ids)
            
            # 각 이슈의 종합 점수 계산 (내용 기반 비교 분석)
            ranked_issues = []
            
            for issue_key, data in issue_scores.items():
                # 평균 중요도 점수
                avg_importance = sum(data['importance_scores']) / len(data['importance_scores']) if data['importance_scores'] else 0.0
                
                # 최대 소스 수
                max_sources = max(data['source_counts']) if data['source_counts'] else 0
                
                # 출처 정보 초기화
                top_source_types = []
                top_source_names = []
                
                # 관심도 계산: 최근 5분 동안 수집된 유사한 내용의 모든 아이템 관심도 합산
                # 5분마다 수집된 데이터로 내용 그룹의 관심도를 계산하여 순위를 매김
                interest_score = 0
                mention_count = 0
                from datetime import timezone
                now = datetime.now(timezone.utc)
                # 최근 5분 기준 시간 (5분마다 수집된 데이터만 사용)
                five_minutes_ago = now - timedelta(minutes=5)
                logger.debug(f"📊 [{data['topic']}] 최근 5분 데이터 기준 시간: {five_minutes_ago.isoformat()} ~ {now.isoformat()}")
                
                # 토픽명과 관련 키워드 추출
                topic = data['topic'].lower() if data['topic'] else ''
                # 토픽에서 주요 키워드 추출 (공백으로 분리)
                topic_keywords = [kw.strip() for kw in topic.split() if len(kw.strip()) > 2]
                if not topic_keywords:
                    topic_keywords = [topic] if topic else []
                
                # 변수 초기화
                items = []
                additional_items = []
                
                # 방법 1: collected_item_ids에 포함된 아이템 중 최근 5분 내 아이템
                if data['collected_item_ids']:
                    item_ids = list(data['collected_item_ids'])
                    # 관련 아이템 가져오기 (최근 5분 필터 적용)
                    items_query = select(CollectedItem).where(
                        CollectedItem.id.in_(item_ids[:200]),  # 최대 200개까지 확인
                        CollectedItem.collected_at >= five_minutes_ago  # 최근 5분 내 아이템만
                    )
                    items_result = await session.execute(items_query)
                    items = list(items_result.scalars().all())
                    
                    # collected_item_ids에 포함된 아이템은 모두 관련 아이템으로 간주
                    for item in items:
                        # calculate_item_interest_score 함수 사용
                        item_score = await calculate_item_interest_score(item)
                        interest_score += item_score
                        mention_count += 1
                    
                    logger.info(f"📊 [{data['topic']}] collected_item_ids 기반 최근 5분 내 아이템: {len(items)}개, 관심도 합계: {interest_score}")
                
                # 방법 2: collected_item_ids 외에도 토픽 키워드로 최근 5분 내 추가 검색
                # (더 많은 유사한 내용의 아이템을 찾기 위해)
                if topic_keywords:
                    from sqlalchemy import or_
                    # 최근 5분 내 모든 아이템 중 토픽 키워드가 포함된 아이템 검색
                    keyword_items_query = select(CollectedItem).where(
                        CollectedItem.collected_at >= five_minutes_ago
                    )
                    
                    # 제목이나 내용에 토픽 키워드가 포함된 아이템 찾기
                    title_conditions = [CollectedItem.title.ilike(f"%{kw}%") for kw in topic_keywords]
                    content_conditions = [CollectedItem.content.ilike(f"%{kw}%") for kw in topic_keywords]
                    keyword_items_query = keyword_items_query.where(
                        or_(*title_conditions, *content_conditions)
                    )
                    
                    keyword_items_result = await session.execute(keyword_items_query)
                    keyword_items = list(keyword_items_result.scalars().all())
                    
                    # collected_item_ids에 포함되지 않은 아이템만 추가
                    existing_item_ids = {item.id for item in items}
                    additional_items = [item for item in keyword_items if item.id not in existing_item_ids]
                    
                    additional_interest = 0
                    for item in additional_items:
                        # calculate_item_interest_score 함수 사용
                        item_score = await calculate_item_interest_score(item)
                        interest_score += item_score
                        additional_interest += item_score
                        mention_count += 1
                    
                    if additional_items:
                        logger.info(f"📊 [{data['topic']}] 토픽 키워드로 추가 발견: {len(additional_items)}개, 추가 관심도: {additional_interest}")
                
                logger.info(f"📊 [{data['topic']}] 최종 관심도 합계: {interest_score} (총 {mention_count}개 아이템)")
                
                # 소스 다양성 계산 (고유 소스 타입 수)
                source_diversity = 0
                top_source_types = []
                top_source_names = []
                
                # 최근 5분 내 아이템들의 소스 정보 수집
                all_recent_items = items + additional_items
                if all_recent_items:
                    # 최근 5분 내 아이템들의 소스 타입 확인
                    source_type_set = {item.source_type for item in all_recent_items if item.source_type}
                    source_diversity = len(source_type_set)
                    
                    # 주요 소스 타입 및 소스 이름 수집 (출처 정보)
                    source_type_counts = {}
                    source_name_counts = {}
                    
                    for item in all_recent_items[:100]:  # 최대 100개
                        source_type = item.source_type or 'unknown'
                        source_name = item.source or 'Unknown'
                        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
                        source_name_counts[source_name] = source_name_counts.get(source_name, 0) + 1
                    
                    # 상위 소스 타입 및 소스 이름 (빈도순)
                    top_source_types = sorted(source_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    top_source_names = sorted(source_name_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                elif data['collected_item_ids']:
                    # 아이템이 없으면 collected_item_ids로 소스 정보 조회
                    all_item_ids = list(data['collected_item_ids'])[:200]
                    if all_item_ids:
                        source_types_query = select(CollectedItem.source_type).where(
                            CollectedItem.id.in_(all_item_ids)
                        ).distinct()
                        source_types_result = await session.execute(source_types_query)
                        source_diversity = len(list(source_types_result.scalars().all()))
                        
                        all_items_query = select(CollectedItem.source_type, CollectedItem.source).where(
                            CollectedItem.id.in_(all_item_ids)
                        )
                        all_items_result = await session.execute(all_items_query)
                        all_source_data = list(all_items_result.all())
                        
                        source_type_counts = {}
                        source_name_counts = {}
                        for source_type, source_name in all_source_data:
                            if source_type:
                                source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
                            if source_name:
                                source_name_counts[source_name] = source_name_counts.get(source_name, 0) + 1
                        
                        top_source_types = sorted(source_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                        top_source_names = sorted(source_name_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                else:
                    # 수집된 아이템이 없으면 분석 결과 수를 사용
                    mention_count = len(data['analysis_ids'])
                    interest_score = mention_count  # 기본값: 언급 횟수와 동일
                    source_diversity = 0
                    top_source_types = []
                    top_source_names = []
                
                # 감정 분석 (가장 많이 나타난 감정)
                sentiment_counts = {}
                for sentiment in data['sentiments']:
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else 'neutral'
                
                # 내용 기반 점수 계산
                # 1. 내용 품질 점수 (what, why_now, context가 모두 있으면 높은 점수)
                content_quality = data['content_quality_score']
                
                # 2. 시점 관련성 점수 (why_now가 있으면 현재 이슈로 판단)
                temporal_relevance = data['temporal_relevance_score']
                
                # 3. 내용의 깊이 점수 (why_now와 context가 모두 있으면 높은 점수)
                depth_score = 0.0
                if data['why_now']:
                    depth_score += 0.6  # why_now가 가장 중요
                if data['context']:
                    depth_score += 0.4
                
                # 종합 점수 계산 (내용 기반 가중치 적용)
                # 중요도(25%) + 내용 품질(25%) + 시점 관련성(20%) + 언급 횟수(15%) + 소스 다양성(10%) + 내용 깊이(5%)
                mention_score = min(mention_count / 10.0, 1.0)  # 최대 10회 = 1.0
                diversity_score = min(source_diversity / 5.0, 1.0)  # 최대 5개 소스 = 1.0
                source_score = min(max_sources / 10.0, 1.0)  # 최대 10개 소스 = 1.0
                
                final_score = (
                    avg_importance * 0.25 +
                    content_quality * 0.25 +
                    temporal_relevance * 0.20 +
                    mention_score * 0.15 +
                    diversity_score * 0.10 +
                    depth_score * 0.05
                )
                
                # 이슈 설명 생성 (why_now 우선, 없으면 what, 없으면 summary)
                issue_description = data['why_now'] if data['why_now'] else (
                    data['what'] if data['what'] else data['summary']
                )
                
                ranked_issues.append({
                    'topic': data['topic'],
                    'description': issue_description,  # 실제 이슈 내용
                    'what': data['what'],
                    'why_now': data['why_now'],
                    'context': data['context'],
                    'score': final_score,
                    'mention_count': mention_count,
                    'interest_score': interest_score,  # 관심도 점수 추가
                    'source_diversity': source_diversity,
                    'max_sources': max_sources,
                    'sentiment': dominant_sentiment,
                    'content_quality': content_quality,
                    'temporal_relevance': temporal_relevance,
                    'collected_item_ids': list(data['collected_item_ids'])[:50],  # 최대 50개
                    'analysis_ids': data['analysis_ids'],
                    # 출처 정보 추가
                    'top_source_types': [{'type': st, 'count': cnt} for st, cnt in top_source_types],
                    'top_source_names': [{'name': sn, 'count': cnt} for sn, cnt in top_source_names]
                })
            
            # 관심도 점수순으로 정렬 (관심도가 높은 순서대로)
            ranked_issues.sort(key=lambda x: x['interest_score'], reverse=True)
            
            # 상위 10위까지만 반환 (5분마다 수집된 데이터로 계산된 관심도 기준)
            top_10_rankings = ranked_issues[:10]
            
            logger.info(f"✅ 이슈 랭킹 계산 완료: {len(ranked_issues)}개 이슈 중 상위 10위 선정")
            if top_10_rankings:
                logger.info("🏆 상위 10위 랭킹:")
                for i, ranking in enumerate(top_10_rankings, 1):
                    logger.info(f"  {i}. {ranking['topic']} (관심도: {ranking['interest_score']:,}, 점수: {ranking['score']:.3f})")
            
            return top_10_rankings
            
        except Exception as e:
            logger.error(f"❌ 이슈 랭킹 계산 실패: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return []


async def save_issue_rankings(rankings: List[Dict[str, Any]], period_hours: int = 1) -> int:
    """
    이슈 랭킹을 데이터베이스에 저장합니다.
    
    Args:
        rankings: 랭킹된 이슈 리스트
        period_hours: 랭킹 기간 (시간)
    
    Returns:
        저장된 랭킹 수
    """
    if not rankings:
        return 0
    
    saved_count = 0
    async with AsyncSessionLocal() as session:
        try:
            from datetime import timezone
            period_start = datetime.now(timezone.utc) - timedelta(hours=period_hours)
            period_end = datetime.now(timezone.utc)
            
            # 기존 랭킹 삭제 (같은 기간의 랭킹이 있으면)
            delete_query = select(IssueRanking).where(
                IssueRanking.period_start >= period_start - timedelta(hours=1)
            )
            existing = await session.execute(delete_query)
            for old_ranking in existing.scalars().all():
                await session.delete(old_ranking)
            
            # 새로운 랭킹 저장
            for rank, issue in enumerate(rankings, 1):
                # 트렌드 방향 계산
                trend_direction = await calculate_trend_direction(
                    topic=issue['topic'],
                    current_interest=issue.get('interest_score', issue['mention_count']),
                    current_rank=rank,
                    session=session
                )
                
                ranking = IssueRanking(
                    topic=issue['topic'],
                    rank=rank,
                    score=issue['score'],
                    mention_count=issue.get('interest_score', issue['mention_count']),  # 관심도를 mention_count에 저장
                    source_diversity=issue['source_diversity'],
                    trend_direction=trend_direction,  # 이전 랭킹과 비교하여 계산
                    period_start=period_start,
                    period_end=period_end,
                    description=issue.get('description', ''),
                    what=issue.get('what', ''),
                    why_now=issue.get('why_now', ''),
                    context=issue.get('context', '')
                )
                
                session.add(ranking)
                saved_count += 1
            
            await session.commit()
            logger.info(f"💾 이슈 랭킹 저장 완료: {saved_count}개")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ 이슈 랭킹 저장 실패: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            raise
    
    return saved_count


async def calculate_trend_direction(topic: str, current_interest: int, current_rank: int, session: AsyncSession) -> str:
    """
    이전 랭킹과 비교하여 트렌드 방향을 계산합니다.
    
    Args:
        topic: 트렌드 토픽
        current_interest: 현재 관심도 점수
        current_rank: 현재 순위
        session: 데이터베이스 세션
    
    Returns:
        트렌드 방향 ('up', 'down', 'stable')
    """
    try:
        # 이전 랭킹 조회 (최근 3개 주기, 약 15분)
        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=20)
        
        previous_rankings_query = select(IssueRanking).where(
            and_(
                IssueRanking.topic == topic,
                IssueRanking.period_end < cutoff_time
            )
        ).order_by(desc(IssueRanking.period_end)).limit(3)
        
        previous_result = await session.execute(previous_rankings_query)
        previous_rankings = list(previous_result.scalars().all())
        
        if not previous_rankings:
            return 'stable'  # 이전 데이터가 없으면 stable
        
        # 가장 최근 이전 랭킹 사용
        previous_ranking = previous_rankings[0]
        previous_interest = previous_ranking.mention_count or 0
        previous_rank = previous_ranking.rank or 999
        
        # 관심도 변화율 계산
        if previous_interest > 0:
            interest_change_rate = ((current_interest - previous_interest) / previous_interest) * 100
        else:
            interest_change_rate = 100 if current_interest > 0 else 0
        
        # 순위 변화 계산 (양수면 상승, 음수면 하락)
        rank_change = previous_rank - current_rank
        
        # 트렌드 방향 결정
        # 관심도가 50% 이상 증가하거나 순위가 3계단 이상 상승하면 'up'
        if interest_change_rate >= 50 or rank_change >= 3:
            return 'up'
        # 관심도가 30% 이상 감소하거나 순위가 3계단 이상 하락하면 'down'
        elif interest_change_rate <= -30 or rank_change <= -3:
            return 'down'
        else:
            return 'stable'
            
    except Exception as e:
        logger.warning(f"⚠️ 트렌드 방향 계산 실패 ({topic}): {e}")
        return 'stable'


async def detect_surge_trends(limit: int = 5) -> List[Dict[str, Any]]:
    """
    급상승 트렌드를 감지합니다.
    
    조건:
    - 관심도가 2배 이상 증가
    - 순위가 5계단 이상 상승
    - 최근 3개 랭킹 주기(15분) 내 급상승
    
    Args:
        limit: 반환할 최대 개수
    
    Returns:
        급상승 트렌드 리스트
    """
    async with AsyncSessionLocal() as session:
        try:
            from datetime import timezone
            from sqlalchemy import or_
            
            # 최근 랭킹 가져오기
            latest_period = await session.execute(
                select(func.max(IssueRanking.period_start))
            )
            latest_start = latest_period.scalar()
            
            if not latest_start:
                return []
            
            # 현재 랭킹 가져오기
            current_rankings_query = select(IssueRanking).where(
                IssueRanking.period_start == latest_start
            ).order_by(IssueRanking.rank)
            
            current_result = await session.execute(current_rankings_query)
            current_rankings = list(current_result.scalars().all())
            
            if not current_rankings:
                return []
            
            surge_trends = []
            
            # 각 현재 랭킹에 대해 이전 랭킹과 비교
            for current_ranking in current_rankings:
                topic = current_ranking.topic
                current_interest = current_ranking.mention_count or 0
                current_rank = current_ranking.rank
                
                # 최근 3개 랭킹 주기 조회 (약 15분)
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=20)
                
                previous_rankings_query = select(IssueRanking).where(
                    and_(
                        IssueRanking.topic == topic,
                        IssueRanking.period_end < cutoff_time
                    )
                ).order_by(desc(IssueRanking.period_end)).limit(3)
                
                previous_result = await session.execute(previous_rankings_query)
                previous_rankings = list(previous_result.scalars().all())
                
                if not previous_rankings:
                    continue
                
                # 가장 오래된 이전 랭킹과 비교 (15분 전)
                oldest_previous = previous_rankings[-1]
                previous_interest = oldest_previous.mention_count or 0
                previous_rank = oldest_previous.rank or 999
                
                # 관심도 변화율 계산
                if previous_interest > 0:
                    interest_change_rate = ((current_interest - previous_interest) / previous_interest) * 100
                    interest_multiplier = current_interest / previous_interest
                else:
                    interest_change_rate = 100 if current_interest > 0 else 0
                    interest_multiplier = 2.0 if current_interest > 0 else 1.0
                
                # 순위 변화 계산
                rank_change = previous_rank - current_rank  # 양수면 상승
                
                # 급상승 조건 확인
                is_surge = False
                surge_reason = []
                
                if interest_multiplier >= 2.0:  # 관심도 2배 이상 증가
                    is_surge = True
                    surge_reason.append(f"관심도 {interest_multiplier:.1f}배 증가")
                
                if rank_change >= 5:  # 순위 5계단 이상 상승
                    is_surge = True
                    surge_reason.append(f"순위 {rank_change}계단 상승")
                
                if interest_change_rate >= 100:  # 관심도 100% 이상 증가
                    is_surge = True
                    surge_reason.append(f"관심도 {interest_change_rate:.0f}% 증가")
                
                if is_surge:
                    surge_trends.append({
                        'topic': topic,
                        'current_rank': current_rank,
                        'previous_rank': previous_rank,
                        'rank_change': rank_change,
                        'current_interest': current_interest,
                        'previous_interest': previous_interest,
                        'interest_change_rate': interest_change_rate,
                        'interest_multiplier': interest_multiplier,
                        'surge_reason': ', '.join(surge_reason),
                        'description': current_ranking.description or '',
                        'what': current_ranking.what or '',
                        'why_now': current_ranking.why_now or '',
                        'context': current_ranking.context or '',
                    })
            
            # 관심도 변화율 기준으로 정렬 (가장 급상승한 순서)
            surge_trends.sort(key=lambda x: x['interest_change_rate'], reverse=True)
            
            logger.info(f"🔥 급상승 트렌드 {len(surge_trends)}개 감지")
            
            return surge_trends[:limit]
            
        except Exception as e:
            logger.error(f"❌ 급상승 트렌드 감지 실패: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            return []


async def get_top_rankings(limit: int = 10) -> List[IssueRanking]:
    """
    최신 이슈 랭킹을 가져옵니다.
    
    Args:
        limit: 가져올 최대 개수
    
    Returns:
        IssueRanking 리스트
    """
    async with AsyncSessionLocal() as session:
        try:
            # 가장 최근 기간의 랭킹 가져오기
            latest_period = await session.execute(
                select(func.max(IssueRanking.period_start))
            )
            latest_start = latest_period.scalar()
            
            if not latest_start:
                return []
            
            # 해당 기간의 랭킹 가져오기
            query = select(IssueRanking).where(
                IssueRanking.period_start == latest_start
            ).order_by(IssueRanking.rank).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"❌ 랭킹 조회 실패: {type(e).__name__} - {e}")
            return []


