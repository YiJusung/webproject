"""
수동으로 AI 분석과 랭킹을 실행하는 스크립트
"""
import asyncio
import sys
from app.services.ai_analyzer import analyze_collected_data, save_analysis_results
from app.services.ranking import calculate_issue_rankings, save_issue_rankings
import logging

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("hourly_pulse")

async def run_analysis():
    """
    AI 분석과 랭킹을 실행합니다.
    """
    print("=" * 70)
    print("🤖 AI 분석 및 랭킹 실행")
    print("=" * 70)
    
    try:
        # 1. AI 분석 실행
        print("\n📊 [1] AI 분석 시작...")
        analysis_results = await analyze_collected_data(hours=24)  # 최근 24시간 데이터 분석
        
        if analysis_results:
            print(f"✅ AI 분석 완료: {len(analysis_results)}개 이슈 발견")
            
            # 분석 결과 저장
            saved_count = await save_analysis_results(analysis_results)
            print(f"💾 분석 결과 저장: {saved_count}개")
            
            # 상위 3개 이슈 출력
            sorted_results = sorted(analysis_results, key=lambda x: x.get('importance_score', 0), reverse=True)
            print("\n📊 주요 이슈 (상위 3개):")
            for i, result in enumerate(sorted_results[:3], 1):
                topic = result.get('topic', 'N/A')
                score = result.get('importance_score', 0)
                why_now = result.get('why_now', '')
                print(f"  {i}. {topic}")
                print(f"     중요도: {score:.2f}")
                if why_now:
                    print(f"     왜 지금: {why_now[:100]}...")
        else:
            print("⚠️ 분석 결과가 없습니다.")
        
        # 2. 이슈 랭킹 계산
        print("\n📊 [2] 이슈 랭킹 계산 시작...")
        rankings = await calculate_issue_rankings(hours=24)
        
        if rankings:
            saved_count = await save_issue_rankings(rankings, period_hours=24)
            print(f"✅ 이슈 랭킹 완료: {len(rankings)}개 이슈, {saved_count}개 저장됨")
            
            # 상위 5개 랭킹 출력
            print("\n🏆 주요 이슈 랭킹 (상위 5개):")
            for i, ranking in enumerate(rankings[:5], 1):
                topic = ranking.get('topic', 'N/A')
                score = ranking.get('score', 0)
                description = ranking.get('description', '')
                why_now = ranking.get('why_now', '')
                print(f"  {i}. {topic} (점수: {score:.2f})")
                if description:
                    print(f"     내용: {description[:100]}...")
                if why_now:
                    print(f"     왜 지금: {why_now[:100]}...")
        else:
            print("⚠️ 랭킹할 이슈가 없습니다.")
        
        print("\n" + "=" * 70)
        print("✅ 완료! 웹사이트를 새로고침하여 결과를 확인하세요.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_analysis())



