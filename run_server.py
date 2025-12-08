"""
서버 실행 스크립트 (Windows 이벤트 루프 문제 해결)
"""
import sys
import asyncio
import selectors
import uvicorn

# Windows에서 SelectorEventLoop 사용 (ProactorEventLoop 대신)
# psycopg는 ProactorEventLoop를 사용할 수 없으므로 반드시 SelectorEventLoop를 사용해야 함
if sys.platform == 'win32':
    # 이벤트 루프 정책 설정
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # DeprecationWarning을 피하기 위해 get_event_loop() 대신 new_event_loop() 사용
    try:
        loop = asyncio.get_running_loop()
        # 실행 중인 루프가 있으면 그대로 사용
    except RuntimeError:
        # 실행 중인 이벤트 루프가 없으면 새로 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

if __name__ == "__main__":
    # Windows에서 SelectorEventLoop를 사용하도록 설정
    # uvicorn.run()은 loop_factory를 지원하지 않으므로
    # 이벤트 루프 정책만 설정하고 uvicorn이 자동으로 사용하도록 함
    import logging
    
    # uvicorn 로그 레벨 설정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="asyncio",
        log_level="info"  # uvicorn 로그 레벨 명시
    )



