# RSS 피드 댓글 수 정보 분석

## RSS 표준

### 표준 RSS 필드
RSS 2.0 표준에는 다음 필드만 포함됩니다:
- `<title>`: 제목
- `<link>`: URL
- `<description>`: 설명
- `<pubDate>`: 발행일
- `<guid>`: 고유 식별자
- `<author>`: 작성자 (선택적)
- `<category>`: 카테고리 (선택적)

**댓글 수는 표준 필드에 포함되지 않습니다.**

## 확장 필드 (일부 사이트 사용)

일부 뉴스 사이트는 자체 확장 필드나 네임스페이스를 사용하여 댓글 수를 제공할 수 있습니다:

### 1. Slash 네임스페이스
```xml
<slash:comments xmlns:slash="http://purl.org/rss/1.0/modules/slash/">5</slash:comments>
```

### 2. WFW (Well-Formed Web) 네임스페이스
```xml
<wfw:commentRss>http://example.com/comments/rss</wfw:commentRss>
<wfw:commentCount>10</wfw:commentCount>
```

### 3. 자체 확장 필드
```xml
<comments>15</comments>
<commentCount>15</commentCount>
```

## 실제 사이트 확인

대부분의 주요 뉴스 사이트는 RSS 피드에 댓글 수를 포함하지 않습니다:
- BBC: 댓글 수 없음
- NYTimes: 댓글 수 없음
- The Guardian: 댓글 수 없음
- TechCrunch: 댓글 수 없음
- The Verge: 댓글 수 없음

**예외**: 일부 블로그나 소규모 사이트는 댓글 수를 포함할 수 있지만, 대부분의 주요 뉴스 사이트는 포함하지 않습니다.

## 개선 사항

코드를 수정하여 RSS 피드에서 댓글 수 관련 필드를 찾도록 개선했습니다:

1. 표준 `<comments>` 필드 확인
2. Slash 네임스페이스 (`slash:comments`) 확인
3. 기타 확장 필드 확인 (태그 이름에 "comment" 포함)

하지만 대부분의 뉴스 사이트는 댓글 수를 제공하지 않으므로, AI 기반 관심도 추정이 더 효과적입니다.

