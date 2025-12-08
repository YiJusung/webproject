"""
통합 수집기 테스트
모든 수집기를 한 번에 실행하고 결과를 확인합니다.
"""
import asyncio
import sys
from app.services.unified_collector import collect_all_sources

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_unified_collector():
    """
    통합 수집기를 테스트합니다.
    """
    print("=" * 70)
    print("🚀 통합 수집기 테스트")
    print("=" * 70)
    
    print("\n📥 모든 소스에서 데이터 수집 중...\n")
    
    try:
        collected_data = await collect_all_sources()
        
        print("=" * 70)
        print("📊 수집 결과 요약")
        print("=" * 70)
        
        total_items = 0
        for source, items in collected_data.items():
            if items:
                count = len(items)
                total_items += count
                print(f"\n📌 {source.upper()}: {count}개")
                
                # 각 소스별로 상위 3개 출력
                for i, item in enumerate(items[:3], 1):
                    title = item.get("title", "N/A")
                    if len(title) > 60:
                        title = title[:57] + "..."
                    
                    # 소스별 추가 정보 출력
                    if source == "reddit" or source == "reddit_subreddits":
                        upvotes = item.get("upvotes", 0)
                        print(f"  {i}. {title}")
                        if upvotes:
                            print(f"     👍 {upvotes:,} upvotes")
                    elif source == "github":
                        stars = item.get("stars", 0)
                        print(f"  {i}. {title}")
                        if stars:
                            print(f"     ⭐ {stars:,} stars")
                    elif source == "youtube":
                        views = item.get("views", 0)
                        print(f"  {i}. {title}")
                        if views:
                            print(f"     👁️  {views:,} views")
                    else:
                        print(f"  {i}. {title}")
        
        print("\n" + "=" * 70)
        print(f"✅ 전체 수집 완료! 총 {total_items}개 아이템")
        print("=" * 70)
        
        # 소스별 통계
        print("\n📈 소스별 통계:")
        for source, items in collected_data.items():
            if items:
                percentage = (len(items) / total_items * 100) if total_items > 0 else 0
                print(f"  {source}: {len(items)}개 ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"❌ 통합 수집 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_collector())




