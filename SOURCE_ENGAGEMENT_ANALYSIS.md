# 소스별 조회수/참여도 정보 수집 현황

## 현재 수집 중인 정보

### 1. Reddit ✅
**수집 가능한 정보**:
- ✅ `upvotes`: 업보트 수 (수집 중)
- ✅ `comments`: 댓글 수 (수집 중)
- ❌ `views`: 조회수 (Reddit API에서 제공하지 않음)

**코드 위치**: `app/services/collector.py`
```python
"upvotes": post.get("ups", 0),
"comments": post.get("num_comments", 0),
```

**Reddit API 제한사항**:
- Reddit JSON API는 조회수(views) 정보를 제공하지 않습니다
- 업보트와 댓글 수만 제공됩니다

### 2. 뉴스 (RSS) ❌
**수집 가능한 정보**:
- ❌ `views`: 조회수 (RSS 피드에 포함되지 않음)
- ❌ `likes`: 좋아요 수 (RSS 피드에 포함되지 않음)
- ❌ `comments`: 댓글 수 (RSS 피드에 포함되지 않음)

**코드 위치**: `app/services/news_collector.py`
```python
# RSS 피드에서 수집 가능한 정보
- title: 제목
- link: URL
- pubDate: 발행일
- description: 설명
```

**RSS 피드 제한사항**:
- RSS는 표준화된 피드 형식으로, 조회수/참여도 정보를 포함하지 않습니다
- 각 뉴스 사이트의 개별 API를 사용해야 조회수 정보를 얻을 수 있습니다

**개선 방안**:
- 각 뉴스 사이트의 개별 API 사용 (예: NYTimes API, Guardian API 등)
- 하지만 대부분의 뉴스 사이트는 API Key가 필요하고, 조회수 정보 제공 여부가 다릅니다

### 3. GitHub ✅
**수집 가능한 정보**:
- ✅ `stars`: 스타 수 (수집 중)
- ⚠️ `views`: 조회수 (별도 API 호출 필요)
- ⚠️ `forks`: 포크 수 (수집 가능하지만 현재 미수집)
- ⚠️ `watchers`: 워처 수 (수집 가능하지만 현재 미수집)

**코드 위치**: `app/services/github_collector.py`
```python
"stars": repo.get("stargazers_count", 0),
```

**GitHub API 추가 정보 수집 가능**:
- `forks`: `repo.get("forks_count", 0)`
- `watchers`: `repo.get("watchers_count", 0)`
- `views`: 저장소 트래픽 API 사용 필요 (`GET /repos/{owner}/{repo}/traffic/views`)
  - 하지만 이는 저장소 소유자만 접근 가능하므로 일반적으로는 사용 불가

### 4. YouTube ✅
**수집 가능한 정보**:
- ✅ `views`: 조회수 (수집 중)
- ✅ `likes`: 좋아요 수 (수집 중)
- ✅ `comments`: 댓글 수 (수집 중)

**코드 위치**: `app/services/youtube_collector.py`
```python
"views": int(stats.get("viewCount", 0)),
"likes": int(stats.get("likeCount", 0)),
"comments": int(stats.get("commentCount", 0)),
```

## 현재 관심도 계산 방식

```python
# YouTube
interest = views + (likes × 10) + (comments × 5)

# Reddit
interest = upvotes + (comments × 2)

# GitHub
interest = stars × 10

# News
interest = 1 (기본값, 조회수 정보 없음)
```

## 개선 가능 사항

### 1. GitHub 추가 정보 수집
- `forks` 수집 추가
- `watchers` 수집 추가
- 관심도 계산에 반영: `interest = stars × 10 + forks × 5 + watchers × 2`

### 2. 뉴스 조회수 정보
- 대부분의 뉴스 사이트는 조회수 정보를 공개 API로 제공하지 않습니다
- 일부 사이트(예: Medium)는 조회수 정보를 제공하지만, RSS 피드에는 포함되지 않습니다
- 개별 사이트 API 사용 시 API Key 필요 및 할당량 제한 있음

### 3. Reddit 조회수
- Reddit API는 조회수 정보를 제공하지 않습니다
- Reddit의 공식 API 제한사항입니다

## 결론

| 소스 | 조회수 수집 | 참여도 수집 | 개선 가능성 |
|------|------------|------------|------------|
| Reddit | ❌ (API 제한) | ✅ (upvotes, comments) | ❌ |
| 뉴스 (RSS) | ❌ (RSS 제한) | ❌ | ⚠️ (개별 API 필요) |
| GitHub | ⚠️ (제한적) | ✅ (stars) | ✅ (forks, watchers 추가 가능) |
| YouTube | ✅ | ✅ (likes, comments) | ✅ |

**현재 상태**: Reddit과 GitHub는 참여도 정보를 수집하고 있으며, YouTube는 조회수와 참여도 모두 수집 중입니다. 뉴스는 RSS 피드의 제한으로 인해 조회수 정보를 수집할 수 없습니다.

