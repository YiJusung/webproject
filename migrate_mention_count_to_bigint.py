"""
데이터베이스 마이그레이션: mention_count 컬럼을 INTEGER에서 BIGINT로 변경
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

# 데이터베이스 URL 설정
env_url = os.getenv("DATABASE_URL")
if env_url:
    if "asyncpg" in env_url:
        env_url = env_url.replace("asyncpg", "psycopg")
    if ":5432/" in env_url:
        env_url = env_url.replace(":5432/", ":5433/")
    DATABASE_URL = env_url
else:
    DATABASE_URL = "postgresql+psycopg://postgres:root@localhost:5433/hourly_pulse"

async def migrate():
    """mention_count 컬럼을 BIGINT로 변경"""
    print("=" * 70)
    print("🗄️  mention_count 컬럼 마이그레이션 시작")
    print("=" * 70)
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    try:
        async with engine.begin() as conn:
            print("\n📊 issue_rankings.mention_count 컬럼을 BIGINT로 변경")
            print("-" * 70)
            
            # mention_count 컬럼을 BIGINT로 변경
            migration = """
            DO $$ 
            BEGIN
                -- 현재 컬럼 타입 확인
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='issue_rankings' AND column_name='mention_count'
                ) THEN
                    -- INTEGER에서 BIGINT로 변경
                    ALTER TABLE issue_rankings 
                    ALTER COLUMN mention_count TYPE BIGINT;
                    RAISE NOTICE 'Changed mention_count column type from INTEGER to BIGINT';
                ELSE
                    RAISE NOTICE 'Column mention_count does not exist';
                END IF;
            END $$;
            """
            
            try:
                await conn.execute(text(migration))
                print("  ✅ mention_count 컬럼이 BIGINT로 성공적으로 변경되었습니다.")
            except Exception as e:
                print(f"  ⚠️  마이그레이션 오류: {e}")
                raise
            
            print("\n" + "=" * 70)
            print("✅ 데이터베이스 마이그레이션 완료!")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())

