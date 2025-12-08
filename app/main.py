from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import apscheduler.events
import logging
import sys
import asyncio
from datetime import datetime
from app.services.unified_collector import collect_all_sources
from app.services.storage import save_all_collected_data
from app.services.ai_analyzer import analyze_collected_data, save_analysis_results
from app.services.ranking import calculate_issue_rankings, save_issue_rankings, get_top_rankings
from app.core.database import init_db

# Windows에서 SelectorEventLoop 사용 (ProactorEventLoop 대신)
import selectors
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # 현재 이벤트 루프가 ProactorEventLoop이면 닫고 새로 생성
    try:
        loop = asyncio.get_event_loop()
        if isinstance(loop, asyncio.ProactorEventLoop):
            loop.close()
            asyncio.set_event_loop(asyncio.SelectorEventLoop(selectors.SelectSelector()))
    except RuntimeError:
        # 실행 중인 이벤트 루프가 없으면 새로 생성
        asyncio.set_event_loop(asyncio.SelectorEventLoop(selectors.SelectSelector()))

def ensure_selector_event_loop():
    """
    Windows에서 SelectorEventLoop를 보장하는 헬퍼 함수
    """
    if sys.platform == 'win32':
        try:
            loop = asyncio.get_running_loop()
            if isinstance(loop, asyncio.ProactorEventLoop):
                logger.warning("⚠️ ProactorEventLoop 감지됨. SelectorEventLoop로 변경 시도...")
                # 실행 중인 루프는 변경할 수 없으므로 경고만 출력
                logger.warning("⚠️ 실행 중인 이벤트 루프는 변경할 수 없습니다.")
        except RuntimeError:
            # 실행 중인 이벤트 루프가 없으면 정책만 확인
            pass

# 1. 로깅 설정 (콘솔에 로그가 예쁘게 찍히도록 설정)
# 개발 단계에서는 INFO 레벨로 설정해서 진행 상황을 눈으로 확인합니다.
import sys as sys_module

# 기존 핸들러 제거
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# 즉시 출력되는 핸들러 생성 (버퍼링 없음)
console_handler = logging.StreamHandler(sys_module.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))
# 버퍼링 비활성화
console_handler.stream.reconfigure(line_buffering=True) if hasattr(console_handler.stream, 'reconfigure') else None

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[console_handler],
    force=True  # 기존 설정 덮어쓰기
)

logger = logging.getLogger("hourly_pulse")
logger.setLevel(logging.INFO)
# propagate를 True로 설정하여 상위 로거로 전파
logger.propagate = True

# uvicorn 로거도 설정
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.INFO)
uvicorn_logger.propagate = True

# apscheduler 로거도 설정
apscheduler_logger = logging.getLogger("apscheduler")
apscheduler_logger.setLevel(logging.INFO)
apscheduler_logger.propagate = True

# 모든 하위 로거도 INFO 레벨로 설정
logging.getLogger("app").setLevel(logging.INFO)
logging.getLogger("app.services").setLevel(logging.INFO)
logging.getLogger("app.core").setLevel(logging.INFO)

# 2. 스케줄러 인스턴스 생성
# AsyncIOScheduler는 FastAPI의 비동기 방식과 찰떡궁합입니다.
# Windows 호환성을 위해 이벤트 루프를 명시적으로 설정
scheduler = AsyncIOScheduler(
    timezone="UTC",
    coalesce=True,  # 여러 작업이 밀렸을 때 하나로 합침
    max_instances=3,  # 동시에 실행될 수 있는 최대 인스턴스 수
    job_defaults={
        'coalesce': True,
        'max_instances': 3,
        'misfire_grace_time': 30
    }
)

# 스케줄러 이벤트 리스너 추가 (디버깅용)
def job_executed_listener(event):
    logger.info(f"✅ 작업 실행 완료: {event.job_id}")

def job_error_listener(event):
    logger.error(f"❌ 작업 실행 오류: {event.job_id}, 오류: {event.exception}")

scheduler.add_listener(job_executed_listener, apscheduler.events.EVENT_JOB_EXECUTED)
scheduler.add_listener(job_error_listener, apscheduler.events.EVENT_JOB_ERROR)

# 3. 주기적으로 실행될 작업 함수 (Job)
async def job_collection_task():
    """
    스케줄러에 의해 주기적으로 실행되는 작업 함수입니다.
    모든 데이터 소스에서 정보를 수집합니다.
    """
    # 작업 함수 진입 확인 로그 (가장 먼저 출력)
    logger.info("=" * 60)
    logger.info("🎯 작업 함수 실행 시작!")
    sys_module.stdout.flush()  # 즉시 출력 보장
    
    # 이벤트 루프 확인 및 로깅
    try:
        loop = asyncio.get_running_loop()
        logger.info(f"🔄 작업 실행 - 이벤트 루프: {type(loop).__name__}")
        sys_module.stdout.flush()
        if sys.platform == 'win32' and isinstance(loop, asyncio.ProactorEventLoop):
            logger.error("❌ ProactorEventLoop가 감지되었습니다! psycopg와 호환되지 않습니다.")
            sys_module.stdout.flush()
    except RuntimeError:
        pass
    
    logger.info(f"🚀 [Scheduler] 정기 작업 실행 중... 현재 시간: {datetime.now()}")
    sys_module.stdout.flush()  # 즉시 출력 보장
    
    # 통합 수집기 호출
    logger.info("📥 데이터 수집 시작...")
    sys_module.stdout.flush()
    collected_data = await collect_all_sources()
    logger.info(f"✅ 데이터 수집 완료: {sum(len(items) for items in collected_data.values())}개 아이템")
    sys_module.stdout.flush()
    
    # 수집된 데이터 요약 출력
    logger.info("=" * 60)
    logger.info("📊 수집된 데이터 요약")
    logger.info("=" * 60)
    
    for source, items in collected_data.items():
        if items:
            logger.info(f"📌 {source.upper()}: {len(items)}개")
            # 각 소스별로 상위 3개만 출력
            for i, item in enumerate(items[:3], 1):
                title = item.get("title", "N/A")
                if len(title) > 50:
                    title = title[:47] + "..."
                logger.info(f"  {i}. {title}")
    
    logger.info("=" * 60)
    
    # 데이터베이스에 저장
    try:
        save_results = await save_all_collected_data(collected_data)
        logger.info("💾 저장 결과:")
        for source, count in save_results.items():
            if count > 0:
                logger.info(f"  - {source}: {count}개 저장됨")
    except Exception as e:
        logger.error(f"❌ 데이터 저장 실패: {type(e).__name__} - {e}")
    
    # AI 분석 수행
    try:
        logger.info("🤖 AI 분석 시작...")
        analysis_results = await analyze_collected_data(hours=1)
        
        if analysis_results:
            # 분석 결과 저장
            saved_count = await save_analysis_results(analysis_results)
            logger.info(f"🤖 AI 분석 완료: {len(analysis_results)}개 토픽 분석, {saved_count}개 저장됨")
            
            # 상위 3개 이슈 출력
            sorted_results = sorted(analysis_results, key=lambda x: x.get('importance_score', 0), reverse=True)
            logger.info("📊 주요 이슈 (상위 3개):")
            for i, result in enumerate(sorted_results[:3], 1):
                topic = result.get('topic', 'N/A')
                score = result.get('importance_score', 0)
                sources = result.get('source_count', 0)
                logger.info(f"  {i}. {topic} (중요도: {score:.2f}, 소스: {sources}개)")
        else:
            logger.warning("⚠️ AI 분석 결과가 없습니다.")
    except Exception as e:
        logger.error(f"❌ AI 분석 실패: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
    
    # 이슈 랭킹 계산 및 저장
    try:
        logger.info("📊 이슈 랭킹 계산 시작...")
        rankings = await calculate_issue_rankings(hours=1)
        
        if rankings:
            saved_count = await save_issue_rankings(rankings, period_hours=1)
            logger.info(f"📊 이슈 랭킹 완료: {len(rankings)}개 이슈, {saved_count}개 저장됨")
            
            # 상위 5개 랭킹 출력
            logger.info("🏆 주요 이슈 랭킹 (상위 5개):")
            for i, ranking in enumerate(rankings[:5], 1):
                topic = ranking.get('topic', 'N/A')
                score = ranking.get('score', 0)
                mentions = ranking.get('mention_count', 0)
                sources = ranking.get('source_diversity', 0)
                logger.info(f"  {i}. {topic} (점수: {score:.2f}, 언급: {mentions}회, 소스: {sources}개)")
        else:
            logger.warning("⚠️ 랭킹할 이슈가 없습니다.")
    except Exception as e:
        logger.error(f"❌ 이슈 랭킹 실패: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()

# 4. Lifespan (수명주기) 관리자
# 서버가 켜질 때(Start)와 꺼질 때(Shutdown) 할 일을 정의합니다.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # [시작 시 실행]
    logger.info("✅ 서버 시작! 스케줄러를 가동합니다.")
    sys_module.stdout.flush()
    
    # 데이터베이스 초기화 (테이블 생성)
    logger.info("💾 데이터베이스 초기화 시작...")
    sys_module.stdout.flush()
    try:
        logger.info("🔄 데이터베이스 연결 시도 중...")
        sys_module.stdout.flush()
        # 타임아웃 설정 (10초)
        await asyncio.wait_for(init_db(), timeout=10.0)
        logger.info("✅ 데이터베이스 초기화 완료!")
        sys_module.stdout.flush()
    except asyncio.TimeoutError:
        logger.error("❌ 데이터베이스 초기화 타임아웃 (10초 초과)")
        sys_module.stdout.flush()
        logger.warning("⚠️ 데이터베이스 연결 없이 서버를 계속 실행합니다.")
        sys_module.stdout.flush()
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {type(e).__name__} - {e}")
        sys_module.stdout.flush()
        import traceback
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        sys_module.stdout.flush()
        logger.warning("⚠️ 데이터베이스 연결 없이 서버를 계속 실행합니다.")
        sys_module.stdout.flush()
        # 데이터베이스 초기화 실패해도 서버는 계속 실행
    
    # 현재 실행 중인 이벤트 루프 가져오기
    logger.info("🔄 이벤트 루프 확인 중...")
    sys_module.stdout.flush()
    loop = asyncio.get_running_loop()
    logger.info(f"🔄 이벤트 루프: {type(loop).__name__}")
    sys_module.stdout.flush()
    
    # 스케줄러에 작업 등록 (스케줄러 시작 전에 등록)
    logger.info("📝 스케줄러에 작업 등록 중...")
    sys_module.stdout.flush()
    # trigger='interval', minutes=5 -> 5분마다 실행 (테스트용)
    scheduler.add_job(
        job_collection_task, 
        "interval", 
        minutes=5, 
        id="hourly_collection",
        replace_existing=True,
        misfire_grace_time=300  # 작업이 지연되어도 5분 내에는 실행
    )
    logger.info("✅ 작업 등록 완료")
    sys_module.stdout.flush()
    
    # 스케줄러 시작 (현재 이벤트 루프 사용)
    logger.info("🚀 스케줄러 시작 준비 중...")
    sys_module.stdout.flush()
    # Windows에서 SelectorEventLoop를 보장
    if sys.platform == 'win32':
        try:
            current_loop = asyncio.get_running_loop()
            if isinstance(current_loop, asyncio.ProactorEventLoop):
                logger.error("❌ ProactorEventLoop가 감지되었습니다! 스케줄러를 시작할 수 없습니다.")
                sys_module.stdout.flush()
                raise RuntimeError("ProactorEventLoop는 psycopg와 호환되지 않습니다.")
            logger.info(f"✅ 올바른 이벤트 루프 확인: {type(current_loop).__name__}")
            sys_module.stdout.flush()
        except RuntimeError:
            pass
    
    try:
        # 스케줄러를 현재 이벤트 루프에서 시작
        logger.info("▶️ 스케줄러 시작 중...")
        sys_module.stdout.flush()
        scheduler.start()
        logger.info(f"📅 스케줄러 시작됨! 실행 상태: {scheduler.running}")
        sys_module.stdout.flush()
        
        # 스케줄러가 제대로 시작되었는지 확인
        if not scheduler.running:
            logger.error("❌ 스케줄러가 시작되지 않았습니다!")
            raise RuntimeError("스케줄러 시작 실패")
            
    except Exception as e:
        logger.error(f"❌ 스케줄러 시작 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    # 작업 정보 확인
    logger.info("🔍 작업 정보 확인 중...")
    sys_module.stdout.flush()
    await asyncio.sleep(0.1)  # 스케줄러가 완전히 시작될 때까지 잠시 대기
    job = scheduler.get_job("hourly_collection")
    if job:
        logger.info(f"⏰ 다음 실행 예정 시간: {job.next_run_time}")
        logger.info(f"📋 등록된 작업 수: {len(scheduler.get_jobs())}")
        sys_module.stdout.flush()
    else:
        logger.warning("⚠️ 작업이 등록되지 않았습니다! 다시 등록 시도...")
        sys_module.stdout.flush()
        # 작업이 없으면 다시 등록
        scheduler.add_job(
            job_collection_task, 
            "interval", 
            minutes=5, 
            id="hourly_collection",
            replace_existing=True
        )
        logger.info("✅ 작업 재등록 완료")
        sys_module.stdout.flush()
    
    # 첫 번째 작업을 즉시 실행 (테스트용)
    logger.info("🔧 첫 번째 작업을 즉시 실행합니다...")
    sys_module.stdout.flush()  # 즉시 출력 보장
    # 작업 실행 후 로그가 출력되도록 ensure_future 사용
    task = asyncio.ensure_future(job_collection_task())
    logger.info(f"📌 작업 태스크 생성됨: {task}")
    sys_module.stdout.flush()  # 즉시 출력 보장
    logger.info("⏳ 작업 실행 대기 중... (로그가 곧 출력됩니다)")
    sys_module.stdout.flush()  # 즉시 출력 보장
    logger.info("✅ 서버 초기화 완료! API 서버가 시작됩니다...")
    sys_module.stdout.flush()
    
    yield # 이 시점에서 API 서버가 작동합니다 (무한 대기)
    
    # [종료 시 실행]
    logger.info("🛑 서버 종료! 스케줄러를 멈춥니다.")
    if scheduler.running:
        scheduler.shutdown(wait=True)

# 5. FastAPI 앱 생성
app = FastAPI(
    title="Hourly Pulse API",
    version="0.1.0",
    description="여러 소스의 정보를 수집하고 AI로 분석하여 주요 이슈를 제공하는 API",
    lifespan=lifespan # 위에서 만든 수명주기 관리자를 등록
)

# CORS 설정 (프론트엔드 접근 허용)
# 개발 환경: 모든 origin 허용 (ngrok, 로컬 네트워크 등 포함)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발 환경)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
from app.api.endpoints import router
app.include_router(router, prefix="/api", tags=["API"])

# 6. 헬스 체크용 API
@app.get("/health")
async def health_check():
    """
    서버가 살아있는지, 스케줄러가 돌고 있는지 확인하는 용도
    """
    job = scheduler.get_job("hourly_collection")
    next_run = job.next_run_time if job else "No Job"
    
    return {
        "status": "ok",
        "scheduler_running": scheduler.running,
        "next_job_run": next_run
    }