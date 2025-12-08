# 데이터 수집 소스 제안

## 현재 수집 중
- ✅ Reddit 인기 게시물

## 추천 데이터 소스 (우선순위별)

### 1. 뉴스 사이트 RSS 피드 (높은 우선순위)
**이유**: 신뢰성 높고 구조화된 데이터, AI 분석에 최적
- **BBC News RSS**: `https://feeds.bbci.co.uk/news/rss.xml`
- **CNN RSS**: `https://rss.cnn.com/rss/edition.rss`
- **한국 뉴스**: 
  - 연합뉴스: `https://www.yna.co.kr/rss/all.xml`
  - 조선일보: `https://www.chosun.com/arc/outboundfeeds/rss/`
  - 중앙일보: `https://rss.joins.com/joins_news_list.xml`
- **기술 뉴스**:
  - Hacker News: `https://hnrss.org/frontpage`
  - TechCrunch: `https://techcrunch.com/feed/`

### 2. NewsAPI (높은 우선순위)
**이유**: 다양한 뉴스 소스 통합, 카테고리별 필터링 가능
- 무료 티어: 하루 100회 요청
- API Key 필요 (무료)
- URL: `https://newsapi.org/v2/top-headlines?country=kr&apiKey=YOUR_KEY`

### 3. Twitter/X 트렌딩 (중간 우선순위)
**이유**: 실시간 이슈 파악에 유용, 하지만 API 제한 있음
- Twitter API v2 사용 (유료 또는 제한적 무료)
- 대안: 트위터 스크래핑 (ToS 주의)

### 4. GitHub Trending (중간 우선순위)
**이유**: 기술 트렌드 파악에 유용, API 무료
- URL: `https://api.github.com/search/repositories?q=created:>2024-01-01&sort=stars`
- 언어별, 날짜별 필터링 가능

### 5. YouTube 트렌딩 (중간 우선순위)
**이유**: 대중적 관심사 파악, 하지만 API 제한
- YouTube Data API v3 (무료 할당량: 하루 10,000 units)
- 인기 동영상 제목, 설명 수집

### 6. 주식/금융 데이터 (낮은 우선순위)
**이유**: 경제 이슈 파악, 하지만 전문성 필요
- Alpha Vantage API (무료)
- Yahoo Finance API (비공식)

### 7. 날씨/재해 정보 (낮은 우선순위)
**이유**: 긴급 이슈 파악
- OpenWeatherMap API (무료 티어)
- 기상청 RSS

## 구현 우선순위 추천

### Phase 1 (즉시 구현 가능)
1. ✅ Reddit (이미 구현됨)
2. 뉴스 RSS 피드 (BBC, CNN, 한국 뉴스)
3. Hacker News RSS

### Phase 2 (API Key 필요)
1. NewsAPI
2. GitHub Trending

### Phase 3 (고급)
1. Twitter/X API
2. YouTube API

## 데이터 구조 제안

각 수집기는 다음 정보를 반환해야 함:
```python
{
    "source": "reddit",  # 데이터 소스
    "title": "...",      # 제목
    "content": "...",    # 내용 (가능한 경우)
    "url": "...",        # 원본 링크
    "timestamp": "...",  # 수집 시간
    "category": "...",   # 카테고리 (선택)
    "engagement": {...}  # 참여도 (좋아요, 댓글 등)
}
```


