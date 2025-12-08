"""
데이터베이스 마이그레이션 스크립트
새로 추가된 컬럼들을 데이터베이스에 추가합니다.
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

async def migrate_database():
    """
    데이터베이스에 새 컬럼을 추가합니다.
    """
    print("=" * 70)
    print("🗄️  데이터베이스 마이그레이션 시작")
    print("=" * 70)
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    try:
        async with engine.begin() as conn:
            print("\n📊 [1] analysis_results 테이블 마이그레이션")
            print("-" * 70)
            
            # analysis_results 테이블에 새 컬럼 추가
            migrations = [
                # what 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='analysis_results' AND column_name='what'
                    ) THEN
                        ALTER TABLE analysis_results ADD COLUMN what TEXT;
                        RAISE NOTICE 'Added column: what';
                    ELSE
                        RAISE NOTICE 'Column what already exists';
                    END IF;
                END $$;
                """,
                # why_now 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='analysis_results' AND column_name='why_now'
                    ) THEN
                        ALTER TABLE analysis_results ADD COLUMN why_now TEXT;
                        RAISE NOTICE 'Added column: why_now';
                    ELSE
                        RAISE NOTICE 'Column why_now already exists';
                    END IF;
                END $$;
                """,
                # context 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='analysis_results' AND column_name='context'
                    ) THEN
                        ALTER TABLE analysis_results ADD COLUMN context TEXT;
                        RAISE NOTICE 'Added column: context';
                    ELSE
                        RAISE NOTICE 'Column context already exists';
                    END IF;
                END $$;
                """,
            ]
            
            for i, migration in enumerate(migrations, 1):
                try:
                    await conn.execute(text(migration))
                    print(f"  ✅ 마이그레이션 {i} 완료")
                except Exception as e:
                    print(f"  ⚠️  마이그레이션 {i} 오류: {e}")
            
            print("\n📊 [2] issue_rankings 테이블 마이그레이션")
            print("-" * 70)
            
            # issue_rankings 테이블에 새 컬럼 추가
            ranking_migrations = [
                # description 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='issue_rankings' AND column_name='description'
                    ) THEN
                        ALTER TABLE issue_rankings ADD COLUMN description TEXT;
                        RAISE NOTICE 'Added column: description';
                    ELSE
                        RAISE NOTICE 'Column description already exists';
                    END IF;
                END $$;
                """,
                # what 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='issue_rankings' AND column_name='what'
                    ) THEN
                        ALTER TABLE issue_rankings ADD COLUMN what TEXT;
                        RAISE NOTICE 'Added column: what';
                    ELSE
                        RAISE NOTICE 'Column what already exists';
                    END IF;
                END $$;
                """,
                # why_now 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='issue_rankings' AND column_name='why_now'
                    ) THEN
                        ALTER TABLE issue_rankings ADD COLUMN why_now TEXT;
                        RAISE NOTICE 'Added column: why_now';
                    ELSE
                        RAISE NOTICE 'Column why_now already exists';
                    END IF;
                END $$;
                """,
                # context 컬럼 추가
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='issue_rankings' AND column_name='context'
                    ) THEN
                        ALTER TABLE issue_rankings ADD COLUMN context TEXT;
                        RAISE NOTICE 'Added column: context';
                    ELSE
                        RAISE NOTICE 'Column context already exists';
                    END IF;
                END $$;
                """,
            ]
            
            for i, migration in enumerate(ranking_migrations, 1):
                try:
                    await conn.execute(text(migration))
                    print(f"  ✅ 마이그레이션 {i} 완료")
                except Exception as e:
                    print(f"  ⚠️  마이그레이션 {i} 오류: {e}")
            
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
    asyncio.run(migrate_database())



