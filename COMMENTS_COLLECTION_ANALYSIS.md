# 뉴스와 Reddit 댓글 수 수집 가능 여부 분석

## Reddit 댓글 수 수집 현황

### 1. Reddit Subreddits ✅ (이미 수집 중)
**현재 상태**: 댓글 수 수집 중
**코드 위치**: `app/services/collector.py` → `fetch_reddit_subreddit()`
```python
"comments": post.get("num_comments", 0),  # ✅ 수집 중
```

**수집 정보**:
- ✅ upvotes
- ✅ comments (댓글 수)
- ✅ title, url, subreddit

### 2. Reddit Popular ❌ (댓글 수 미수집)
**현재 상태**: 제목만 수집, 댓글 수 미수집
**코드 위치**: `app/services/collector.py` → `fetch_google_trends()`

**현재 코드**:
```python
# 제목만 추출
trends.append(title)
```

**Reddit API 응답 확인**:
- Reddit API (`/r/popular/hot.json`) 응답에는 `num_comments` 필드가 포함되어 있음
- 하지만 현재 코드는 제목만 추출하고 있음

**개선 가능**: ✅ **쉽게 개선 가능**
- Reddit API 응답에서 `num_comments` 필드도 함께 수집 가능

## 뉴스 댓글 수 수집 현황

### RSS 피드 ❌ (댓글 수 없음)
**현재 상태**: RSS 피드에는 댓글 수 정보가 포함되지 않음
**코드 위치**: `app/services/news_collector.py`

**RSS 피드 표준 필드**:
- ✅ title: 제목
- ✅ link: URL
- ✅ pubDate: 발행일
- ✅ description: 설명
- ❌ comments: 댓글 수 (RSS 표준에 없음)

**RSS 피드 제한사항**:
- RSS는 표준화된 XML 형식으로, 댓글 수 정보를 포함하지 않습니다
- 각 뉴스 사이트마다 댓글 시스템이 다르고, RSS 피드에는 포함되지 않습니다

### 개선 가능성

#### 1. RSS 피드 확장 (일부 사이트)
- 일부 뉴스 사이트는 자체 RSS 확장 필드를 사용할 수 있음
- 하지만 표준이 아니므로 사이트마다 다름
- 예: `<comments>`, `<slash:comments>` 등 (사용 빈도 낮음)

#### 2. 각 뉴스 사이트 개별 API 사용
- **NYTimes API**: 댓글 수 제공 (API Key 필요)
- **Guardian API**: 댓글 수 제공 (API Key 필요)
- **Medium API**: 일부 댓글 정보 제공
- **Disqus API**: 댓글 플랫폼 사용 사이트의 경우 (API Key 필요)

**문제점**:
- 각 사이트마다 다른 API 필요
- 대부분 API Key 필요 및 할당량 제한
- 구현 복잡도 높음

#### 3. 웹 스크래핑 (비권장)
- 각 뉴스 기사 페이지에서 댓글 수 추출
- 하지만 ToS 위반 가능성, 불안정함, 유지보수 어려움

## 결론

### Reddit
| 소스 | 댓글 수 수집 | 상태 |
|------|------------|------|
| Reddit Subreddits | ✅ 수집 중 | 정상 |
| Reddit Popular | ❌ 미수집 | 개선 가능 |

**Reddit Popular 개선**: Reddit API 응답에 `num_comments`가 있으므로 쉽게 수집 가능

### 뉴스
| 소스 | 댓글 수 수집 | 상태 |
|------|------------|------|
| RSS 피드 | ❌ 불가능 | RSS 표준 제한 |
| 개별 API | ⚠️ 제한적 | API Key 필요, 사이트별 다름 |

**뉴스 개선**: RSS 피드로는 불가능, 개별 API 사용 시 제한적

## 개선 제안

### Reddit Popular 댓글 수 수집 추가 (권장)
Reddit API 응답에서 `num_comments`도 함께 수집하도록 개선 가능

```python
# 개선 예시
for post in data["data"]["children"]:
    post_data = post.get("data", {})
    if post_data.get("title"):
        trend_item = {
            "source": "Reddit Popular",
            "title": post_data.get("title", ""),
            "upvotes": post_data.get("ups", 0),  # 추가
            "comments": post_data.get("num_comments", 0),  # 추가
            "url": f"https://reddit.com{post_data.get('permalink', '')}",  # 추가
            "collected_at": datetime.now().isoformat()
        }
```

### 뉴스 댓글 수 수집 (선택적)
- RSS 피드로는 불가능
- 주요 뉴스 사이트의 개별 API 사용 고려 (NYTimes, Guardian 등)
- 하지만 구현 복잡도와 유지보수 비용이 높음

