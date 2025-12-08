"""
기존 랭킹 데이터를 삭제하고 새로운 분석을 위한 스크립트
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from app.core.database import AsyncSessionLocal
from app.core.models import IssueRanking, AnalysisResult

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def clear_old_data():
    """
    기존 랭킹 데이터를 삭제하여 새로운 분석이 실행되도록 합니다.
    """
    print("=" * 70)
    print("🗑️  기존 데이터 정리")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # 기존 랭킹 데이터 삭제
            result = await session.execute(delete(IssueRanking))
            deleted_rankings = result.rowcount
            print(f"✅ 삭제된 랭킹 데이터: {deleted_rankings}개")
            
            # 기존 분석 결과도 삭제 (선택사항 - 주석 해제하면 실행)
            # result = await session.execute(delete(AnalysisResult))
            # deleted_analysis = result.rowcount
            # print(f"✅ 삭제된 분석 결과: {deleted_analysis}개")
            
            await session.commit()
            print("\n" + "=" * 70)
            print("✅ 데이터 정리 완료!")
            print("=" * 70)
            print("\n💡 다음 스케줄러 실행 시 새로운 분석과 랭킹이 생성됩니다.")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ 데이터 정리 실패: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clear_old_data())



