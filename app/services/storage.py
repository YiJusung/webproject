"""
수집된 데이터를 데이터베이스에 저장하는 모듈
"""
import logging
import sys
import asyncio
import os
import psutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, text
from app.core.database import AsyncSessionLocal
from app.core.models import CollectedItem

logger = logging.getLogger("hourly_pulse")

# 최대 저장 개수 (환경 변수로 설정 가능, 기본값: 50,000개)
MAX_STORED_ITEMS = int(os.getenv("MAX_STORED_ITEMS", "50000"))

# 최대 컨테이너 메모리 용량 (GB, 환경 변수로 설정 가능, 기본값: 7.5GB)
# Docker 컨테이너 메모리 제한에 맞춰 설정
MAX_CONTAINER_MEMORY_GB = float(os.getenv("MAX_CONTAINER_MEMORY_GB", "7.5"))

# 메모리 사용량 임계값 (이 비율을 초과하면 정리 시작, 기본값: 80%)
MEMORY_USAGE_THRESHOLD = float(os.getenv("MEMORY_USAGE_THRESHOLD", "0.8"))

# 최대 디스크 용량 (GB, 환경 변수로 설정 가능, 기본값: 800GB)
# Docker 제한이 1006.85GB이므로 80%인 800GB를 기본값으로 설정
MAX_DISK_SIZE_GB = float(os.getenv("MAX_DISK_SIZE_GB", "800"))

# 디스크 용량 임계값 (이 비율을 초과하면 정리 시작, 기본값: 80%)
DISK_USAGE_THRESHOLD = float(os.getenv("DISK_USAGE_THRESHOLD", "0.8"))

def check_event_loop():
    """
    Windows에서 이벤트 루프가 올바른지 확인합니다.
    """
    if sys.platform == 'win32':
        try:
            loop = asyncio.get_running_loop()
            if isinstance(loop, asyncio.ProactorEventLoop):
                logger.error("❌ ProactorEventLoop가 감지되었습니다! psycopg와 호환되지 않습니다.")
                raise RuntimeError(
                    "ProactorEventLoop는 psycopg와 호환되지 않습니다. "
                    "SelectorEventLoop를 사용하세요."
                )
        except RuntimeError:
            # 실행 중인 이벤트 루프가 없으면 무시
            pass


async def get_container_memory_usage_gb() -> Optional[float]:
    """
    Docker 컨테이너의 현재 메모리 사용량을 GB 단위로 반환합니다.
    
    Returns:
        메모리 사용량 (GB), 실패 시 None
    """
    try:
        # 프로세스의 메모리 사용량 확인 (RSS - Resident Set Size)
        process = psutil.Process()
        memory_bytes = process.memory_info().rss
        
        # GB로 변환
        memory_gb = memory_bytes / (1024 ** 3)
        return memory_gb
    except Exception as e:
        logger.error(f"❌ 컨테이너 메모리 사용량 조회 실패: {type(e).__name__} - {e}")
        return None


async def get_database_size_gb(session: AsyncSession) -> float:
    """
    데이터베이스의 현재 크기를 GB 단위로 반환합니다.
    
    Args:
        session: 데이터베이스 세션
    
    Returns:
        데이터베이스 크기 (GB)
    """
    try:
        # PostgreSQL의 pg_database_size 함수를 사용하여 데이터베이스 크기 확인
        # 현재 데이터베이스 이름을 가져옴
        db_name_result = await session.execute(text("SELECT current_database()"))
        db_name = db_name_result.scalar()
        
        # 데이터베이스 크기 조회 (바이트 단위)
        size_result = await session.execute(
            text(f"SELECT pg_database_size('{db_name}')")
        )
        size_bytes = size_result.scalar() or 0
        
        # GB로 변환
        size_gb = size_bytes / (1024 ** 3)
        return size_gb
    except Exception as e:
        logger.error(f"❌ 데이터베이스 크기 조회 실패: {type(e).__name__} - {e}")
        return 0.0


async def cleanup_by_memory_usage(session: AsyncSession, max_memory_gb: float = MAX_CONTAINER_MEMORY_GB, threshold: float = MEMORY_USAGE_THRESHOLD) -> int:
    """
    컨테이너 메모리 사용량이 임계값을 초과하면 가장 오래된 데이터부터 삭제합니다.
    
    Args:
        session: 데이터베이스 세션
        max_memory_gb: 최대 컨테이너 메모리 용량 (GB)
        threshold: 메모리 사용량 임계값 비율 (0.0 ~ 1.0)
    
    Returns:
        삭제된 아이템 수
    """
    try:
        # 현재 메모리 사용량 확인
        current_memory_gb = await get_container_memory_usage_gb()
        
        if current_memory_gb is None:
            logger.warning("⚠️ 메모리 사용량을 확인할 수 없어 메모리 기반 정리를 건너뜁니다.")
            return 0
        
        threshold_memory_gb = max_memory_gb * threshold
        
        logger.info(f"💾 현재 컨테이너 메모리 사용량: {current_memory_gb:.2f}GB / 최대 {max_memory_gb:.2f}GB (임계값: {threshold_memory_gb:.2f}GB)")
        
        if current_memory_gb < threshold_memory_gb:
            return 0
        
        # 임계값을 초과한 경우, 목표 메모리 사용량까지 삭제
        # 목표 메모리는 임계값의 70%로 설정 (여유 공간 확보)
        target_memory_gb = max_memory_gb * 0.7
        
        deleted_total = 0
        batch_size = 1000  # 한 번에 삭제할 개수
        max_iterations = 50  # 무한 루프 방지
        
        iteration = 0
        while current_memory_gb > target_memory_gb and iteration < max_iterations:
            iteration += 1
            
            # 가장 오래된 아이템들의 ID 조회
            old_items_query = (
                select(CollectedItem.id)
                .order_by(CollectedItem.collected_at.asc())
                .limit(batch_size)
            )
            old_items_result = await session.execute(old_items_query)
            old_item_ids = [row[0] for row in old_items_result.all()]
            
            if not old_item_ids:
                break
            
            # 삭제 실행
            delete_result = await session.execute(
                delete(CollectedItem).where(CollectedItem.id.in_(old_item_ids))
            )
            deleted_count = delete_result.rowcount
            deleted_total += deleted_count
            
            # 세션 커밋
            await session.commit()
            
            # 삭제 후 메모리 사용량 다시 확인
            current_memory_gb = await get_container_memory_usage_gb()
            if current_memory_gb is None:
                logger.warning("⚠️ 메모리 사용량 확인 실패, 정리 중단")
                break
            
            logger.info(f"🗑️ {deleted_count}개 삭제 후 메모리 사용량: {current_memory_gb:.2f}GB (목표: {target_memory_gb:.2f}GB)")
            
            # 더 이상 삭제할 데이터가 없으면 중단
            if deleted_count == 0:
                break
        
        if deleted_total > 0:
            logger.info(f"🗑️ 메모리 사용량 기반 정리 완료: 총 {deleted_total}개 삭제 (최종 메모리: {current_memory_gb:.2f}GB)")
        
        return deleted_total
    except Exception as e:
        logger.error(f"❌ 메모리 사용량 기반 정리 실패: {type(e).__name__} - {e}")
        return 0


async def cleanup_by_disk_size(session: AsyncSession, max_size_gb: float = MAX_DISK_SIZE_GB, threshold: float = DISK_USAGE_THRESHOLD) -> int:
    """
    디스크 용량이 임계값을 초과하면 가장 오래된 데이터부터 삭제합니다.
    
    Args:
        session: 데이터베이스 세션
        max_size_gb: 최대 디스크 용량 (GB)
        threshold: 용량 임계값 비율 (0.0 ~ 1.0)
    
    Returns:
        삭제된 아이템 수
    """
    try:
        # 현재 데이터베이스 크기 확인
        current_size_gb = await get_database_size_gb(session)
        threshold_size_gb = max_size_gb * threshold
        
        logger.info(f"💾 현재 데이터베이스 크기: {current_size_gb:.2f}GB / 최대 {max_size_gb:.2f}GB (임계값: {threshold_size_gb:.2f}GB)")
        
        if current_size_gb < threshold_size_gb:
            return 0
        
        # 임계값을 초과한 경우, 목표 크기까지 삭제
        # 목표 크기는 임계값의 70%로 설정 (여유 공간 확보)
        target_size_gb = max_size_gb * 0.7
        
        # 삭제할 데이터 양 계산 (대략적으로)
        # 각 아이템의 평균 크기를 추정하여 삭제할 개수 계산
        # 실제로는 반복적으로 삭제하면서 크기를 확인
        deleted_total = 0
        batch_size = 1000  # 한 번에 삭제할 개수
        
        while current_size_gb > target_size_gb:
            # 가장 오래된 아이템들의 ID 조회
            old_items_query = (
                select(CollectedItem.id)
                .order_by(CollectedItem.collected_at.asc())
                .limit(batch_size)
            )
            old_items_result = await session.execute(old_items_query)
            old_item_ids = [row[0] for row in old_items_result.all()]
            
            if not old_item_ids:
                break
            
            # 삭제 실행
            delete_result = await session.execute(
                delete(CollectedItem).where(CollectedItem.id.in_(old_item_ids))
            )
            deleted_count = delete_result.rowcount
            deleted_total += deleted_count
            
            # 세션 커밋
            await session.commit()
            
            # 삭제 후 크기 다시 확인
            current_size_gb = await get_database_size_gb(session)
            logger.info(f"🗑️ {deleted_count}개 삭제 후 데이터베이스 크기: {current_size_gb:.2f}GB (목표: {target_size_gb:.2f}GB)")
            
            # 더 이상 삭제할 데이터가 없으면 중단
            if deleted_count == 0:
                break
        
        if deleted_total > 0:
            logger.info(f"🗑️ 디스크 용량 정리 완료: 총 {deleted_total}개 삭제 (최종 크기: {current_size_gb:.2f}GB)")
        
        return deleted_total
    except Exception as e:
        logger.error(f"❌ 디스크 용량 기반 정리 실패: {type(e).__name__} - {e}")
        return 0


async def cleanup_old_items(session: AsyncSession, max_items: int = MAX_STORED_ITEMS) -> int:
    """
    데이터베이스에 저장된 아이템이 최대 개수를 초과하면 가장 오래된 데이터부터 삭제합니다.
    
    Args:
        session: 데이터베이스 세션
        max_items: 최대 저장 개수
    
    Returns:
        삭제된 아이템 수
    """
    try:
        # 현재 저장된 아이템 개수 확인
        count_result = await session.execute(select(func.count(CollectedItem.id)))
        current_count = count_result.scalar() or 0
        
        if current_count <= max_items:
            return 0
        
        # 삭제할 개수 계산
        items_to_delete = current_count - max_items
        
        # 가장 오래된 아이템부터 삭제 (collected_at 기준 오름차순)
        # 먼저 삭제할 아이템들의 ID를 조회
        old_items_query = (
            select(CollectedItem.id)
            .order_by(CollectedItem.collected_at.asc())
            .limit(items_to_delete)
        )
        old_items_result = await session.execute(old_items_query)
        old_item_ids = [row[0] for row in old_items_result.all()]
        
        if old_item_ids:
            # ID 목록을 사용하여 삭제
            delete_result = await session.execute(
                delete(CollectedItem).where(CollectedItem.id.in_(old_item_ids))
            )
            deleted_count = delete_result.rowcount
        else:
            deleted_count = 0
        
        if deleted_count > 0:
            logger.info(f"🗑️ 오래된 데이터 {deleted_count}개 삭제 (최대 저장 개수: {max_items}개 유지)")
        
        return deleted_count
    except Exception as e:
        logger.error(f"❌ 오래된 데이터 삭제 실패: {type(e).__name__} - {e}")
        return 0


async def save_collected_items(items: List[Dict[str, Any]], source_type: str) -> int:
    """
    수집된 아이템들을 데이터베이스에 저장합니다.
    
    Args:
        items: 수집된 아이템 리스트
        source_type: 소스 타입 (예: "reddit", "news", "github", "youtube")
    
    Returns:
        저장된 아이템 수
    """
    # 이벤트 루프 확인
    check_event_loop()
    
    if not items:
        return 0
    
    saved_count = 0
    async with AsyncSessionLocal() as session:
        try:
            # 저장 전에 메모리 사용량 기반 정리 (최우선순위)
            deleted_by_memory = await cleanup_by_memory_usage(session, MAX_CONTAINER_MEMORY_GB, MEMORY_USAGE_THRESHOLD)
            
            # 저장 전에 디스크 용량 기반 정리 (우선순위 2)
            deleted_by_size = await cleanup_by_disk_size(session, MAX_DISK_SIZE_GB, DISK_USAGE_THRESHOLD)
            
            # 저장 전에 오래된 데이터 정리 (최대 개수 초과 시, 우선순위 3)
            deleted_by_count = await cleanup_old_items(session, MAX_STORED_ITEMS)
            
            for item in items:
                # 중복 체크 없이 모든 데이터 저장
                url = item.get("url", "")
                title = item.get("title", "")
                
                # collected_at 파싱
                collected_at_str = item.get("collected_at")
                if collected_at_str:
                    try:
                        if isinstance(collected_at_str, str):
                            collected_at = datetime.fromisoformat(collected_at_str.replace('Z', '+00:00'))
                        else:
                            collected_at = datetime.now()
                    except:
                        collected_at = datetime.now()
                else:
                    collected_at = datetime.now()
                
                # CollectedItem 생성
                collected_item = CollectedItem(
                    source=item.get("source", "Unknown"),
                    source_type=source_type,
                    title=title,
                    content=item.get("description") or item.get("content", ""),
                    url=url,
                    extra_data={
                        "upvotes": item.get("upvotes"),
                        "likes": item.get("likes"),
                        "views": item.get("views"),
                        "comments": item.get("comments"),
                        "retweets": item.get("retweets"),
                        "stars": item.get("stars"),
                        "subreddit": item.get("subreddit"),
                        "channel": item.get("channel"),
                        "published": item.get("published_at") or item.get("published"),
                        **{k: v for k, v in item.items() if k not in [
                            "source", "title", "description", "content", "url",
                            "upvotes", "likes", "views", "comments", "retweets",
                            "stars", "subreddit", "channel", "published_at", "published",
                            "collected_at"
                        ]}
                    },
                    collected_at=collected_at
                )
                
                session.add(collected_item)
                saved_count += 1
            
            await session.commit()
            
            # 저장 후 현재 데이터 개수, 디스크 용량, 메모리 사용량 확인
            count_result = await session.execute(select(func.count(CollectedItem.id)))
            total_count = count_result.scalar() or 0
            db_size_gb = await get_database_size_gb(session)
            memory_gb = await get_container_memory_usage_gb()
            memory_info = f", 메모리: {memory_gb:.2f}GB" if memory_gb is not None else ""
            
            logger.info(f"💾 {source_type} 데이터 저장 완료: {saved_count}개 저장 (총 {len(items)}개 중, 현재 DB 총 {total_count}개, 크기: {db_size_gb:.2f}GB{memory_info})")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ {source_type} 데이터 저장 실패: {type(e).__name__} - {e}")
            raise
    
    return saved_count


async def save_all_collected_data(collected_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    """
    모든 수집된 데이터를 데이터베이스에 저장합니다.
    
    Args:
        collected_data: 소스별로 분류된 수집 데이터 딕셔너리
    
    Returns:
        소스별 저장된 아이템 수 딕셔너리
    """
    logger.info("💾 데이터베이스 저장 시작...")
    
    save_results = {}
    
    # 각 소스 타입별로 저장
    source_type_mapping = {
        "reddit": "reddit",
        "reddit_subreddits": "reddit",
        "news": "news",
        "github": "github",
        "youtube": "youtube"
    }
    
    for source_key, items in collected_data.items():
        if items:
            source_type = source_type_mapping.get(source_key, source_key)
            try:
                saved_count = await save_collected_items(items, source_type)
                save_results[source_key] = saved_count
            except Exception as e:
                logger.error(f"❌ {source_key} 저장 중 오류: {e}")
                save_results[source_key] = 0
    
    total_saved = sum(save_results.values())
    logger.info(f"💾 전체 저장 완료! 총 {total_saved}개 아이템 저장됨")
    
    return save_results


async def get_recent_items(source_type: str = None, limit: int = 10) -> List[CollectedItem]:
    """
    최근 수집된 아이템을 조회합니다.
    
    Args:
        source_type: 소스 타입 필터 (None이면 전체)
        limit: 조회할 최대 개수
    
    Returns:
        CollectedItem 리스트
    """
    # 이벤트 루프 확인
    check_event_loop()
    
    async with AsyncSessionLocal() as session:
        try:
            query = select(CollectedItem).order_by(CollectedItem.collected_at.desc())
            
            if source_type:
                query = query.where(CollectedItem.source_type == source_type)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"❌ 데이터 조회 실패: {type(e).__name__} - {e}")
            return []

