import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Windows에서 SelectorEventLoop 사용 (ProactorEventLoop 대신)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# .env 파일 로드
load_dotenv()

# .env 파일의 DATABASE_URL이 있으면 사용, 없으면 psycopg 사용
env_url = os.getenv("DATABASE_URL")
if env_url:
    # asyncpg를 psycopg로 변경하고 포트를 5433으로 변경
    if "asyncpg" in env_url:
        env_url = env_url.replace("asyncpg", "psycopg")
    # 포트를 5433으로 변경
    if ":5432/" in env_url:
        env_url = env_url.replace(":5432/", ":5433/")
    DATABASE_URL = env_url
else:
    DATABASE_URL = "postgresql+psycopg://postgres:root@localhost:5433/hourly_pulse"

async def test_connection():
    print(f"🔌 접속 시도 중... URL: {DATABASE_URL}")
    
    # 엔진 생성 (연결 풀 설정 추가)
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,
        pool_pre_ping=True,  # 연결이 끊어졌는지 확인
        pool_size=5,
        max_overflow=10
    )
    
    try:
        async with engine.connect() as conn:
            # 간단한 쿼리 실행 (SELECT 1)
            result = await conn.execute(text("SELECT 1"))
            print("✅ 데이터베이스 연결 성공! 결과:", result.scalar())
    except Exception as e:
        print("❌ 연결 실패:", e)
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())