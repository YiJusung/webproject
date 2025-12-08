"""
Twitter/X API를 사용하여 트렌딩 데이터를 수집하는 모듈
"""
import httpx
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("hourly_pulse")

async def fetch_twitter_trends(bearer_token: str = None) -> List[Dict[str, Any]]:
    """
    Twitter/X API를 사용하여 트렌딩 토픽을 수집합니다.
    
    Args:
        bearer_token: Twitter Bearer Token (환경변수 TWITTER_BEARER_TOKEN에서도 읽음)
    
    Returns:
        트렌딩 토픽 리스트
    """
    # Bearer Token 가져오기
    token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    
    if not token:
        logger.warning("⚠️ Twitter Bearer Token이 설정되지 않았습니다. 환경변수 TWITTER_BEARER_TOKEN을 설정하세요.")
        return []
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "HourlyPulse/1.0"
    }
    
    # 트렌딩 토픽 조회 (WOEID: 1 = 전세계, 23424868 = 한국)
    # 참고: Twitter API v2는 트렌딩 토픽 엔드포인트가 제한적입니다
    # 대안: 트윗 검색 API 사용
    url = "https://api.twitter.com/2/tweets/search/recent"
    
    # 최근 인기 트윗 검색 (예: 높은 좋아요 수)
    params = {
        "query": "lang:en -is:retweet",  # 영어, 리트윗 제외
        "max_results": 10,
        "tweet.fields": "public_metrics,created_at,text",
        "sort_order": "relevancy"
    }
    
    logger.info("🐦 Twitter/X 트렌딩 데이터 수집 시작...")
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            
            if response.status_code == 401:
                logger.error("❌ Twitter API 인증 실패. Bearer Token을 확인하세요.")
                return []
            elif response.status_code == 429:
                logger.warning("⚠️ Twitter API 요청 한도 초과. 잠시 후 다시 시도하세요.")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            trends = []
            if "data" in data:
                for tweet in data["data"]:
                    metrics = tweet.get("public_metrics", {})
                    trend_item = {
                        "source": "Twitter/X",
                        "title": tweet.get("text", "")[:200],  # 최대 200자
                        "url": f"https://twitter.com/i/web/status/{tweet.get('id', '')}",
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "replies": metrics.get("reply_count", 0),
                        "created_at": tweet.get("created_at", ""),
                        "collected_at": datetime.now().isoformat()
                    }
                    trends.append(trend_item)
            
            if trends:
                logger.info(f"✅ Twitter/X 수집 성공! {len(trends)}개 트윗 발견")
            return trends
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Twitter API HTTP 오류 ({e.response.status_code}): {e}")
            if e.response.status_code == 403:
                logger.error("💡 Twitter API v2 Basic 접근 권한이 필요합니다. https://developer.twitter.com/ 에서 확인하세요.")
            return []
        except Exception as e:
            logger.error(f"❌ Twitter/X 수집 실패: {type(e).__name__} - {e}")
            return []


async def fetch_twitter_hashtags(bearer_token: str = None, hashtag: str = "trending") -> List[Dict[str, Any]]:
    """
    특정 해시태그의 트윗을 수집합니다.
    
    Args:
        bearer_token: Twitter Bearer Token
        hashtag: 검색할 해시태그 (예: "trending", "news", "tech")
    
    Returns:
        트윗 리스트
    """
    token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    
    if not token:
        return []
    
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "HourlyPulse/1.0"
    }
    
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"#{hashtag} -is:retweet lang:en",
        "max_results": 10,
        "tweet.fields": "public_metrics,created_at,text"
    }
    
    logger.info(f"🐦 Twitter 해시태그 #{hashtag} 수집 시작...")
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            tweets = []
            
            if "data" in data:
                for tweet in data["data"]:
                    metrics = tweet.get("public_metrics", {})
                    tweet_item = {
                        "source": f"Twitter #{hashtag}",
                        "title": tweet.get("text", "")[:200],
                        "url": f"https://twitter.com/i/web/status/{tweet.get('id', '')}",
                        "hashtag": hashtag,
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "collected_at": datetime.now().isoformat()
                    }
                    tweets.append(tweet_item)
            
            if tweets:
                logger.info(f"✅ Twitter #{hashtag} 수집 성공! {len(tweets)}개 트윗 발견")
            return tweets
            
        except Exception as e:
            logger.error(f"❌ Twitter #{hashtag} 수집 실패: {type(e).__name__} - {e}")
            return []


