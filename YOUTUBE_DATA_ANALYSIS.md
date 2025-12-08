# YouTube 데이터 수집 및 AI 분석 애로사항 분석

## 현재 YouTube 데이터 처리 방식

### 1. 수집 단계 (`youtube_collector.py`)
**수집되는 정보**:
- ✅ 제목 (title): 최대 200자
- ✅ 설명 (description): 최대 300자
- ✅ 통계 정보: 조회수(views), 좋아요(likes), 댓글(comments)
- ✅ 메타데이터: 채널명, 게시일, URL
- ❌ **실제 영상 내용**: 수집하지 않음 (자막, 음성 전사 없음)

### 2. 저장 단계 (`storage.py`)
**저장되는 필드**:
- `title`: 동영상 제목
- `content`: 동영상 설명 (description)
- `source_type`: "youtube"
- `extra_data`: views, likes, comments, channel 등

### 3. AI 분석 단계 (`ai_analyzer.py`)
**분석에 사용되는 정보**:
```python
# 제목과 내용 조합
if content and len(content) > 20:
    text = f"[YOUTUBE] {title[:150]} | {content[:500]}"
else:
    text = f"[YOUTUBE] {title[:200]}"  # 제목만 사용
```

## 주요 애로사항

### 1. 정보량 부족 ⚠️
**문제점**:
- 실제 영상 내용(자막, 음성)을 수집하지 않아 **텍스트 정보가 매우 제한적**
- 제목과 설명만으로는 영상의 핵심 내용을 파악하기 어려움
- 다른 소스(뉴스, Reddit)에 비해 분석 가능한 텍스트가 적음

**예시**:
- 뉴스: 제목 + 본문 전체 (수백~수천 자)
- Reddit: 제목 + 본문 + 댓글 (수백 자)
- YouTube: 제목 + 설명 (최대 500자, 실제로는 보통 100-200자)

### 2. 설명 부재 가능성 ⚠️
**문제점**:
- 많은 YouTube 동영상이 설명을 작성하지 않거나 매우 짧게 작성
- 설명이 없으면 제목만으로 분석해야 함
- AI 분석 시 컨텍스트 부족으로 정확도 저하

### 3. 키워드 매칭 어려움 ⚠️
**문제점**:
- 제목과 설명만으로는 토픽 키워드와 매칭이 어려울 수 있음
- 실제 영상 내용과 제목/설명이 다를 수 있음
- 예: 제목이 "New Tech Review"인데 실제 내용은 "AI Breakthrough"에 대한 것일 수 있음

### 4. 통계 정보 활용 부족 ⚠️
**문제점**:
- 조회수, 좋아요, 댓글 수는 수집되지만 AI 분석에 직접 활용되지 않음
- 트렌드 분석에 유용한 정보(인기도, 참여도)가 활용되지 않음

## 개선 방안

### 방안 1: 자막/전사 데이터 수집 (권장, 고난이도)
**장점**:
- 영상의 실제 내용을 분석 가능
- AI 분석 정확도 대폭 향상

**단점**:
- YouTube Data API v3는 자막/전사 제공 안 함
- 별도 라이브러리 필요 (youtube-transcript-api 등)
- 추가 API 호출 및 처리 시간 증가
- 자막이 없는 영상은 여전히 제한적

**구현 방법**:
```python
# youtube-transcript-api 사용 예시
from youtube_transcript_api import YouTubeTranscriptApi

async def get_video_transcript(video_id: str):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = ' '.join([item['text'] for item in transcript])
        return text[:5000]  # 최대 5000자
    except:
        return None
```

### 방안 2: 설명 길이 제한 확대 (쉬움)
**현재**: 설명 최대 300자
**개선**: 설명 최대 1000자로 확대

**장점**:
- 더 많은 텍스트 정보 수집
- 구현 간단

**단점**:
- 여전히 설명이 없거나 짧은 영상은 제한적

### 방안 3: 통계 정보를 중요도 점수에 반영 (중간 난이도)
**현재**: 통계 정보는 수집만 하고 분석에 미사용
**개선**: 조회수, 좋아요, 댓글 수를 중요도 점수 계산에 반영

**장점**:
- 인기 있는 영상이 더 높은 점수를 받음
- 트렌드 분석 정확도 향상

**구현 방법**:
```python
# importance_score 계산 시
views_score = min(item.views / 1000000, 1.0)  # 100만 조회수 = 1.0
likes_score = min(item.likes / 10000, 1.0)    # 1만 좋아요 = 1.0
engagement_score = (views_score * 0.5 + likes_score * 0.5)
```

### 방안 4: 댓글 수집 (중간 난이도)
**장점**:
- 사용자 반응 및 의견 파악 가능
- 추가 텍스트 정보 확보

**단점**:
- YouTube Data API v3는 댓글 수집 가능하지만 추가 API 호출 필요
- 댓글이 많으면 처리 시간 증가
- 스팸/부적절한 댓글 필터링 필요

## 권장 개선 순서

1. **즉시 적용 가능**: 설명 길이 제한 확대 (300자 → 1000자)
2. **단기 개선**: 통계 정보를 중요도 점수에 반영
3. **중기 개선**: 댓글 수집 추가
4. **장기 개선**: 자막/전사 데이터 수집 (가장 효과적이지만 구현 복잡)

## 현재 상태 요약

✅ **정상 작동**: 제목과 설명 기반 분석은 가능
⚠️ **제한적**: 다른 소스에 비해 텍스트 정보가 부족
💡 **개선 여지**: 자막/전사 수집 시 분석 정확도 대폭 향상 가능

