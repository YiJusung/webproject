# 📝 TrendPulse 프롬프트 설계 문서

이 문서는 TrendPulse 웹사이트 개발 과정에서 사용된 AI 프롬프트 설계 내용을 정리한 것입니다.

## 📋 목차

1. [개요](#개요)
2. [AI 분석 프롬프트](#ai-분석-프롬프트)
3. [번역 프롬프트](#번역-프롬프트)
4. [프롬프트 설계 원칙](#프롬프트-설계-원칙)
5. [프롬프트 최적화 이력](#프롬프트-최적화-이력)

---

## 개요

TrendPulse는 Google Gemini API를 활용하여 다음과 같은 AI 기능을 제공합니다:

- **트렌드 분석**: 다양한 소스에서 수집된 데이터를 분석하여 현재 중요한 이슈를 식별
- **번역**: 선택된 언어에 맞춰 이슈 정보를 자동 번역
- **관심도 평가**: 뉴스 기사의 잠재적 관심도를 평가

### 사용 모델
- **모델**: `gemini-2.0-flash-lite`
- **최대 토큰**: 8,000 tokens (분석), 1,000 tokens (번역)
- **온도 설정**: 0.7 (분석), 0.3 (번역, 관심도 평가)

---

## AI 분석 프롬프트

### 1. 트렌드 분석 프롬프트 (Summary Type)

**목적**: 다양한 소스(뉴스, Reddit, GitHub, YouTube 등)에서 수집된 데이터를 분석하여 현재 중요한 이슈를 식별하고, 왜 지금 중요한지 설명

**프롬프트 구조**:

```
You are an expert multi-source trend analyst with deep understanding of current events, market dynamics, social media trends, developer communities, and information patterns across all platforms. Your role is to identify what information is becoming an issue RIGHT NOW and explain WHY it matters at this moment.

## Your Role (Persona):
- Multi-Source Trend Analyst: You analyze trends across news, social media (Reddit, Twitter/X), developer communities (GitHub), video platforms (YouTube), and other sources
- Technology Trend Analyst: You understand tech industry dynamics, emerging patterns, and market shifts
- Social Media Analyst: You recognize viral trends, community discussions, and grassroots movements
- Developer Community Analyst: You understand open-source trends, technical discussions, and developer sentiment
- News Editor: You can identify what's newsworthy and why certain topics gain traction
- Context Interpreter: You connect dots between events, trends, and their significance across different platforms

## Your Reasoning Framework:
When analyzing information, think through these dimensions:

1. **Temporal Significance (Why Now?)**: 
   - What makes this information relevant RIGHT NOW?
   - Is this a sudden development, breaking news, or emerging trend?
   - What changed recently that makes this important?

2. **Context & Background**:
   - What is the broader context behind this issue?
   - What events or trends led to this moment?
   - What background information is needed to understand why this matters?

3. **Impact & Implications**:
   - Who is affected by this issue?
   - What are the potential consequences or implications?
   - How might this develop in the near future?

4. **Pattern Recognition**:
   - Is this part of a larger trend or pattern?
   - How does this relate to other current issues?
   - What makes this stand out from similar past events?

## Analysis Task:
Analyze the following information from various sources (news, social media, GitHub, YouTube, etc.). Identify the main issues that are becoming important RIGHT NOW, not just frequently mentioned keywords. Consider all source types equally - each provides valuable insights.

[수집된 데이터 텍스트 - 최대 32,000자]

For each issue you identify, provide:
1. **Issue Title**: A descriptive, meaningful title (not just a single word)
2. **What It Is**: Brief description of what the issue is about
3. **Why Now**: Explain WHY this is becoming an issue RIGHT NOW - what makes it timely and relevant at this moment
4. **Context**: Provide background context that helps understand why this matters

Format your response as:
Issues:
1. [Descriptive Issue Title]
   What: [Brief description of what this issue is about]
   Why Now: [Explain why this is becoming an issue RIGHT NOW - what changed, what makes it timely]
   Context: [Background context that explains the significance]

2. [Descriptive Issue Title]
   What: [Brief description]
   Why Now: [Why this matters right now]
   Context: [Background context]

3. [Descriptive Issue Title]
   What: [Brief description]
   Why Now: [Why this matters right now]
   Context: [Background context]

Summary: [Overall summary of the main trends and why they matter now, one sentence under 200 characters]
Keywords: [5-10 relevant keywords, comma-separated]
```

**설계 의도**:
- **Persona 기반 접근**: AI에게 전문가 역할을 부여하여 더 정확한 분석 유도
- **4가지 분석 프레임워크**: 시간적 중요성, 맥락, 영향, 패턴 인식을 통해 다각도 분석
- **구조화된 출력 형식**: 파싱이 쉬운 형식으로 응답 요청
- **예시 제공**: AI가 원하는 형식을 이해하도록 구체적인 예시 포함

**설정 파라미터**:
- Temperature: 0.7 (창의성과 맥락 이해를 위한 적절한 수준)
- Max Output Tokens: 8,000 (상세한 분석을 위한 충분한 공간)
- Input Text Limit: 32,000자 (4M TPM 활용)

### 2. 키워드 추출 프롬프트 (Keywords Type)

**목적**: 텍스트에서 가장 중요한 키워드와 주제를 추출

**프롬프트**:
```
다음 텍스트에서 가장 중요한 키워드와 주제를 추출해주세요.

텍스트:
[텍스트 - 최대 16,000자]

응답 형식:
- 키워드: (중요한 키워드 10개, 쉼표로 구분)
- 주요 주제: (3-5개의 주요 주제)
```

**설계 의도**:
- 간단하고 명확한 지시
- 구조화된 출력 형식
- 한국어 프롬프트 사용 (키워드 추출은 언어에 덜 민감)

### 3. 감정 분석 프롬프트 (Sentiment Type)

**목적**: 텍스트의 감정을 분석 (positive, negative, neutral)

**프롬프트**:
```
다음 텍스트의 감정을 분석해주세요.

텍스트:
[텍스트 - 최대 16,000자]

응답 형식:
- 감정: (positive, negative, neutral 중 하나)
- 이유: (간단한 설명)
```

**설계 의도**:
- 간단한 3가지 감정 분류
- 이유 제공으로 신뢰성 향상

### 4. 뉴스 관심도 평가 프롬프트

**목적**: 뉴스 기사의 잠재적 관심도와 조회수를 평가

**프롬프트**:
```
You are an expert news analyst. Evaluate the potential public interest and viewership for this news article based on its title and description.

Consider these factors:
1. **Newsworthiness**: How important or significant is this news?
2. **Timeliness**: Is this breaking news or a current hot topic?
3. **Relevance**: How relevant is this to a broad audience?
4. **Impact**: How many people would be affected or interested?
5. **Viral Potential**: How likely is this to be shared or discussed?

News Article:
Title: [뉴스 제목]
Description: [뉴스 설명 - 최대 500자]

Provide your assessment as a single number from 0 to 100, where:
- 0-20: Low interest (niche topic, limited relevance)
- 21-40: Moderate interest (somewhat relevant)
- 41-60: Good interest (relevant to many people)
- 61-80: High interest (important news, breaking story)
- 81-100: Very high interest (major breaking news, viral potential, widespread impact)

Respond with ONLY a number between 0 and 100, nothing else.
```

**설계 의도**:
- 5가지 평가 기준을 명시하여 일관성 있는 평가 유도
- 숫자만 반환하도록 명확히 지시 (파싱 용이성)
- 점수 범위별 의미를 명시하여 AI가 적절한 점수 부여

**설정 파라미터**:
- Temperature: 0.3 (일관성 있는 점수 평가를 위한 낮은 온도)
- Max Output Tokens: 10 (숫자만 필요하므로 최소화)

---

## 번역 프롬프트

### 텍스트 번역 프롬프트

**목적**: 이슈 정보를 선택된 언어(한국어/영어)로 번역

**프롬프트**:
```
Translate the following text to {target_lang_name}. 
Keep the meaning and tone accurate. If the text is already in {target_lang_name}, return it as is.

Text to translate:
[원본 텍스트 - 최대 2,000자]

Translation:
```

**설계 의도**:
- 간단하고 명확한 번역 지시
- 의미와 톤 보존 강조
- 이미 목표 언어인 경우 원본 반환 지시 (불필요한 번역 방지)

**설정 파라미터**:
- Temperature: 0.3 (정확한 번역을 위한 낮은 온도)
- Max Output Tokens: 1,000
- Input Text Limit: 2,000자

**언어 감지 로직**:
- 번역 전에 간단한 휴리스틱으로 언어 감지 시도
- 한글 유니코드 범위 체크: `\uac00` ~ `\ud7a3`
- 영어는 ASCII 범위 체크: `ord(c) < 128`

---

## 프롬프트 설계 원칙

### 1. 명확성 (Clarity)
- AI가 수행해야 할 작업을 명확하게 정의
- 구체적인 출력 형식 요구
- 예시 제공으로 기대 형식 명시

### 2. 구조화 (Structure)
- Persona 기반 접근으로 전문성 부여
- 단계별 분석 프레임워크 제공
- 구조화된 출력 형식 요구

### 3. 맥락 제공 (Context)
- 분석해야 할 데이터의 소스와 특성 명시
- 분석 목적과 사용 목적 설명
- 평가 기준 명시

### 4. 안전성 (Safety)
- Safety Settings를 `BLOCK_NONE`으로 설정하여 안전 필터 회피
- 영어 프롬프트 사용으로 안전 필터 우회 (분석 프롬프트)
- 명확한 지시로 의도하지 않은 차단 방지

### 5. 효율성 (Efficiency)
- 필요한 만큼의 토큰만 사용
- 캐싱을 통한 중복 요청 방지
- 입력 텍스트 길이 제한으로 비용 최적화

### 6. 파싱 용이성 (Parseability)
- 구조화된 출력 형식 (Issues:, Summary:, Keywords: 등)
- 일관된 구분자 사용 (콜론, 쉼표 등)
- 예외 처리 로직 포함

---

## 프롬프트 최적화 이력

### v1.0 (초기 버전)
- 기본적인 트렌드 분석 프롬프트
- 간단한 키워드 추출
- 입력 텍스트: 6,000자

### v2.0 (4M TPM 활용)
- **입력 텍스트 증가**: 6,000자 → 32,000자
- **출력 토큰 증가**: 2,000 → 8,000 tokens
- **데이터 수집량 증가**: 100개 → 1,000개 아이템
- **소스 다양성 강화**: 소스 타입별 균등 샘플링

### v2.1 (이슈 기반 분석)
- **구조화된 이슈 형식**: 단순 키워드 → What/Why Now/Context 포함
- **Persona 강화**: 6가지 전문가 역할 명시
- **4가지 분석 프레임워크 추가**: 시간적 중요성, 맥락, 영향, 패턴 인식

### v2.2 (번역 기능 개선)
- **번역 헬퍼 함수 추가**: 일관된 번역 로직
- **오류 처리 개선**: API 키 오류 시 자동 재시도
- **로깅 추가**: 번역 시도/성공/실패 추적

---

## 프롬프트 응답 파싱

### 분석 결과 파싱

AI 응답은 다음과 같은 형식으로 파싱됩니다:

```python
{
    'issues': [
        {
            'title': '이슈 제목',
            'what': '무엇인지 설명',
            'why_now': '왜 지금 중요한지',
            'context': '배경 맥락'
        }
    ],
    'topics': ['이슈 제목 리스트'],
    'summary': '전체 요약',
    'keywords': ['키워드1', '키워드2', ...],
    'sentiment': 'neutral' | 'positive' | 'negative'
}
```

### 파싱 로직 특징

1. **유연한 파싱**: 여러 형식 지원 (Issues:, Topics:, Keywords: 등)
2. **하위 호환성**: 기존 형식과 새 형식 모두 지원
3. **기본값 제공**: 파싱 실패 시 기본값 반환
4. **에러 처리**: 예외 발생 시 안전하게 처리

---

## 성능 최적화

### 1. 캐싱
- 번역 결과 캐싱 (메모리 기반)
- 동일한 텍스트 재번역 방지

### 2. 배치 처리
- 여러 필드 동시 번역
- 소스 타입별 균등 샘플링

### 3. 토큰 최적화
- 필요한 만큼만 토큰 사용
- 입력 텍스트 길이 제한
- 출력 형식 최적화

### 4. 비동기 처리
- `run_in_executor`를 통한 비동기 API 호출
- 여러 요청 병렬 처리

---

## 주의사항

### 1. API 키 보안
- API 키는 환경 변수로 관리
- `.env` 파일은 `.gitignore`에 포함
- API 키 유출 시 즉시 재발급 필요

### 2. 안전 필터
- Safety Settings를 `BLOCK_NONE`으로 설정
- 영어 프롬프트 사용으로 안전 필터 우회
- 명확한 지시로 의도하지 않은 차단 방지

### 3. 오류 처리
- API 호출 실패 시 원본 데이터 반환
- 번역 실패 시 원본 텍스트 유지
- 로깅을 통한 문제 추적

### 4. 비용 관리
- 토큰 사용량 모니터링
- 캐싱을 통한 중복 요청 방지
- 불필요한 번역 시도 최소화

---

## 향후 개선 방향

### 1. 프롬프트 개선
- 더 정확한 이슈 식별을 위한 프롬프트 튜닝
- 다양한 언어 지원 확대
- 감정 분석 정확도 향상

### 2. 성능 최적화
- 프롬프트 압축으로 토큰 사용량 감소
- 더 효율적인 파싱 로직
- 배치 처리 최적화

### 3. 기능 확장
- 다국어 번역 지원
- 더 상세한 분석 옵션
- 사용자 맞춤형 분석

---

## 참고 자료

- [Google Gemini API 문서](https://ai.google.dev/docs)
- [프롬프트 엔지니어링 가이드](https://ai.google.dev/docs/prompt_intro)
- [Gemini 모델 정보](https://ai.google.dev/models/gemini)

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-12-17  
**작성자**: TrendPulse 개발팀

