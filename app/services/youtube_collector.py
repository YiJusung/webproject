"""
YouTube Data API를 사용하여 트렌딩 동영상을 수집하는 모듈
"""
import httpx
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("hourly_pulse")

async def fetch_youtube_trending(api_key: str = None, region_code: str = "KR") -> List[Dict[str, Any]]:
    """
    YouTube Data API를 사용하여 트렌딩 동영상을 수집합니다.
    
    Args:
        api_key: YouTube Data API Key (환경변수 YOUTUBE_API_KEY에서도 읽음)
        region_code: 지역 코드 (KR=한국, US=미국, 등)
    
    Returns:
        트렌딩 동영상 리스트
    """
    # API Key 가져오기
    key = api_key or os.getenv("YOUTUBE_API_KEY")
    
    if not key:
        logger.warning("⚠️ YouTube API Key가 설정되지 않았습니다. 환경변수 YOUTUBE_API_KEY를 설정하세요.")
        return []
    
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": 50,  # 10 -> 50으로 증가 (4K RPM 활용)
        "key": key
    }
    
    logger.info(f"📺 YouTube 트렌딩 동영상 수집 시작... (지역: {region_code})")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 403:
                logger.error("❌ YouTube API 인증 실패 또는 할당량 초과. API Key를 확인하세요.")
                return []
            elif response.status_code == 400:
                logger.error("❌ YouTube API 요청 오류. 파라미터를 확인하세요.")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            videos = []
            if "items" in data:
                for video in data["items"]:
                    snippet = video.get("snippet", {})
                    stats = video.get("statistics", {})
                    
                    video_item = {
                        "source": "YouTube",
                        "title": snippet.get("title", "")[:200],
                        "description": snippet.get("description", "")[:1000],  # 300 -> 1000자로 확대
                        "url": f"https://www.youtube.com/watch?v={video.get('id', '')}",
                        "channel": snippet.get("channelTitle", ""),
                        "views": int(stats.get("viewCount", 0)),
                        "likes": int(stats.get("likeCount", 0)),
                        "comments": int(stats.get("commentCount", 0)),
                        "published_at": snippet.get("publishedAt", ""),
                        "region": region_code,
                        "collected_at": datetime.now().isoformat()
                    }
                    videos.append(video_item)
            
            if videos:
                logger.info(f"✅ YouTube 수집 성공! {len(videos)}개 동영상 발견")
            return videos
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ YouTube API HTTP 오류 ({e.response.status_code}): {e}")
            return []
        except Exception as e:
            logger.error(f"❌ YouTube 수집 실패: {type(e).__name__} - {e}")
            return []


async def fetch_youtube_search(api_key: str = None, query: str = "trending", max_results: int = 10) -> List[Dict[str, Any]]:
    """
    YouTube에서 특정 키워드로 동영상을 검색합니다.
    
    Args:
        api_key: YouTube Data API Key
        query: 검색 키워드
        max_results: 최대 결과 수
    
    Returns:
        검색 결과 동영상 리스트
    """
    key = api_key or os.getenv("YOUTUBE_API_KEY")
    
    if not key:
        return []
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",  # 조회수 순
        "maxResults": max_results,
        "key": key
    }
    
    logger.info(f"📺 YouTube 검색 수집 시작... (키워드: {query})")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            if "items" in data:
                for video in data["items"]:
                    snippet = video.get("snippet", {})
                    video_item = {
                        "source": f"YouTube ({query})",
                        "title": snippet.get("title", "")[:200],
                        "url": f"https://www.youtube.com/watch?v={video.get('id', {}).get('videoId', '')}",
                        "channel": snippet.get("channelTitle", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "collected_at": datetime.now().isoformat()
                    }
                    videos.append(video_item)
            
            if videos:
                logger.info(f"✅ YouTube 검색 성공! {len(videos)}개 동영상 발견")
            return videos
            
        except Exception as e:
            logger.error(f"❌ YouTube 검색 실패: {type(e).__name__} - {e}")
            return []


