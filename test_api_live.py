"""
실시간 API 테스트
서버가 실행 중일 때 API를 테스트합니다.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_live():
    """
    실행 중인 서버의 API를 테스트합니다.
    """
    print("=" * 70)
    print("🌐 실시간 API 테스트")
    print("=" * 70)
    
    # 1. 루트 엔드포인트
    print("\n📋 [1] 루트 엔드포인트")
    print("-" * 70)
    try:
        r = requests.get(f"{BASE_URL}/api/")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ 성공: {data['message']}")
            print(f"   버전: {data['version']}")
        else:
            print(f"❌ 실패: {r.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
        return
    
    # 2. 통계 정보
    print("\n📊 [2] 통계 정보")
    print("-" * 70)
    try:
        r = requests.get(f"{BASE_URL}/api/stats")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ 성공:")
            print(f"   총 수집 데이터: {data.get('total_collected', 0)}개")
            print(f"   총 분석 결과: {data.get('total_analysis', 0)}개")
            print(f"   총 랭킹: {data.get('total_rankings', 0)}개")
            print(f"   소스별 통계:")
            for source, count in data.get('source_counts', {}).items():
                print(f"     - {source}: {data.get('source_counts', {}).get(source, 0)}개")
        else:
            print(f"❌ 실패: {r.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 3. 최근 수집 데이터
    print("\n📰 [3] 최근 수집 데이터 (상위 5개)")
    print("-" * 70)
    try:
        r = requests.get(f"{BASE_URL}/api/recent?limit=5")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ 성공: {len(data)}개 아이템")
            for i, item in enumerate(data[:5], 1):
                title = item.get('title', 'N/A')
                if len(title) > 50:
                    title = title[:47] + "..."
                print(f"   {i}. [{item.get('source_type')}] {item.get('source')}: {title}")
        else:
            print(f"❌ 실패: {r.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 4. 이슈 랭킹
    print("\n🏆 [4] 이슈 랭킹 (상위 5개)")
    print("-" * 70)
    try:
        r = requests.get(f"{BASE_URL}/api/rankings?limit=5")
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"✅ 성공: {len(data)}개 랭킹")
                for rank in data:
                    print(f"   {rank.get('rank')}. {rank.get('topic')}")
                    print(f"      점수: {rank.get('score', 0):.3f} | 언급: {rank.get('mention_count', 0)}회")
            else:
                print("⚠️  랭킹 데이터가 없습니다.")
        else:
            print(f"❌ 실패: {r.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 5. 분석 결과
    print("\n🤖 [5] 분석 결과 (상위 5개)")
    print("-" * 70)
    try:
        r = requests.get(f"{BASE_URL}/api/analysis?limit=5")
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"✅ 성공: {len(data)}개 분석 결과")
                for i, analysis in enumerate(data[:5], 1):
                    print(f"   {i}. {analysis.get('topic', 'N/A')}")
                    print(f"      중요도: {analysis.get('importance_score', 0):.2f}")
            else:
                print("⚠️  분석 결과가 없습니다.")
        else:
            print(f"❌ 실패: {r.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 6. 스케줄러 상태 확인 (로그 확인용)
    print("\n⏰ [6] 스케줄러 정보")
    print("-" * 70)
    print("   현재 수집 간격: 10초 (테스트용)")
    print("   서버가 실행 중이며 자동으로 데이터를 수집합니다.")
    print("   로그를 확인하여 수집 진행 상황을 볼 수 있습니다.")
    
    print("\n" + "=" * 70)
    print("✅ API 테스트 완료!")
    print("=" * 70)
    print("\n💡 추가 정보:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - 서버 중지: Ctrl+C")

if __name__ == "__main__":
    test_api_live()




