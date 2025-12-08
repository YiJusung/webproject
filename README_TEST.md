# 테스트 가이드

이 프로젝트를 테스트하는 방법을 안내합니다.

## 테스트 방법

### 1. 전체 플로우 테스트 (권장)

전체 시스템을 한 번에 테스트합니다:
- 데이터 수집 → 저장 → AI 분석

```bash
.\venv\Scripts\python.exe test_full_flow.py
```

**테스트 내용:**
1. 데이터베이스 초기화
2. 데이터 수집 (Reddit, 뉴스, GitHub, YouTube)
3. 데이터베이스 저장
4. 저장된 데이터 확인
5. AI 분석 (Gemini API 사용)

### 2. 개별 컴포넌트 테스트

#### 데이터베이스 연결 테스트
```bash
.\venv\Scripts\python.exe db_test.py
```

#### 데이터 수집기 테스트
```bash
.\venv\Scripts\python.exe test_collector.py
```

### 3. FastAPI 서버 실행 (실시간 모니터링)

스케줄러가 자동으로 데이터를 수집하고 분석합니다:

```bash
.\venv\Scripts\uvicorn.exe app.main:app --reload
```

서버가 실행되면:
- 자동으로 데이터 수집 시작
- 10초마다 (테스트용) 또는 매시 정각 (프로덕션)에 실행
- 로그에서 진행 상황 확인 가능

## 환경 설정

### 필수 환경변수

`.env` 파일에 다음을 설정하세요:

```env
# 데이터베이스
DATABASE_URL=postgresql+psycopg://postgres:root@localhost:5433/hourly_pulse

# Gemini API (AI 분석용)
GEMINI_API_KEY=your_gemini_api_key_here
```

### Gemini API Key 발급

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 방문
2. API Key 생성
3. `.env` 파일에 추가

## 테스트 결과 확인

### 데이터베이스 확인

PostgreSQL에 접속하여 데이터 확인:

```sql
-- 수집된 데이터 확인
SELECT source_type, COUNT(*) FROM collected_items GROUP BY source_type;

-- 최근 수집 데이터 확인
SELECT source, title, collected_at 
FROM collected_items 
ORDER BY collected_at DESC 
LIMIT 10;

-- 분석 결과 확인
SELECT topic, importance_score, sentiment, analyzed_at 
FROM analysis_results 
ORDER BY importance_score DESC 
LIMIT 10;
```

### 로그 확인

테스트 실행 시 콘솔에 상세한 로그가 출력됩니다:
- ✅ 성공
- ⚠️ 경고
- ❌ 오류

## 문제 해결

### Gemini API 안전 필터 차단

만약 "안전 필터에 의해 차단되었습니다" 오류가 발생하면:
- 프롬프트가 너무 민감한 내용을 포함할 수 있습니다
- 코드의 `safety_settings`를 조정하거나
- 프롬프트를 더 중립적으로 수정하세요

### 데이터베이스 연결 실패

1. Docker 컨테이너가 실행 중인지 확인:
   ```bash
   docker ps
   ```

2. 포트가 올바른지 확인 (기본: 5433)

3. 데이터베이스가 생성되었는지 확인:
   ```bash
   docker exec -it hourly-pulse-db psql -U postgres -c "\l"
   ```

## 다음 단계

테스트가 성공하면:
1. API 엔드포인트 구현 (3단계)
2. 이슈 랭킹 시스템 구현 (4단계)
3. 웹 대시보드 구현 (선택)




