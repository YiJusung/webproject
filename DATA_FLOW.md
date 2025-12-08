# 정보 수집 및 AI 가공 흐름

## 전체 프로세스 개요

```
[스케줄러] → [데이터 수집] → [데이터 저장] → [AI 분석] → [랭킹 계산] → [API 제공]
```

---

## 1단계: 스케줄러 시작 (app/main.py)

**위치**: `app/main.py` - `job_collection_task()`

**실행 주기**: 
- 서버 시작 시 즉시 1회 실행
- 이후 매 시간마다 자동 실행 (APScheduler)

**주요 작업**:
```python
async def job_collection_task():
    # 1. 데이터 수집
    collected_data = await collect_all_sources()
    
    # 2. 데이터베이스 저장
    save_results = await save_all_collected_data(collected_data)
    
    # 3. AI 분석
    analysis_results = await analyze_collected_data(hours=1)
    
    # 4. 랭킹 계산
    rankings = await calculate_issue_rankings(hours=1)
```

---

## 2단계: 데이터 수집 (app/services/unified_collector.py)

**위치**: `app/services/unified_collector.py` - `collect_all_sources()`

**수집 소스** (4K RPM 활용, 대량 수집):

### 2-1. Reddit 수집
- **Reddit Popular**: 50개 인기 게시물
- **Reddit 서브레딧**: 10개 서브레딧 × 50개 = 500개 게시물
  - worldnews, technology, korea, news, programming, science, business, politics, entertainment, gaming

### 2-2. 뉴스 수집
- **13개 뉴스 소스** × 50개 = 650개 기사
  - BBC, NYTimes, CBC, WashingtonPost, TheGuardian
  - HackerNews, TechCrunch, TheVerge, Wired, ArsTechnica, Engadget
  - Bloomberg

### 2-3. GitHub 수집
- **GitHub Trending**: 100개 저장소
  - 최근 7일간 생성된 저장소 중 스타가 많은 순

### 2-4. YouTube 수집
- **YouTube Trending**: 50개 동영상
  - 한국 지역 인기 동영상

**총 수집량**: 약 1,300개 이상의 아이템

**수집 데이터 구조**:
```python
{
    "source": "소스 이름",
    "title": "제목",
    "content": "내용/설명",
    "url": "원본 URL",
    "upvotes": 0,  # Reddit
    "stars": 0,    # GitHub
    "views": 0,    # YouTube
    "collected_at": "2025-12-08T10:00:00"
}
```

---

## 3단계: 데이터 저장 (app/services/storage.py)

**위치**: `app/services/storage.py` - `save_collected_items()`

**저장 프로세스**:

### 3-1. 디스크 용량 관리
- 현재 DB 크기 확인
- 800GB의 80% (640GB) 초과 시 오래된 데이터 삭제
- 목표: 70% (560GB)까지 삭제하여 여유 공간 확보

### 3-2. 아이템 개수 관리
- 최대 저장 개수: 50,000개
- 초과 시 가장 오래된 데이터부터 삭제

### 3-3. 데이터 저장
- **중복 체크 없음**: 모든 수집 데이터 저장
- `CollectedItem` 테이블에 저장
- 필드: source, source_type, title, content, url, extra_data, collected_at

**저장 결과**: 수집된 모든 아이템이 데이터베이스에 저장됨

---

## 4단계: AI 분석 (app/services/ai_analyzer.py)

**위치**: `app/services/ai_analyzer.py` - `analyze_collected_data()`

**AI 모델**: Gemini 2.0 Flash Lite (4M TPM 활용)

### 4-1. 데이터 준비
```python
# 최근 1시간 내 데이터 가져오기
items = await get_recent_items_for_analysis(hours=1, limit=1000)  # 1000개 아이템

# 소스 타입별 균등 샘플링
# - 각 소스 타입에서 최소 10개씩
# - 최신 50% + 랜덤 50%로 다양성 확보
```

### 4-2. 텍스트 변환
```python
# 최대 1000개 아이템 사용
# 각 아이템: [SOURCE_TYPE] 제목(200자) | 내용(500자)
# 최종 텍스트: 최대 32,000자 (4M TPM 활용)
analysis_text = await prepare_text_for_analysis(items)
```

**텍스트 예시**:
```
[NEWS] Breaking: AI Regulation Bill Passes Senate | The bill requires AI companies to...
[REDDIT] r/technology: New GPU Architecture Announced | AMD reveals next-gen...
[GITHUB] trending-repo: AI Framework v2.0 Released | Major update includes...
[YOUTUBE] Tech Review: Latest Smartphone Comparison | Comprehensive analysis...
```

### 4-3. AI 분석 수행
**프롬프트**: Multi-Source Trend Analyst 역할
- 뉴스, 소셜 미디어, 개발자 커뮤니티, 비디오 플랫폼 모두 고려
- 현재 시점의 이슈 식별 (Why Now?)
- 배경 맥락 제공 (Context)

**AI 요청**:
```python
ai_result = await analyze_text_with_ai(
    analysis_text,  # 최대 32,000자
    analysis_type="summary"
)
```

**AI 출력 설정**:
- `max_output_tokens`: 8,000토큰 (4M TPM 활용)
- `temperature`: 0.7 (창의성과 정확도 균형)

**AI 응답 형식**:
```
Issues:
1. [이슈 제목]
   What: [이슈가 무엇인지]
   Why Now: [왜 지금 이슈가 되고 있는지]
   Context: [배경 맥락]

Summary: [전체 요약]
Keywords: [키워드 목록]
Sentiment: [positive/negative/neutral]
```

### 4-4. 이슈별 상세 분석
각 이슈에 대해:
1. **관련 아이템 필터링**: 이슈 키워드가 제목/내용에 포함된 아이템 찾기
2. **중요도 점수 계산**:
   - 언급 횟수 (30%)
   - 소스 다양성 (30%)
   - 최신성 (20%)
   - 참여도 (20%)
3. **분석 결과 생성**:
   - topic: 이슈 제목
   - what: 이슈 설명
   - why_now: 왜 지금 중요한지
   - context: 배경 맥락
   - importance_score: 중요도 점수
   - source_count: 관련 소스 수
   - collected_item_ids: 관련 아이템 ID 목록

### 4-5. 분석 결과 저장
**위치**: `AnalysisResult` 테이블
- 각 이슈별로 분석 결과 저장
- 최대 10개 이슈 분석

---

## 5단계: 랭킹 계산 (app/services/ranking.py)

**위치**: `app/services/ranking.py` - `calculate_issue_rankings()`

### 5-1. 분석 결과 수집
- 최근 1시간 내 `AnalysisResult` 가져오기
- 같은 토픽의 분석 결과들을 그룹화

### 5-2. 이슈별 점수 계산
각 이슈에 대해:

**언급 횟수 계산**:
```python
# CollectedItem에서 토픽/키워드 매칭
# 제목과 내용에서 토픽명 또는 주요 키워드 검색
mention_count = 실제 매칭된 아이템 수
```

**소스 다양성**:
```python
# 관련 아이템의 고유 소스 타입 수
source_diversity = len(unique_source_types)
```

**출처 정보 수집**:
```python
# 상위 5개 소스 타입
top_source_types = [{"type": "news", "count": 15}, ...]

# 상위 5개 소스 이름
top_source_names = [{"name": "BBC", "count": 8}, ...]
```

**종합 점수 계산**:
```python
final_score = (
    avg_importance * 0.25 +        # 평균 중요도
    content_quality * 0.25 +       # 내용 품질 (what, why_now, context)
    temporal_relevance * 0.20 +    # 시점 관련성 (why_now 존재 여부)
    mention_score * 0.15 +         # 언급 횟수 (최대 10회 = 1.0)
    diversity_score * 0.10 +       # 소스 다양성 (최대 5개 = 1.0)
    depth_score * 0.05             # 내용 깊이 (why_now + context)
)
```

### 5-3. 랭킹 정렬 및 저장
- 점수순으로 정렬
- `IssueRanking` 테이블에 저장
- 필드: topic, rank, score, mention_count, source_diversity, what, why_now, context

---

## 6단계: API 제공 (app/api/endpoints.py)

**API 엔드포인트**:

### 6-1. 랭킹 조회
```
GET /api/rankings?limit=10&lang=ko
```
- 최신 랭킹 반환
- 출처 정보 포함 (sources.types, sources.names)

### 6-2. 상세 분석 조회
```
GET /api/trends/{topic}/detail?lang=ko
```
- 특정 트렌드의 상세 분석
- 시간대별 언급 추이 (24시간)
- 소스별 분포
- 감정 분석 분포
- 주요 키워드
- 관련 아이템 목록

### 6-3. 최근 데이터 조회
```
GET /api/recent?source_type=news&limit=10
```
- 최근 수집된 원본 데이터

---

## 데이터 흐름 다이어그램

```
┌─────────────────┐
│  스케줄러       │ (매 시간 실행)
│  (APScheduler)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  데이터 수집     │
│  - Reddit: 550개 │
│  - News: 650개   │
│  - GitHub: 100개 │
│  - YouTube: 50개 │
│  총: ~1,350개    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  데이터 저장     │
│  - 디스크 관리   │
│  - 개수 관리     │
│  - 중복 없이 저장│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI 분석        │
│  - 1,000개 선택 │
│  - 32,000자 텍스트│
│  - Gemini 분석   │
│  - 8,000 토큰 출력│
│  - 최대 10개 이슈│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  랭킹 계산      │
│  - 언급 횟수     │
│  - 소스 다양성   │
│  - 종합 점수     │
│  - 출처 정보     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API 제공        │
│  - /rankings     │
│  - /trends/detail│
│  - /recent       │
└─────────────────┘
```

---

## 주요 설정값

### 데이터 수집
- Reddit 서브레딧: 10개 × 50개 = 500개
- Reddit Popular: 50개
- 뉴스: 13개 소스 × 50개 = 650개
- GitHub: 100개
- YouTube: 50개
- **총 예상 수집량**: ~1,350개/회

### AI 분석
- 분석 아이템 수: 1,000개
- 입력 텍스트: 최대 32,000자
- 출력 토큰: 8,000토큰
- 최대 이슈 수: 10개

### 데이터 저장
- 최대 저장 개수: 50,000개
- 최대 디스크 용량: 800GB
- 임계값: 80% (640GB)
- 목표 용량: 70% (560GB)

---

## 성능 최적화

### 4K RPM 활용
- 각 수집기에서 대량 데이터 수집
- 병렬 처리로 빠른 수집

### 4M TPM 활용
- 긴 텍스트 분석 (32,000자)
- 상세한 AI 응답 (8,000토큰)
- 더 많은 아이템 분석 (1,000개)

### 무제한 RPD 활용
- 매 시간마다 분석 실행
- 실시간 트렌드 파악

---

## 로깅 및 모니터링

각 단계마다 상세한 로그 출력:
- 수집량 통계
- 저장 결과
- AI 분석 결과
- 랭킹 결과

로그 예시:
```
📥 데이터 수집 시작...
✅ Reddit Popular: 50개 수집
✅ Reddit 서브레딧: 500개 수집
✅ 뉴스: 650개 수집
✅ GitHub: 100개 수집
✅ YouTube: 50개 수집
📊 전체 수집 완료! 총 1,350개 아이템

💾 저장 결과:
  - reddit: 50개 저장됨
  - reddit_subreddits: 500개 저장됨
  - news: 650개 저장됨
  - github: 100개 저장됨
  - youtube: 50개 저장됨

🤖 AI 분석 시작...
📊 분석 대상: 최근 1시간 내 1,000개 아이템
📝 분석 텍스트 생성 완료: 1,000개 항목, 총 32,000자
🤖 AI 분석 완료: 10개 토픽 분석, 10개 저장됨

📊 이슈 랭킹 계산 시작...
📊 이슈 랭킹 완료: 10개 이슈, 10개 저장됨
🏆 주요 이슈 랭킹 (상위 5개):
  1. AI Regulation Bill (점수: 0.85, 언급: 45회, 소스: 4개)
  2. New GPU Architecture (점수: 0.78, 언급: 32회, 소스: 3개)
  ...
```

