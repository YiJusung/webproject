"""
전체 플로우 테스트 스크립트
데이터 수집 → 저장 → AI 분석까지 전체 과정을 테스트합니다.
"""
import asyncio
import sys
import os
from app.services.unified_collector import collect_all_sources
from app.services.storage import save_all_collected_data, get_recent_items
from app.services.ai_analyzer import analyze_collected_data, save_analysis_results
from app.core.database import init_db

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_full_flow():
    """
    전체 플로우를 테스트합니다:
    1. 데이터베이스 초기화
    2. 데이터 수집
    3. 데이터 저장
    4. AI 분석
    5. 분석 결과 저장
    """
    print("=" * 70)
    print("🧪 전체 플로우 테스트 시작")
    print("=" * 70)
    
    # 0. 환경변수 확인
    print("\n📋 환경변수 확인:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print(f"  ✅ GEMINI_API_KEY: 설정됨 ({gemini_key[:10]}...)")
    else:
        print("  ⚠️  GEMINI_API_KEY: 설정되지 않음 (AI 분석은 건너뜁니다)")
    
    # 1. 데이터베이스 초기화
    print("\n🗄️  [1단계] 데이터베이스 초기화 중...")
    try:
        await init_db()
        print("  ✅ 데이터베이스 초기화 완료!")
    except Exception as e:
        print(f"  ❌ 데이터베이스 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 데이터 수집
    print("\n📥 [2단계] 데이터 수집 중...")
    try:
        collected_data = await collect_all_sources()
        
        print(f"\n  📊 수집된 데이터 요약:")
        total_items = 0
        for source, items in collected_data.items():
            if items:
                count = len(items)
                total_items += count
                print(f"    - {source}: {count}개")
        
        if total_items == 0:
            print("  ⚠️  수집된 데이터가 없습니다. 테스트를 종료합니다.")
            return
        
        print(f"\n  ✅ 총 {total_items}개 아이템 수집 완료!")
        
    except Exception as e:
        print(f"  ❌ 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 데이터 저장
    print("\n💾 [3단계] 데이터베이스에 저장 중...")
    try:
        save_results = await save_all_collected_data(collected_data)
        
        print(f"\n  💾 저장 결과:")
        total_saved = 0
        for source, count in save_results.items():
            if count > 0:
                total_saved += count
                print(f"    - {source}: {count}개 저장됨")
        
        print(f"\n  ✅ 총 {total_saved}개 아이템 저장 완료!")
        
    except Exception as e:
        print(f"  ❌ 데이터 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 저장된 데이터 확인
    print("\n📖 [4단계] 저장된 데이터 확인 중...")
    try:
        recent_items = await get_recent_items(limit=5)
        print(f"  ✅ 최근 저장된 {len(recent_items)}개 아이템:")
        for i, item in enumerate(recent_items[:3], 1):
            title = item.title[:60] + "..." if len(item.title) > 60 else item.title
            print(f"    {i}. [{item.source_type}] {item.source}: {title}")
    except Exception as e:
        print(f"  ⚠️  데이터 조회 실패: {e}")
    
    # 5. AI 분석 (Gemini API Key가 있는 경우만)
    if gemini_key:
        print("\n🤖 [5단계] AI 분석 시작...")
        try:
            analysis_results = await analyze_collected_data(hours=1)
            
            if analysis_results:
                print(f"  ✅ {len(analysis_results)}개 토픽 분석 완료!")
                
                # 분석 결과 저장
                saved_count = await save_analysis_results(analysis_results)
                print(f"  💾 {saved_count}개 분석 결과 저장됨")
                
                # 상위 5개 이슈 출력
                sorted_results = sorted(
                    analysis_results, 
                    key=lambda x: x.get('importance_score', 0), 
                    reverse=True
                )
                print(f"\n  📊 주요 이슈 (상위 5개):")
                for i, result in enumerate(sorted_results[:5], 1):
                    topic = result.get('topic', 'N/A')
                    score = result.get('importance_score', 0)
                    sources = result.get('source_count', 0)
                    sentiment = result.get('sentiment', 'neutral')
                    print(f"    {i}. {topic}")
                    print(f"       중요도: {score:.2f} | 소스: {sources}개 | 감정: {sentiment}")
                    if result.get('summary'):
                        summary = result['summary'][:80]
                        print(f"       요약: {summary}...")
                    print()
            else:
                print("  ⚠️  AI 분석 결과가 없습니다.")
                
        except Exception as e:
            print(f"  ❌ AI 분석 실패: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n🤖 [5단계] AI 분석 건너뜀 (GEMINI_API_KEY 미설정)")
    
    # 완료
    print("\n" + "=" * 70)
    print("✅ 전체 플로우 테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_full_flow())




