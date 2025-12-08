"""
텍스트 번역 서비스 (Gemini API 사용)
"""
import os
import logging
import asyncio
from typing import Optional, Dict
from functools import lru_cache
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("hourly_pulse")

# 간단한 번역 캐시 (메모리 기반)
_translation_cache: Dict[str, str] = {}

# Gemini 클라이언트 초기화
gemini_model = None
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
    logger.info("✅ Gemini 번역 클라이언트 초기화 완료")
else:
    logger.warning("⚠️ GEMINI_API_KEY가 설정되지 않았습니다. 번역 기능이 작동하지 않습니다.")


async def translate_text(text: str, target_language: str = "ko") -> Optional[str]:
    """
    텍스트를 지정된 언어로 번역합니다.
    
    Args:
        text: 번역할 텍스트
        target_language: 목표 언어 ("ko" 또는 "en")
    
    Returns:
        번역된 텍스트
    """
    if not text or len(text.strip()) < 3:
        return text  # 너무 짧은 텍스트는 번역하지 않음
    
    # 캐시 확인
    cache_key = f"{target_language}:{text[:100]}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    if not gemini_model:
        logger.warning("⚠️ Gemini 클라이언트가 초기화되지 않았습니다.")
        return text  # 번역 실패 시 원본 반환
    
    # 이미 목표 언어인지 확인 (간단한 휴리스틱)
    if target_language == "en" and all(ord(c) < 128 for c in text[:100]):
        # 영어로 보이는 텍스트
        _translation_cache[cache_key] = text
        return text
    if target_language == "ko" and any('\uac00' <= c <= '\ud7a3' for c in text[:100]):
        # 한글이 포함된 텍스트
        _translation_cache[cache_key] = text
        return text
    
    try:
        target_lang_name = "Korean" if target_language == "ko" else "English"
        
        prompt = f"""Translate the following text to {target_lang_name}. 
Keep the meaning and tone accurate. If the text is already in {target_lang_name}, return it as is.

Text to translate:
{text[:2000]}

Translation:"""
        
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
                    temperature=0.3,  # 번역은 정확성이 중요
                    max_output_tokens=1000,
                ),
                safety_settings=safety_settings
            )
        )
        
        # Gemini 응답에서 텍스트 추출
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content.parts:
                    translated = candidate.content.parts[0].text.strip()
                    # 캐시에 저장
                    _translation_cache[cache_key] = translated
                    return translated
            elif hasattr(response, 'text'):
                translated = response.text.strip()
                _translation_cache[cache_key] = translated
                return translated
        except Exception as e:
            logger.error(f"❌ 번역 응답 처리 실패: {e}")
        
        # 번역 실패 시 원본 반환 및 캐시
        _translation_cache[cache_key] = text
        return text
        
    except Exception as e:
        logger.error(f"❌ 번역 실패: {type(e).__name__} - {e}")
        return text  # 번역 실패 시 원본 반환


async def translate_list(texts: list, target_language: str = "ko") -> list:
    """
    텍스트 리스트를 일괄 번역합니다.
    
    Args:
        texts: 번역할 텍스트 리스트
        target_language: 목표 언어
    
    Returns:
        번역된 텍스트 리스트
    """
    if not texts:
        return []
    
    # 짧은 텍스트들은 한 번에 번역 (효율성)
    if len(texts) <= 5:
        translated = []
        for text in texts:
            if text:
                result = await translate_text(text, target_language)
                translated.append(result)
            else:
                translated.append(text)
        return translated
    else:
        # 많은 텍스트는 원본 반환 (성능 고려)
        return texts

