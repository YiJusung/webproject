# 조회수와 참여도 둘 다 수집되지 않는 소스

## 현재 수집 중인 소스별 정보 수집 현황

### 1. Reddit Popular (fetch_google_trends) ❌❌
**수집 정보**:
- ✅ 제목 (title)만 수집
- ❌ 조회수: 없음
- ❌ 참여도: 없음 (upvotes, comments 미수집)

**코드 위치**: `app/services/collector.py` → `fetch_google_trends()`
```python
# 제목만 추출
trends.append(title)

# unified_collector.py에서 저장
{
    "source": "Reddit Popular",
    "title": trend,  # 제목만
    "collected_at": datetime.now().isoformat()
}
```

**문제점**: 
- Reddit API에서 제목만 가져오고 있음
- 실제 게시물 데이터(upvotes, comments)를 수집하지 않음

**개선 가능**: 
- Reddit API 응답에서 `ups`, `num_comments` 필드도 함께 수집 가능

### 2. 뉴스 (RSS 피드) ❌❌
**수집 정보**:
- ✅ 제목 (title)
- ✅ 설명 (description)
- ✅ URL
- ✅ 발행일 (published)
- ❌ 조회수: RSS 피드에 포함되지 않음
- ❌ 참여도: RSS 피드에 포함되지 않음

**코드 위치**: `app/services/news_collector.py`
```python
news_item = {
    "source": source_name,
    "title": title_elem.text.strip(),
    "url": link_elem.text,
    "published": pub_date_elem.text,
    "description": description_elem.text,
    # 조회수/참여도 정보 없음
}
```

**문제점**:
- RSS 피드는 표준 형식으로 조회수/참여도 정보를 포함하지 않음

**개선 가능성**:
- ⚠️ 제한적: 각 뉴스 사이트의 개별 API 필요
- 대부분 API Key 필요 및 할당량 제한
- 일부 사이트는 조회수 정보를 제공하지 않음

## 요약

| 소스 | 조회수 | 참여도 | 상태 |
|------|--------|--------|------|
| **Reddit Popular** | ❌ | ❌ | 제목만 수집 |
| **뉴스 (RSS)** | ❌ | ❌ | RSS 제한 |
| Reddit Subreddits | ❌ | ✅ | upvotes, comments |
| GitHub | ❌ | ✅ | stars, forks, watchers |
| YouTube | ✅ | ✅ | views, likes, comments |

## 개선 방안

### 1. Reddit Popular 개선 (쉬움)
**현재**: 제목만 수집
**개선**: Reddit API 응답에서 upvotes, comments도 함께 수집

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

### 2. 뉴스 조회수 개선 (어려움)
**현재**: RSS 피드만 사용
**개선**: 각 뉴스 사이트의 개별 API 사용 필요
- NYTimes API
- Guardian API
- Medium API (일부 조회수 제공)
- 하지만 대부분 API Key 필요 및 할당량 제한

## 결론

**조회수와 참여도 둘 다 수집되지 않는 소스**:
1. **Reddit Popular** - 제목만 수집 (개선 가능)
2. **뉴스 (RSS)** - RSS 피드 제한 (개선 어려움)

**Reddit Popular**는 쉽게 개선 가능하지만, **뉴스**는 RSS 피드의 한계로 인해 개선이 어렵습니다.

