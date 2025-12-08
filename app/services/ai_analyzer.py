"""
AI를 사용하여 수집된 데이터를 분석하는 모듈 (Gemini API 사용)
"""
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.core.models import CollectedItem, AnalysisResult

load_dotenv()
logger = logging.getLogger("hourly_pulse")

# Gemini 클라이언트 초기화
gemini_model = None
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # gemini-2.0-flash-lite 사용
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
    logger.info("✅ Gemini 클라이언트 초기화 완료 (gemini-2.0-flash-lite)")
else:
    logger.warning("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. AI 분석 기능이 작동하지 않습니다.")


async def analyze_text_with_ai(text: str, analysis_type: str = "summary") -> Optional[Dict[str, Any]]:
    """
    Gemini API를 사용하여 텍스트를 분석합니다.
    
    Args:
        text: 분석할 텍스트
        analysis_type: 분석 타입 ("summary", "keywords", "sentiment")
    
    Returns:
        분석 결과 딕셔너리
    """
    if not gemini_model:
        logger.error("❌ Gemini 클라이언트가 초기화되지 않았습니다.")
        return None
    
    if not text or len(text.strip()) < 10:
        logger.warning("⚠️ 분석할 텍스트가 너무 짧습니다.")
        return None
    
    try:
        # 프롬프트 구성 (영어 프롬프트 사용 - 안전 필터 회피)
        if analysis_type == "summary":
            prompt = f"""You are an expert multi-source trend analyst with deep understanding of current events, market dynamics, social media trends, developer communities, and information patterns across all platforms. Your role is to identify what information is becoming an issue RIGHT NOW and explain WHY it matters at this moment.

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

{text[:32000]}  # 6000 -> 32000으로 증가 (4M TPM 활용)

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

Example:
Issues:
1. AI Safety Regulation Push
   What: Major tech companies and governments are pushing for AI safety regulations as AI capabilities rapidly advance
   Why Now: Recent high-profile AI incidents and rapid deployment of powerful AI models have created urgency for regulatory frameworks before potential risks materialize
   Context: This follows months of AI breakthroughs and growing public concern about AI's societal impact, making it a critical policy moment

2. Climate Tech Investment Surge
   What: Significant increase in climate technology investments and carbon reduction commitments
   Why Now: Recent climate events and policy changes have created a window of opportunity for climate tech, with investors seeing both urgency and potential returns
   Context: This aligns with upcoming climate summits and new government incentives, creating a convergence of factors that make climate tech attractive now

Summary: Current focus is on AI regulation urgency and climate tech investment surge, both driven by recent developments creating critical decision points.
Keywords: AI, regulation, safety, climate, tech, investment, policy, urgency
"""
        elif analysis_type == "keywords":
            prompt = f"""다음 텍스트에서 가장 중요한 키워드와 주제를 추출해주세요.

텍스트:
{text[:16000]}  # 4000 -> 16000으로 증가 (4M TPM 활용)

응답 형식:
- 키워드: (중요한 키워드 10개, 쉼표로 구분)
- 주요 주제: (3-5개의 주요 주제)
"""
        else:  # sentiment
            prompt = f"""다음 텍스트의 감정을 분석해주세요.

텍스트:
{text[:16000]}  # 4000 -> 16000으로 증가 (4M TPM 활용)

응답 형식:
- 감정: (positive, negative, neutral 중 하나)
- 이유: (간단한 설명)
"""
        
        # Gemini API 호출 (비동기 실행을 위해 run_in_executor 사용)
        # 안전 설정을 최대한 완화
        safety_settings = [
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
        ]
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,  # 창의성 증가 (맥락과 설명을 위해)
                    max_output_tokens=8000,  # 4M TPM 활용하여 더 긴 응답 (2000 -> 8000으로 증가)
                ),
                safety_settings=safety_settings
            )
        )
        
        # Gemini 응답에서 텍스트 추출
        try:
            # finish_reason 확인
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason
                
                # finish_reason이 SAFETY(2) 또는 다른 이유로 차단된 경우
                if finish_reason != 1:  # 1 = STOP (정상 완료)
                    logger.warning(f"⚠️ Gemini 응답이 차단됨 (finish_reason: {finish_reason})")
                    if finish_reason == 2:  # SAFETY
                        logger.warning("  안전 필터에 의해 차단되었습니다. 프롬프트를 조정해주세요.")
                    return None
                
                # 정상 응답인 경우 텍스트 추출
                if hasattr(candidate, 'content') and candidate.content.parts:
                    content = candidate.content.parts[0].text
                else:
                    logger.error("❌ Gemini 응답에 텍스트가 없습니다.")
                    return None
            elif hasattr(response, 'text'):
                content = response.text
            else:
                logger.error("❌ Gemini 응답 형식이 예상과 다릅니다.")
                return None
        except Exception as e:
            logger.error(f"❌ Gemini 응답 처리 실패: {e}")
            return None
        
        logger.info(f"✅ AI 분석 완료 ({analysis_type})")
        
        # 응답 파싱
        return parse_ai_response(content, analysis_type)
        
    except Exception as e:
        logger.error(f"❌ AI 분석 실패: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_ai_response(content: str, analysis_type: str) -> Dict[str, Any]:
    """
    AI 응답을 파싱하여 구조화된 데이터로 변환합니다.
    """
    result = {}
    
    try:
        # 영어 응답 파싱 (Issues:, Summary:, Keywords: 형식)
        if 'Issues:' in content or 'Summary:' in content or 'Keywords:' in content:
            lines = content.split('\n')
            issues = []
            current_issue = None
            current_what = None
            current_why_now = None
            current_context = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Issues: 섹션 시작
                if line.startswith('Issues:'):
                    continue
                
                # 이슈 항목 파싱 (새 형식: 1. [Title] 또는 기존 형식: 1. [Title]: [Description])
                if line and line[0].isdigit() and ('.' in line or ':' in line):
                    # 이전 이슈 저장
                    if current_issue:
                        issues.append({
                            'title': current_issue,
                            'description': current_what or current_context or '',
                            'what': current_what or '',
                            'why_now': current_why_now or '',
                            'context': current_context or ''
                        })
                    
                    # 새 이슈 시작
                    issue_text = line.split('.', 1)[1].strip() if '.' in line else line
                    if ':' in issue_text:
                        # 기존 형식: 1. [Title]: [Description]
                        parts = issue_text.split(':', 1)
                        current_issue = parts[0].strip()
                        current_what = parts[1].strip()
                        current_why_now = None
                        current_context = None
                    else:
                        # 새 형식: 1. [Title] (다음 줄에 What:, Why Now:, Context:)
                        current_issue = issue_text.strip()
                        current_what = None
                        current_why_now = None
                        current_context = None
                
                # What: 섹션
                elif line.startswith('What:') and current_issue:
                    current_what = line.replace('What:', '').strip()
                
                # Why Now: 섹션
                elif line.startswith('Why Now:') and current_issue:
                    current_why_now = line.replace('Why Now:', '').strip()
                
                # Context: 섹션
                elif line.startswith('Context:') and current_issue:
                    current_context = line.replace('Context:', '').strip()
                
                # Topics: 형식 (하위 호환성)
                elif line.startswith('Topics:'):
                    topics_str = line.replace('Topics:', '').strip()
                    result['topics'] = [t.strip() for t in topics_str.split(',') if t.strip()]
                
                # Summary: 형식
                elif line.startswith('Summary:'):
                    summary = line.replace('Summary:', '').strip()
                    result['summary'] = summary
                
                # Keywords: 형식
                elif line.startswith('Keywords:'):
                    keywords_str = line.replace('Keywords:', '').strip()
                    result['keywords'] = [k.strip() for k in keywords_str.split(',') if k.strip()]
            
            # 마지막 이슈 저장
            if current_issue:
                issues.append({
                    'title': current_issue,
                    'description': current_what or current_context or '',
                    'what': current_what or '',
                    'why_now': current_why_now or '',
                    'context': current_context or ''
                })
            
            # 이슈를 topics로 변환 (이슈 제목만)
            if issues:
                result['issues'] = issues
                result['topics'] = [issue['title'] for issue in issues]
                # 첫 번째 이슈의 설명을 전체 summary로 사용 (없는 경우)
                if 'summary' not in result or not result.get('summary'):
                    # why_now가 있으면 그것을 summary로 사용
                    if issues[0].get('why_now'):
                        result['summary'] = issues[0]['why_now']
                    elif issues[0].get('what'):
                        result['summary'] = issues[0]['what']
                    else:
                        result['summary'] = issues[0].get('description', '')
        
        # 한국어 응답 파싱
        else:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 섹션 헤더 감지
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        
                        if '주요 이슈' in key or '주요 주제' in key or 'topics' in key:
                            result['topics'] = [t.strip() for t in value.split(',') if t.strip()]
                        elif '요약' in key or 'summary' in key:
                            result['summary'] = value
                        elif '키워드' in key or 'keywords' in key:
                            keywords = [k.strip() for k in value.split(',') if k.strip()]
                            result['keywords'] = keywords
                        elif '감정' in key or 'sentiment' in key:
                            sentiment = value.lower()
                            if 'positive' in sentiment or '긍정' in sentiment:
                                result['sentiment'] = 'positive'
                            elif 'negative' in sentiment or '부정' in sentiment:
                                result['sentiment'] = 'negative'
                            else:
                                result['sentiment'] = 'neutral'
        
        # 기본값 설정
        if 'keywords' not in result:
            # Keywords가 없으면 Summary에서 추출 시도
            if 'summary' in result and result['summary']:
                # Summary에서 쉼표로 구분된 키워드 추출
                summary = result['summary']
                if ',' in summary:
                    result['keywords'] = [k.strip() for k in summary.split(',')[:10] if k.strip()]
                else:
                    result['keywords'] = []
            else:
                result['keywords'] = []
        
        if 'summary' not in result:
            result['summary'] = content[:200] if content else "분석 결과를 파싱할 수 없습니다."
        
        if 'topics' not in result:
            # Topics가 없으면 Issues에서 추출, 없으면 Keywords에서 추출
            if result.get('issues'):
                result['topics'] = [issue['title'] for issue in result['issues']]
            elif result.get('keywords'):
                result['topics'] = result['keywords'][:5]
            else:
                result['topics'] = []
        
        if 'sentiment' not in result:
            result['sentiment'] = 'neutral'
            
    except Exception as e:
        logger.error(f"❌ AI 응답 파싱 실패: {e}")
        # 파싱 실패 시 기본값 반환
        result = {
            'summary': content[:200] if content else "분석 결과를 파싱할 수 없습니다.",
            'keywords': [],
            'topics': [],
            'sentiment': 'neutral'
        }
    
    return result


async def estimate_news_interest_score(title: str, description: str = "") -> Optional[int]:
    """
    AI를 사용하여 뉴스 기사의 관심도 점수를 추정합니다.
    
    Args:
        title: 뉴스 제목
        description: 뉴스 설명 (선택적)
    
    Returns:
        추정 조회수 (0-100000 범위의 점수를 조회수로 변환)
    """
    if not gemini_model:
        logger.warning("⚠️ Gemini 클라이언트가 초기화되지 않았습니다. 뉴스 관심도 추정을 건너뜁니다.")
        return None
    
    if not title or len(title.strip()) < 5:
        return None
    
    try:
        # 뉴스 관심도 평가 프롬프트
        text_content = f"Title: {title}"
        if description and len(description.strip()) > 10:
            text_content += f"\nDescription: {description[:500]}"
        
        prompt = f"""You are an expert news analyst. Evaluate the potential public interest and viewership for this news article based on its title and description.

Consider these factors:
1. **Newsworthiness**: How important or significant is this news?
2. **Timeliness**: Is this breaking news or a current hot topic?
3. **Relevance**: How relevant is this to a broad audience?
4. **Impact**: How many people would be affected or interested?
5. **Viral Potential**: How likely is this to be shared or discussed?

News Article:
{text_content}

Provide your assessment as a single number from 0 to 100, where:
- 0-20: Low interest (niche topic, limited relevance)
- 21-40: Moderate interest (somewhat relevant)
- 41-60: Good interest (relevant to many people)
- 61-80: High interest (important news, breaking story)
- 81-100: Very high interest (major breaking news, viral potential, widespread impact)

Respond with ONLY a number between 0 and 100, nothing else."""
        
        # Gemini API 호출
        safety_settings = [
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
            {
                "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE
            },
        ]
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # 낮은 온도로 일관성 있는 점수
                    max_output_tokens=10,  # 숫자만 필요하므로 짧게
                ),
                safety_settings=safety_settings
            )
        )
        
        # 응답 파싱
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if candidate.finish_reason == 1:  # STOP (정상 완료)
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        content = candidate.content.parts[0].text.strip()
                    elif hasattr(response, 'text'):
                        content = response.text.strip()
                    else:
                        return None
                    
                    # 숫자만 추출
                    import re
                    numbers = re.findall(r'\d+', content)
                    if numbers:
                        score = int(numbers[0])
                        # 0-100 범위로 제한
                        score = max(0, min(100, score))
                        # 점수를 조회수로 변환 (0-100 점수를 100-10000 조회수로 변환)
                        estimated_views = 100 + (score * 99)  # 100 ~ 10000 범위
                        return estimated_views
        except Exception as e:
            logger.warning(f"⚠️ 뉴스 관심도 점수 파싱 실패: {e}")
            return None
        
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ 뉴스 관심도 추정 실패: {type(e).__name__} - {e}")
        return None


async def get_recent_items_for_analysis(hours: int = 1, limit: int = 1000) -> List[CollectedItem]:  # 100 -> 1000으로 증가 (4M TPM 활용)
    """
    분석할 최근 수집 아이템을 가져옵니다.
    모든 소스 타입을 균등하게 사용하여 다양성 확보
    
    Args:
        hours: 최근 몇 시간 내 데이터
        limit: 최대 개수
    
    Returns:
        CollectedItem 리스트 (소스 다양성을 고려한 샘플링)
    """
    async with AsyncSessionLocal() as session:
        try:
            from datetime import timezone
            import random
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # 1. 모든 소스 타입별로 데이터 개수 확인
            source_type_query = select(
                CollectedItem.source_type,
                func.count(CollectedItem.id)
            ).where(
                CollectedItem.collected_at >= cutoff_time
            ).group_by(CollectedItem.source_type)
            
            source_type_result = await session.execute(source_type_query)
            source_type_counts = dict(source_type_result.all())
            
            if not source_type_counts:
                logger.warning("⚠️ 분석할 데이터가 없습니다.")
                return []
            
            # 2. 소스 타입별로 균등하게 샘플링 (최소 10개씩, 최대 limit/소스타입수)
            items = []
            source_types = list(source_type_counts.keys())
            items_per_source = max(10, limit // len(source_types))
            
            logger.info(f"📊 소스 타입별 데이터 분포: {source_type_counts}")
            
            for source_type in source_types:
                try:
                    # 각 소스 타입에서 최신 데이터 가져오기
                    query = select(CollectedItem).where(
                        CollectedItem.collected_at >= cutoff_time,
                        CollectedItem.source_type == source_type
                    ).order_by(CollectedItem.collected_at.desc()).limit(items_per_source * 2)  # 2배 가져와서 다양성 확보
                    
                    result = await session.execute(query)
                    source_items = list(result.scalars().all())
                    
                    # 랜덤 샘플링으로 다양성 확보 (최신성과 다양성 균형)
                    if len(source_items) > items_per_source:
                        # 최신 50%는 확실히 포함, 나머지 50%는 랜덤 샘플링
                        recent_count = items_per_source // 2
                        recent_items = source_items[:recent_count]
                        random_items = random.sample(source_items[recent_count:], min(items_per_source - recent_count, len(source_items) - recent_count))
                        source_items = recent_items + random_items
                    else:
                        source_items = source_items[:items_per_source]
                    
                    items.extend(source_items)
                    
                    if len(items) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ {source_type} 소스 타입 데이터 조회 실패: {e}")
                    continue
            
            # 3. 최종적으로 limit 개수만큼만 반환 (최신성 우선)
            items = sorted(items, key=lambda x: x.collected_at if x.collected_at else datetime.min, reverse=True)[:limit]
            
            # 소스 타입별 최종 분포 로깅
            final_source_dist = {}
            for item in items:
                final_source_dist[item.source_type] = final_source_dist.get(item.source_type, 0) + 1
            
            logger.info(f"📊 분석 대상: 최근 {hours}시간 내 {len(items)}개 아이템 (소스 분포: {final_source_dist})")
            return items
            
        except Exception as e:
            logger.error(f"❌ 데이터 조회 실패: {type(e).__name__} - {e}")
            return []


async def prepare_text_for_analysis(items: List[CollectedItem]) -> str:
    """
    수집된 아이템들을 분석 가능한 텍스트로 변환합니다.
    모든 소스 타입을 포함하여 더 다양한 분석을 수행합니다.
    """
    texts = []
    
    # 최대 1000개까지 사용 (4M TPM 활용하여 더 많은 데이터로 분석 정확도 향상)
    # 소스 타입별로 균등하게 포함
    max_items = min(1000, len(items))  # 100 -> 1000으로 증가
    selected_items = items[:max_items]
    
    # 소스 타입별 통계
    source_stats = {}
    for item in selected_items:
        source_stats[item.source_type] = source_stats.get(item.source_type, 0) + 1
    
    logger.info(f"📝 분석 텍스트 준비: {len(selected_items)}개 아이템 (소스 분포: {source_stats})")
    
    for item in selected_items:
        # 제목과 내용 모두 사용 (내용 기반 분석)
        title = item.title or ""
        content = item.content or ""
        
        # HTML 엔티티 디코딩
        import html
        title = html.unescape(title)
        content = html.unescape(content)
        
        # 특수 문자 제거 및 정리
        title = title.replace('\n', ' ').replace('\r', ' ').strip()
        content = content.replace('\n', ' ').replace('\r', ' ').strip()
        
        # 소스 타입 정보 포함 (다양성 강조)
        source_type_label = item.source_type.upper()
        
        # 제목과 내용 조합 (내용이 있으면 포함, 4M TPM 활용하여 더 긴 텍스트)
        if content and len(content) > 20:
            # YouTube는 설명이 더 길 수 있으므로 더 많은 텍스트 사용
            if source_type_label == "YOUTUBE":
                # 제목 + 내용 (최대 1000자로 증가)
                text = f"[{source_type_label}] {title[:150]} | {content[:1000]}"
            else:
                # 제목 + 내용 요약 (최대 500자)
                text = f"[{source_type_label}] {title[:150]} | {content[:500]}"
        else:
            # 제목만 사용
            text = f"[{source_type_label}] {title[:200]}"
        
        if text and len(text.strip()) > 10:  # 최소 길이 체크
            texts.append(text)
    
    final_text = "\n".join(texts)
    logger.info(f"📝 분석 텍스트 생성 완료: {len(texts)}개 항목, 총 {len(final_text)}자")
    return final_text


async def calculate_importance_score(topic: str, items: List[CollectedItem]) -> float:
    """
    토픽의 중요도 점수를 계산합니다.
    
    Args:
        topic: 토픽/키워드
        items: 관련 아이템 리스트
    
    Returns:
        중요도 점수 (0.0 ~ 1.0)
    """
    if not items:
        return 0.0
    
    # 1. 언급 횟수 (빈도)
    mention_count = sum(1 for item in items if topic.lower() in item.title.lower() or 
                       (item.content and topic.lower() in item.content.lower()))
    
    # 2. 소스 다양성 (다양한 소스에서 언급되었는지)
    unique_sources = len(set(item.source_type for item in items))
    
    # 3. 최근성 (최근 데이터일수록 높은 점수)
    from datetime import timezone
    now = datetime.now(timezone.utc)
    recency_score = sum(
        1.0 / (1 + (now - (item.collected_at if item.collected_at.tzinfo else item.collected_at.replace(tzinfo=timezone.utc))).total_seconds() / 3600)
        for item in items
    ) / len(items) if items else 0
    
    # 4. 소셜 미디어 참여도 (upvotes, likes 등)
    engagement_score = 0.0
    for item in items:
        if item.extra_data:
            upvotes = item.extra_data.get('upvotes', 0) or 0
            likes = item.extra_data.get('likes', 0) or 0
            views = item.extra_data.get('views', 0) or 0
            engagement_score += (upvotes + likes * 0.5 + views * 0.1) / 1000.0
    
    # 종합 점수 계산 (정규화)
    mention_score = min(mention_count / 10.0, 1.0)  # 최대 10회 언급 = 1.0
    diversity_score = min(unique_sources / 5.0, 1.0)  # 최대 5개 소스 = 1.0
    recency_normalized = min(recency_score, 1.0)
    engagement_normalized = min(engagement_score / len(items) if items else 0, 1.0)
    
    # 가중 평균
    importance = (
        mention_score * 0.3 +
        diversity_score * 0.3 +
        recency_normalized * 0.2 +
        engagement_normalized * 0.2
    )
    
    return min(importance, 1.0)


async def analyze_collected_data(hours: int = 1) -> List[Dict[str, Any]]:
    """
    최근 수집된 데이터를 분석합니다.
    
    Args:
        hours: 분석할 최근 시간 범위
    
    Returns:
        분석 결과 리스트
    """
    if not gemini_model:
        logger.warning("⚠️ Gemini API Key가 설정되지 않아 AI 분석을 건너뜁니다.")
        return []
    
    logger.info("🤖 AI 분석 시작...")
    
    # 1. 최근 수집 데이터 가져오기
    items = await get_recent_items_for_analysis(hours=hours, limit=100)
    
    if not items:
        logger.warning("⚠️ 분석할 데이터가 없습니다.")
        return []
    
    # 2. 텍스트 준비 (내용 포함)
    analysis_text = await prepare_text_for_analysis(items)
    
    if len(analysis_text) < 50:
        logger.warning("⚠️ 분석할 텍스트가 너무 짧습니다.")
        return []
    
    # 3. AI 분석 수행 (내용 기반 이슈 추출)
    ai_result = await analyze_text_with_ai(analysis_text, analysis_type="summary")
    
    if not ai_result:
        logger.error("❌ AI 분석 실패")
        return []
    
    # 4. 각 토픽에 대해 상세 분석
    analysis_results = []
    
    # 이슈 기반 분석 (내용 중심)
    issues = ai_result.get('issues', [])
    topics = ai_result.get('topics', [])
    
    # Issues가 없으면 topics를 이슈로 변환
    if not issues and topics:
        issues = [{'title': topic, 'description': ''} for topic in topics[:5]]
    
    # 키워드만 있는 경우 (하위 호환성)
    if not issues and not topics:
        keywords = ai_result.get('keywords', [])[:5]
        issues = [{'title': kw, 'description': ''} for kw in keywords]
    
    for issue in issues[:10]:  # 최대 10개 이슈만 분석
        issue_title = issue.get('title', '') if isinstance(issue, dict) else str(issue)
        issue_desc = issue.get('description', '') if isinstance(issue, dict) else ''
        
        if not issue_title:
            continue
        
        # 해당 이슈와 관련된 아이템 필터링 (내용 기반 매칭)
        # 소스 타입별로 균등하게 포함하여 출처 다양성 확보
        related_items = []
        issue_keywords = issue_title.lower().split()
        
        # 소스 타입별로 아이템 분류
        items_by_source = {}
        for item in items:
            source_type = item.source_type or 'unknown'
            if source_type not in items_by_source:
                items_by_source[source_type] = []
            items_by_source[source_type].append(item)
        
        # 각 소스 타입별로 최소 1개 이상 포함하도록 매칭
        for source_type, source_items in items_by_source.items():
            source_matched = []
            
            for item in source_items:
                title_lower = (item.title or "").lower()
                content_lower = (item.content or "").lower()
                
                # 이슈 제목의 주요 단어들이 제목이나 내용에 포함되는지 확인
                match_score = 0
                for keyword in issue_keywords:
                    if len(keyword) > 2:  # 2글자 이상인 키워드도 포함 (기존 3글자 → 2글자)
                        if keyword in title_lower:
                            match_score += 2
                        elif keyword in content_lower:
                            match_score += 1
                
                # 최소 1점 이상이면 관련 아이템으로 간주 (기존 2점 → 1점으로 완화)
                if match_score >= 1:
                    source_matched.append((item, match_score))
            
            # 매칭이 안 되면 이슈 제목 자체가 포함된 경우도 포함
            if not source_matched:
                for item in source_items:
                    title_lower = (item.title or "").lower()
                    content_lower = (item.content or "").lower()
                    if issue_title.lower() in title_lower or issue_title.lower() in content_lower:
                        source_matched.append((item, 3))  # 높은 점수 부여
            
            # 각 소스 타입별로 최대 10개까지 점수 순으로 선택
            source_matched.sort(key=lambda x: x[1], reverse=True)
            related_items.extend([item for item, score in source_matched[:10]])
        
        # 전체 아이템에서도 추가 매칭 시도 (소스 타입 무관)
        if len(related_items) < 5:
            for item in items:
                if item in related_items:
                    continue
                title_lower = (item.title or "").lower()
                content_lower = (item.content or "").lower()
                if issue_title.lower() in title_lower or issue_title.lower() in content_lower:
                    related_items.append(item)
        
        if not related_items:
            continue
        
        # 중요도 점수 계산
        importance_score = await calculate_importance_score(issue_title, related_items)
        
        # 관련 아이템 ID 수집
        related_ids = [item.id for item in related_items]
        
        # 분석 결과 생성 (이슈 설명 포함)
        issue_what = issue.get('what', '') if isinstance(issue, dict) else ''
        issue_why_now = issue.get('why_now', '') if isinstance(issue, dict) else ''
        issue_context = issue.get('context', '') if isinstance(issue, dict) else ''
        
        # summary는 why_now가 있으면 우선 사용, 없으면 기존 로직
        summary_text = issue_why_now if issue_why_now else (issue_desc if issue_desc else ai_result.get('summary', ''))
        
        analysis_result = {
            'analysis_type': 'comprehensive',
            'topic': issue_title,  # 이슈 제목을 토픽으로 사용
            'summary': summary_text,
            'keywords': ai_result.get('keywords', []),
            'sentiment': ai_result.get('sentiment', 'neutral'),
            'importance_score': importance_score,
            'source_count': len(set(item.source_type for item in related_items)),
            'collected_item_ids': related_ids,
            'what': issue_what,
            'why_now': issue_why_now,
            'context': issue_context
        }
        
        analysis_results.append(analysis_result)
    
    logger.info(f"✅ AI 분석 완료: {len(analysis_results)}개 토픽 분석됨")
    
    return analysis_results


async def save_analysis_results(analysis_results: List[Dict[str, Any]]) -> int:
    """
    분석 결과를 데이터베이스에 저장합니다.
    
    Args:
        analysis_results: 분석 결과 리스트
    
    Returns:
        저장된 결과 수
    """
    if not analysis_results:
        return 0
    
    saved_count = 0
    async with AsyncSessionLocal() as session:
        try:
            for result in analysis_results:
                # 중복 체크 (같은 토픽이 최근 1시간 내에 분석되었는지)
                one_hour_ago = datetime.now() - timedelta(hours=1)
                existing = await session.execute(
                    select(AnalysisResult).where(
                        AnalysisResult.topic == result['topic'],
                        AnalysisResult.analyzed_at >= one_hour_ago
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # 이미 최근에 분석됨
                
                # AnalysisResult 생성
                analysis_result = AnalysisResult(
                    analysis_type=result.get('analysis_type', 'comprehensive'),
                    topic=result['topic'],
                    summary=result.get('summary', ''),
                    keywords=result.get('keywords', []),
                    sentiment=result.get('sentiment', 'neutral'),
                    importance_score=result.get('importance_score', 0.0),
                    source_count=result.get('source_count', 0),
                    collected_item_ids=result.get('collected_item_ids', []),
                    what=result.get('what', ''),
                    why_now=result.get('why_now', ''),
                    context=result.get('context', '')
                )
                
                session.add(analysis_result)
                saved_count += 1
            
            await session.commit()
            logger.info(f"💾 분석 결과 저장 완료: {saved_count}개")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ 분석 결과 저장 실패: {type(e).__name__} - {e}")
            raise
    
    return saved_count

