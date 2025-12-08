# 관심도 계산 로직 분석 및 개선 제안

## 현재 구현 분석

### 1. 소스별 관심도 계산 공식

#### YouTube
```python
estimated_views = int(extra.get('views', 0) or 0)
```
- ✅ **장점**: 실제 조회수 사용 (가장 정확)
- ⚠️ **문제점**: 없음

#### Reddit
```python
estimated_views = (upvotes * 80) + (comments * 20)
```
- ⚠️ **문제점**: 
  - **80배는 너무 높음**: Reddit의 실제 view:upvote 비율은 일반적으로 **10:1 ~ 50:1**
  - 예: 1,000 upvotes → 80,000 views 추정 (실제로는 10,000~50,000 views)
  - **과대평가 위험**: Reddit 게시물이 YouTube 동영상보다 높은 관심도로 표시될 수 있음

#### GitHub
```python
estimated_views = (stars * 200) + (forks * 50) + (watchers * 10)
```
- ⚠️ **문제점**:
  - **Stars는 views와 다른 개념**: Stars는 "좋아요" 개념, views는 "조회수"
  - **200배는 과대평가**: GitHub 저장소의 실제 views는 stars보다 훨씬 낮음
  - **스케일 불일치**: GitHub 저장소는 일반적으로 수천~수만 views, stars는 수백~수천

#### News
```python
if comments > 0:
    estimated_views = comments * 50
else:
    # 휴리스틱 점수
    title_length_score = min(len(title) / 10, 50)
    keyword_score = sum(10 for kw in important_keywords if kw.lower() in title.lower())
    estimated_views = 100 + int(title_length_score) + keyword_score
```
- ⚠️ **문제점**:
  - **AI 추정 함수 미사용**: `estimate_news_interest_score()` 함수가 있지만 사용하지 않음
  - **휴리스틱이 너무 단순**: 제목 길이와 키워드만으로는 정확도 낮음
  - **중복 키워드**: `important_keywords` 리스트에 'urgent'가 두 번 나열됨
  - **스케일이 너무 낮음**: 100~300 범위 (YouTube는 수백만~수십억)

## 주요 문제점

### 1. 소스별 스케일 불일치
- **YouTube**: 실제 views (수백만~수십억)
- **Reddit**: 추정 views (수만~수십만, 과대평가 가능)
- **GitHub**: 추정 views (수천~수만, stars 기반)
- **News**: 추정 views (100~10,000, 매우 낮음)

**결과**: News는 항상 낮은 순위, YouTube는 항상 높은 순위로 편향됨

### 2. Reddit 공식의 과대평가
- 현재: `upvotes * 80`
- 실제 비율: `upvotes * 10 ~ 50` (게시물에 따라 다름)
- **개선 필요**: 더 현실적인 배수 사용

### 3. GitHub 공식의 개념적 오류
- Stars ≠ Views
- Stars는 "좋아요" 개념, Views는 "조회수"
- **개선 필요**: 다른 지표 사용 또는 공식 재검토

### 4. News AI 추정 미사용
- `estimate_news_interest_score()` 함수가 구현되어 있지만 사용하지 않음
- 휴리스틱만 사용하여 정확도 낮음

### 5. 엣지 케이스 처리 부족
- 음수 값 처리 없음
- 매우 큰 값 처리 없음
- extra_data 형식 검증 부족

## 개선 제안

### 1. Reddit 공식 개선
```python
# 현재
estimated_views = (upvotes * 80) + (comments * 20)

# 개선안 1: 더 현실적인 배수
estimated_views = (upvotes * 15) + (comments * 5)

# 개선안 2: 로그 스케일 적용 (큰 값 완화)
import math
base_views = (upvotes * 15) + (comments * 5)
estimated_views = int(base_views * (1 + math.log10(max(upvotes, 1)) / 10))
```

### 2. GitHub 공식 개선
```python
# 현재
estimated_views = (stars * 200) + (forks * 50) + (watchers * 10)

# 개선안 1: 더 낮은 배수
estimated_views = (stars * 20) + (forks * 10) + (watchers * 5)

# 개선안 2: Stars를 views로 직접 변환하지 않고, 다른 지표 사용
# GitHub 저장소의 실제 views는 stars의 5~10배 정도
estimated_views = (stars * 8) + (forks * 15) + (watchers * 3)
```

### 3. News AI 추정 활용
```python
# 현재: 휴리스틱만 사용
# 개선안: AI 추정 우선, 실패 시 휴리스틱 fallback
from app.services.ai_analyzer import estimate_news_interest_score

if source_type == 'news':
    # AI 추정 시도
    ai_score = await estimate_news_interest_score(item.title, item.content)
    if ai_score is not None:
        estimated_views = ai_score
    else:
        # Fallback: 휴리스틱
        comments = int(extra.get('comments', 0) or 0)
        if comments > 0:
            estimated_views = comments * 50
        else:
            # 개선된 휴리스틱
            estimated_views = calculate_news_heuristic_score(item)
```

### 4. 소스별 정규화 (선택적)
```python
# 모든 소스를 0-1 범위로 정규화 후 스케일 조정
def normalize_interest_score(raw_score: int, source_type: str) -> int:
    """
    소스별로 다른 스케일을 정규화하여 공정한 비교 가능
    """
    # 소스별 최대값 설정 (경험적 데이터 기반)
    max_scores = {
        'youtube': 10_000_000_000,  # 100억
        'reddit': 1_000_000,        # 100만
        'github': 100_000,          # 10만
        'news': 1_000_000,          # 100만
    }
    
    max_score = max_scores.get(source_type, 1_000_000)
    normalized = min(raw_score / max_score, 1.0)
    
    # 정규화된 값을 공통 스케일로 변환 (예: 0-1M)
    return int(normalized * 1_000_000)
```

### 5. 엣지 케이스 처리 강화
```python
async def calculate_item_interest_score(item: CollectedItem) -> int:
    # ... 기존 코드 ...
    
    # 음수 방지
    estimated_views = max(0, estimated_views)
    
    # 매우 큰 값 제한 (오버플로우 방지)
    estimated_views = min(estimated_views, 10_000_000_000)  # 100억 제한
    
    return int(estimated_views)
```

### 6. News 휴리스틱 개선
```python
def calculate_news_heuristic_score(item: CollectedItem) -> int:
    """
    개선된 News 휴리스틱 점수 계산
    """
    title = item.title or ""
    content = item.content or ""
    
    # 1. 제목 길이 점수 (너무 짧거나 길면 낮음)
    title_length = len(title)
    if 20 <= title_length <= 100:
        length_score = 30
    elif 10 <= title_length < 20 or 100 < title_length <= 150:
        length_score = 20
    else:
        length_score = 10
    
    # 2. 중요 키워드 점수 (중복 제거)
    important_keywords = ['breaking', 'urgent', 'major', 'crisis', 'alert', 'important']
    keyword_score = sum(15 for kw in important_keywords if kw.lower() in title.lower())
    
    # 3. 내용 길이 점수
    content_length = len(content) if content else 0
    content_score = min(content_length / 100, 20)  # 최대 20점
    
    # 4. 기본 점수
    base_score = 100
    
    estimated_views = base_score + int(length_score) + keyword_score + int(content_score)
    return estimated_views
```

## 권장 개선 사항 (우선순위)

### 🔴 높은 우선순위
1. **Reddit 공식 조정**: `upvotes * 80` → `upvotes * 15` (또는 10-20 범위)
2. **News AI 추정 활용**: 휴리스틱 대신 AI 추정 우선 사용
3. **엣지 케이스 처리**: 음수, 매우 큰 값 처리

### 🟡 중간 우선순위
4. **GitHub 공식 조정**: `stars * 200` → `stars * 20` (또는 10-30 범위)
5. **News 휴리스틱 개선**: 더 정교한 점수 계산
6. **중복 키워드 제거**: `important_keywords` 리스트 정리

### 🟢 낮은 우선순위 (선택적)
7. **소스별 정규화**: 공정한 비교를 위한 스케일 조정
8. **로그 스케일 적용**: 큰 값의 과대평가 완화
9. **시간 가중치**: 최근 아이템에 가중치 부여

## 예상 효과

### 개선 전
- Reddit 게시물: 과대평가 (예: 1,000 upvotes = 80,000 views)
- GitHub 저장소: 과대평가 (예: 1,000 stars = 200,000 views)
- News 기사: 과소평가 (예: 100-300 views)
- **결과**: Reddit/GitHub가 News보다 항상 높은 순위

### 개선 후
- Reddit 게시물: 현실적 평가 (예: 1,000 upvotes = 15,000 views)
- GitHub 저장소: 현실적 평가 (예: 1,000 stars = 20,000 views)
- News 기사: AI 기반 정확한 평가 (예: 1,000-50,000 views)
- **결과**: 소스별로 공정한 비교 가능

