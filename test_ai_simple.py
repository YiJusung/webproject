"""
간단한 테스트 데이터로 AI 분석 기능 테스트
"""
import asyncio
import sys
import os
from app.services.ai_analyzer import analyze_text_with_ai

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_ai_simple():
    """
    간단한 테스트 데이터로 AI 분석 기능을 테스트합니다.
    """
    print("=" * 70)
    print("🧪 AI 분석 기능 간단 테스트")
    print("=" * 70)
    
    # 환경변수 확인
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return
    
    print(f"✅ GEMINI_API_KEY: 설정됨 ({gemini_key[:10]}...)\n")
    
    # 테스트 데이터 1: 기술 뉴스
    print("📰 [테스트 1] 기술 뉴스 분석")
    print("-" * 70)
    tech_news = """
    제목: 새로운 AI 모델 출시
    내용: 최근 OpenAI에서 새로운 언어 모델을 출시했습니다. 이 모델은 이전 버전보다 더 빠르고 효율적입니다.
    
    제목: Python 3.12 업데이트
    내용: Python 3.12 버전이 출시되었으며, 성능 개선과 새로운 기능이 추가되었습니다.
    
    제목: 클라우드 서비스 가격 인하
    내용: 주요 클라우드 서비스 제공업체들이 서비스 가격을 인하했습니다.
    """
    
    result1 = await analyze_text_with_ai(tech_news, "summary")
    if result1:
        print("✅ 분석 성공!")
        print(f"  주요 이슈: {result1.get('topics', [])}")
        print(f"  요약: {result1.get('summary', 'N/A')[:100]}...")
        print(f"  키워드: {result1.get('keywords', [])}")
        print(f"  감정: {result1.get('sentiment', 'N/A')}")
    else:
        print("❌ 분석 실패")
    print()
    
    # 테스트 데이터 2: 일반 뉴스
    print("📰 [테스트 2] 일반 뉴스 분석")
    print("-" * 70)
    general_news = """
    제목: 날씨 예보
    내용: 내일 전국에 맑은 날씨가 예상됩니다. 기온은 평년과 비슷한 수준입니다.
    
    제목: 경제 지표 발표
    내용: 이번 달 경제 지표가 발표되었으며, 전반적으로 안정적인 성장세를 보이고 있습니다.
    
    제목: 교육 정책 발표
    내용: 새로운 교육 정책이 발표되었으며, 학생들의 학습 환경 개선에 중점을 두고 있습니다.
    """
    
    result2 = await analyze_text_with_ai(general_news, "summary")
    if result2:
        print("✅ 분석 성공!")
        print(f"  주요 이슈: {result2.get('topics', [])}")
        print(f"  요약: {result2.get('summary', 'N/A')[:100]}...")
        print(f"  키워드: {result2.get('keywords', [])}")
        print(f"  감정: {result2.get('sentiment', 'N/A')}")
    else:
        print("❌ 분석 실패")
    print()
    
    # 테스트 데이터 3: 키워드 추출
    print("🔑 [테스트 3] 키워드 추출")
    print("-" * 70)
    keywords_text = """
    제목: 스마트폰 신제품 출시
    내용: 새로운 스마트폰이 출시되었으며, 카메라 성능과 배터리 수명이 크게 개선되었습니다.
    """
    
    result3 = await analyze_text_with_ai(keywords_text, "keywords")
    if result3:
        print("✅ 키워드 추출 성공!")
        print(f"  키워드: {result3.get('keywords', [])}")
        print(f"  주요 주제: {result3.get('topics', [])}")
    else:
        print("❌ 키워드 추출 실패")
    print()
    
    print("=" * 70)
    print("✅ AI 분석 기능 테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_ai_simple())




