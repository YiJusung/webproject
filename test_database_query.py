"""
데이터베이스 쿼리 테스트
저장된 데이터를 다양한 방식으로 조회합니다.
"""
import asyncio
import sys
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.models import CollectedItem, AnalysisResult

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_database_queries():
    """
    데이터베이스 쿼리를 테스트합니다.
    """
    print("=" * 70)
    print("🗄️  데이터베이스 쿼리 테스트")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. 전체 데이터 개수
            print("\n📊 [1] 전체 통계")
            print("-" * 70)
            total_count = await session.execute(select(func.count(CollectedItem.id)))
            print(f"  총 수집 아이템: {total_count.scalar()}개")
            
            # 2. 소스 타입별 개수
            print("\n📊 [2] 소스 타입별 통계")
            print("-" * 70)
            source_stats = await session.execute(
                select(CollectedItem.source_type, func.count(CollectedItem.id))
                .group_by(CollectedItem.source_type)
            )
            for source_type, count in source_stats:
                print(f"  {source_type}: {count}개")
            
            # 3. 최근 수집된 데이터 (상위 10개)
            print("\n📰 [3] 최근 수집된 데이터 (상위 10개)")
            print("-" * 70)
            recent_items = await session.execute(
                select(CollectedItem)
                .order_by(desc(CollectedItem.collected_at))
                .limit(10)
            )
            for i, item in enumerate(recent_items.scalars().all(), 1):
                title = item.title[:60] + "..." if len(item.title) > 60 else item.title
                print(f"  {i}. [{item.source_type}] {item.source}")
                print(f"     {title}")
                print(f"     수집 시간: {item.collected_at}")
                print()
            
            # 4. 소스별 최신 데이터
            print("\n📰 [4] 소스별 최신 데이터")
            print("-" * 70)
            sources = await session.execute(
                select(CollectedItem.source).distinct()
            )
            for source_row in sources.scalars().all():
                source = source_row
                latest = await session.execute(
                    select(CollectedItem)
                    .where(CollectedItem.source == source)
                    .order_by(desc(CollectedItem.collected_at))
                    .limit(1)
                )
                item = latest.scalar_one_or_none()
                if item:
                    title = item.title[:50] + "..." if len(item.title) > 50 else item.title
                    print(f"  {source}: {title}")
            
            # 5. 분석 결과 확인
            print("\n🤖 [5] 분석 결과 확인")
            print("-" * 70)
            analysis_count = await session.execute(select(func.count(AnalysisResult.id)))
            count = analysis_count.scalar()
            print(f"  총 분석 결과: {count}개")
            
            if count > 0:
                recent_analysis = await session.execute(
                    select(AnalysisResult)
                    .order_by(desc(AnalysisResult.analyzed_at))
                    .limit(5)
                )
                for i, result in enumerate(recent_analysis.scalars().all(), 1):
                    print(f"  {i}. {result.topic}")
                    print(f"     중요도: {result.importance_score:.2f}")
                    print(f"     감정: {result.sentiment}")
                    print(f"     소스 수: {result.source_count}개")
                    print()
            else:
                print("  분석 결과가 없습니다.")
            
            # 6. URL 중복 체크 테스트
            print("\n🔍 [6] URL 중복 체크 테스트")
            print("-" * 70)
            duplicate_urls = await session.execute(
                select(CollectedItem.url, func.count(CollectedItem.id))
                .where(CollectedItem.url.isnot(None))
                .group_by(CollectedItem.url)
                .having(func.count(CollectedItem.id) > 1)
            )
            dup_count = 0
            for url, count in duplicate_urls:
                dup_count += 1
            print(f"  중복된 URL: {dup_count}개")
            
            # 7. 메타데이터 확인
            print("\n📋 [7] 메타데이터 샘플")
            print("-" * 70)
            sample = await session.execute(
                select(CollectedItem)
                .where(CollectedItem.extra_data.isnot(None))
                .limit(3)
            )
            for item in sample.scalars().all():
                print(f"  소스: {item.source}")
                if item.extra_data:
                    print(f"  메타데이터: {list(item.extra_data.keys())}")
                print()
            
        except Exception as e:
            print(f"❌ 쿼리 실행 실패: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print("✅ 데이터베이스 쿼리 테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_database_queries())




