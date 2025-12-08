"""
API 엔드포인트 테스트
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    """
    API 엔드포인트를 테스트합니다.
    """
    print("=" * 70)
    print("🌐 API 엔드포인트 테스트")
    print("=" * 70)
    
    # 1. 루트 엔드포인트
    print("\n📋 [1] 루트 엔드포인트")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
        print("  (서버가 실행 중이지 않을 수 있습니다)")
    
    # 2. 통계 정보
    print("\n📊 [2] 통계 정보")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공:")
            print(f"  총 수집 데이터: {data.get('total_collected', 0)}개")
            print(f"  총 분석 결과: {data.get('total_analysis', 0)}개")
            print(f"  총 랭킹: {data.get('total_rankings', 0)}개")
            print(f"  소스별 통계: {data.get('source_counts', {})}")
        else:
            print(f"❌ 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 3. 최근 수집 데이터
    print("\n📰 [3] 최근 수집 데이터")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/recent?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 성공: {len(data)}개 아이템")
            for i, item in enumerate(data[:3], 1):
                print(f"  {i}. [{item.get('source_type')}] {item.get('title', 'N/A')[:50]}...")
        else:
            print(f"❌ 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 4. 이슈 랭킹
    print("\n🏆 [4] 이슈 랭킹")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/rankings?limit=5")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✅ 성공: {len(data)}개 랭킹")
                for ranking in data:
                    print(f"  {ranking.get('rank')}. {ranking.get('topic')}")
                    print(f"     점수: {ranking.get('score', 0):.3f} | 언급: {ranking.get('mention_count', 0)}회")
            else:
                print("⚠️ 랭킹 데이터가 없습니다.")
        else:
            print(f"❌ 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    # 5. 분석 결과
    print("\n🤖 [5] 분석 결과")
    print("-" * 70)
    try:
        response = requests.get(f"{BASE_URL}/api/analysis?limit=5")
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"✅ 성공: {len(data)}개 분석 결과")
                for i, analysis in enumerate(data[:3], 1):
                    print(f"  {i}. {analysis.get('topic', 'N/A')}")
                    print(f"     중요도: {analysis.get('importance_score', 0):.2f}")
            else:
                print("⚠️ 분석 결과가 없습니다.")
        else:
            print(f"❌ 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 오류: {e}")
    
    print("\n" + "=" * 70)
    print("✅ API 테스트 완료!")
    print("=" * 70)
    print("\n💡 서버를 실행하려면:")
    print("   .\\venv\\Scripts\\uvicorn.exe app.main:app --reload")

if __name__ == "__main__":
    test_api()




