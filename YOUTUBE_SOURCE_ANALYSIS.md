# YouTube 출처 정보 누락 원인 분석

## 문제 현상
- 출처 정보에 Reddit, News, GitHub만 표시되고 YouTube가 표시되지 않음

## 원인 분석

### 1. 데이터 수집 단계 ✅
- `youtube_collector.py`: YouTube 데이터 수집 로직 정상
- `unified_collector.py`: YouTube 수집 호출 정상
- `storage.py`: `source_type_mapping`에 "youtube": "youtube" 매핑 정상
- **가능한 문제**: YouTube API Key가 설정되지 않았거나 할당량 초과

### 2. AI 분석 단계 ⚠️ (주요 원인)
**파일**: `app/services/ai_analyzer.py` (658-694줄)

**문제점**:
- AI 분석 시 `related_items`를 필터링할 때 **키워드 매칭**을 사용
- 이슈 제목의 키워드가 YouTube 아이템의 제목/내용에 포함되지 않으면 `related_items`에 포함되지 않음
- 따라서 `collected_item_ids`에 YouTube 아이템 ID가 포함되지 않음

**현재 로직**:
```python
# 이슈 제목의 주요 단어들이 제목이나 내용에 포함되는지 확인
match_score = 0
for keyword in issue_keywords:
    if len(keyword) > 3:  # 3글자 이상인 키워드만
        if keyword in title_lower:
            match_score += 2
        elif keyword in content_lower:
            match_score += 1

# 최소 2점 이상이면 관련 아이템으로 간주
if match_score >= 2:
    related_items.append(item)
```

**문제**:
- YouTube 동영상 제목이 토픽 키워드와 정확히 일치하지 않으면 제외됨
- 예: 토픽이 "2025 Video Game Releases"인데 YouTube 제목이 "New Games Coming in 2025"이면 매칭 실패

### 3. 출처 정보 계산 단계 ⚠️
**파일**: `app/services/ranking.py` (177줄)

**문제점**:
- 출처 정보 계산 시 `items[:50]`만 확인
- AI 분석 단계에서 YouTube가 제외되면, 이 50개에도 YouTube가 없음

**현재 로직**:
```python
for item in items[:50]:  # 최대 50개만 확인
    source_type = item.source_type or 'unknown'
    source_name = item.source or 'Unknown'
    source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1
```

## 해결 방안

### 방안 1: AI 분석 시 더 관대한 매칭 로직 (권장)
- 키워드 매칭 점수 기준을 낮추기 (2점 → 1점)
- 또는 모든 소스 타입을 균등하게 포함하도록 수정

### 방안 2: 출처 정보 계산 시 더 많은 아이템 확인
- `items[:50]` → `items[:200]`으로 증가
- 또는 `collected_item_ids` 전체를 확인

### 방안 3: YouTube 데이터 수집 확인
- 실제로 YouTube 데이터가 수집되고 있는지 로그 확인
- YouTube API Key 설정 확인

## 권장 수정 사항

1. **AI 분석 매칭 로직 개선**: 키워드 매칭 점수 기준 완화
2. **출처 정보 계산 범위 확대**: 더 많은 아이템 확인
3. **YouTube 데이터 수집 확인**: 로그 및 API Key 확인

