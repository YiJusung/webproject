"""
collector.py를 직접 테스트하는 스크립트입니다.
"""
import asyncio
import sys
import logging
from app.services.collector import fetch_google_trends

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

async def main():
    print("=" * 50)
    print("구글 트렌드 수집기 테스트")
    print("=" * 50)
    
    trends = await fetch_google_trends()
    
    if trends:
        print(f"\n🔥 [실시간 인기 검색어 TOP {len(trends)}] 🔥")
        for i, keyword in enumerate(trends, 1):
            print(f"  {i}. {keyword}")
        print("-" * 50)
    else:
        print("\n⚠️ 수집된 트렌드가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())


