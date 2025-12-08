"""
안전한 데이터만 사용하여 AI 분석 테스트
"""
import asyncio
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.models import CollectedItem
from app.services.ai_analyzer import analyze_text_with_ai

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_ai_with_safe_data():
    """
    안전한 데이터만 사용하여 AI 분석을 테스트합니다.
    """
    print("=" * 70)
    print("🤖 안전한 데이터로 AI 분석 테스트")
    print("=" * 70)
    
    # GitHub와 기술 뉴스만 가져오기
    async with AsyncSessionLocal() as session:
        try:
            # GitHub 저장소만 가져오기
            query = select(CollectedItem).where(
                CollectedItem.source_type == "github"
            ).limit(10)
            
            result = await session.execute(query)
            github_items = list(result.scalars().all())
            
            # 기술 뉴스만 가져오기
            tech_news_query = select(CollectedItem).where(
                CollectedItem.source_type == "news",
                CollectedItem.source.in_(["HackerNews", "TechCrunch", "ArsTechnica", "Wired"])
            ).limit(10)
            
            tech_result = await session.execute(tech_news_query)
            tech_items = list(tech_result.scalars().all())
            
            # 안전한 텍스트 준비
            texts = []
            for item in github_items[:5] + tech_items[:5]:
                title = item.title or ""
                import html
                title = html.unescape(title)
                title = title.replace('\n', ' ').replace('\r', ' ').strip()
                if title and len(title) > 10:
                    texts.append(title[:80])
            
            if not texts:
                print("❌ 분석할 안전한 데이터가 없습니다.")
                return
            
            test_text = "\n".join(texts)
            print(f"\n📝 분석할 텍스트 ({len(texts)}개 항목):")
            print("-" * 70)
            for i, text in enumerate(texts[:5], 1):
                print(f"  {i}. {text}")
            print()
            
            # AI 분석 실행
            print("🤖 AI 분석 시작...")
            result = await analyze_text_with_ai(test_text, "summary")
            
            if result:
                print("\n✅ AI 분석 성공!")
                print("=" * 70)
                print(f"주요 이슈: {result.get('topics', [])}")
                print(f"\n요약: {result.get('summary', 'N/A')}")
                print(f"\n키워드: {result.get('keywords', [])}")
                print(f"\n감정: {result.get('sentiment', 'N/A')}")
            else:
                print("\n❌ AI 분석 실패")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(test_ai_with_safe_data())




