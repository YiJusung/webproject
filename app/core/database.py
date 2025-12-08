"""
데이터베이스 연결 및 세션 관리
"""
import os
import sys
import asyncio
import selectors
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Windows에서 SelectorEventLoop 사용 (ProactorEventLoop 대신)
# psycopg는 ProactorEventLoop를 사용할 수 없으므로 반드시 SelectorEventLoop를 사용해야 함
if sys.platform == 'win32':
    # 이벤트 루프 정책을 먼저 설정
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # 현재 이벤트 루프가 ProactorEventLoop이면 닫고 새로 생성
    try:
        loop = asyncio.get_event_loop()
        if isinstance(loop, asyncio.ProactorEventLoop):
            loop.close()
            # SelectorEventLoop로 새 이벤트 루프 생성
            asyncio.set_event_loop(asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except RuntimeError:
        # 실행 중인 이벤트 루프가 없으면 새로 생성
        asyncio.set_event_loop(asyncio.SelectorEventLoop(selectors.SelectSelector()))

load_dotenv()

# 데이터베이스 URL 설정
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

# 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base 클래스
Base = declarative_base()


async def init_db():
    """
    데이터베이스 테이블을 생성합니다.
    """
    from app.core.models import CollectedItem, AnalysisResult, IssueRanking
    
    # 이벤트 루프가 올바르게 설정되었는지 확인
    if sys.platform == 'win32':
        try:
            loop = asyncio.get_running_loop()
            if isinstance(loop, asyncio.ProactorEventLoop):
                raise RuntimeError(
                    "ProactorEventLoop는 psycopg와 호환되지 않습니다. "
                    "SelectorEventLoop를 사용하세요."
                )
        except RuntimeError:
            # 실행 중인 이벤트 루프가 없으면 정책만 확인
            pass
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
