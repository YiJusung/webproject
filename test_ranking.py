"""
이슈 랭킹 시스템 테스트
"""
import asyncio
import sys
from app.services.ranking import calculate_issue_rankings, save_issue_rankings, get_top_rankings

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_ranking():
    """
    이슈 랭킹 시스템을 테스트합니다.
    """
    print("=" * 70)
    print("🏆 이슈 랭킹 시스템 테스트")
    print("=" * 70)
    
    # 1. 랭킹 계산
    print("\n📊 [1단계] 이슈 랭킹 계산 중...")
    try:
        rankings = await calculate_issue_rankings(hours=24)  # 최근 24시간
        
        if rankings:
            print(f"✅ {len(rankings)}개 이슈 랭킹 계산 완료!")
            
            # 상위 10개 출력
            print("\n🏆 상위 10개 이슈:")
            for i, ranking in enumerate(rankings[:10], 1):
                topic = ranking.get('topic', 'N/A')
                score = ranking.get('score', 0)
                mentions = ranking.get('mention_count', 0)
                sources = ranking.get('source_diversity', 0)
                sentiment = ranking.get('sentiment', 'neutral')
                print(f"  {i}. {topic}")
                print(f"     점수: {score:.3f} | 언급: {mentions}회 | 소스: {sources}개 | 감정: {sentiment}")
            
            # 2. 랭킹 저장
            print("\n💾 [2단계] 랭킹 저장 중...")
            saved_count = await save_issue_rankings(rankings, period_hours=24)
            print(f"✅ {saved_count}개 랭킹 저장 완료!")
            
            # 3. 저장된 랭킹 조회
            print("\n📖 [3단계] 저장된 랭킹 조회 중...")
            top_rankings = await get_top_rankings(limit=10)
            
            if top_rankings:
                print(f"✅ {len(top_rankings)}개 랭킹 조회 완료!")
                print("\n📊 저장된 랭킹 (상위 5개):")
                for ranking in top_rankings[:5]:
                    print(f"  {ranking.rank}. {ranking.topic}")
                    print(f"     점수: {ranking.score:.3f} | 언급: {ranking.mention_count}회")
            else:
                print("⚠️ 저장된 랭킹이 없습니다.")
        else:
            print("⚠️ 랭킹할 이슈가 없습니다. (분석 결과가 필요합니다)")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ 이슈 랭킹 시스템 테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_ranking())




