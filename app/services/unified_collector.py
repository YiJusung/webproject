"""
모든 데이터 소스를 통합하여 수집하는 모듈
"""
import logging
from datetime import datetime
from typing import List, Dict, Any
from app.services.collector import fetch_google_trends, fetch_reddit_subreddit
from app.services.news_collector import fetch_multiple_news_sources
from app.services.github_collector import fetch_github_trending
from app.services.youtube_collector import fetch_youtube_trending, fetch_youtube_search

logger = logging.getLogger("hourly_pulse")

async def collect_all_sources() -> Dict[str, List[Dict[str, Any]]]:
    """
    모든 데이터 소스에서 정보를 수집합니다.
    
    Returns:
        소스별로 분류된 데이터 딕셔너리
    """
    logger.info("🚀 전체 데이터 수집 시작...")
    
    collected_data = {
        "reddit": [],
        "reddit_subreddits": [],
        "news": [],
        "github": [],
        "youtube": []
    }
    
    # 1. Reddit Popular 수집
    try:
        reddit_posts = await fetch_google_trends()  # 이제 딕셔너리 리스트 반환
        collected_data["reddit"] = reddit_posts  # 직접 할당 (이미 딕셔너리 형태)
        logger.info(f"✅ Reddit Popular: {len(collected_data['reddit'])}개 수집")
    except Exception as e:
        logger.error(f"❌ Reddit Popular 수집 실패: {e}")
    
    # 2. Reddit 특정 서브레딧 수집 (4K RPM 활용하여 수집량 증가)
    try:
        subreddits = ["worldnews", "technology", "korea", "news", "programming", "science", "business", "politics", "entertainment", "gaming"]
        all_subreddit_posts = []
        for subreddit in subreddits:
            posts = await fetch_reddit_subreddit(subreddit, limit=50)  # 5 -> 50으로 증가
            all_subreddit_posts.extend(posts)
        collected_data["reddit_subreddits"] = all_subreddit_posts
        logger.info(f"✅ Reddit 서브레딧: {len(collected_data['reddit_subreddits'])}개 수집")
    except Exception as e:
        logger.error(f"❌ Reddit 서브레딧 수집 실패: {e}")
    
    # 3. 뉴스 수집
    try:
        news_items = await fetch_multiple_news_sources()
        collected_data["news"] = news_items
        logger.info(f"✅ 뉴스: {len(collected_data['news'])}개 수집")
    except Exception as e:
        logger.error(f"❌ 뉴스 수집 실패: {e}")
    
    # 4. GitHub Trending 수집
    try:
        github_repos = await fetch_github_trending()
        collected_data["github"] = github_repos
        logger.info(f"✅ GitHub: {len(collected_data['github'])}개 수집")
    except Exception as e:
        logger.error(f"❌ GitHub 수집 실패: {e}")
    
    # 5. YouTube 수집
    try:
        youtube_trending = await fetch_youtube_trending(region_code="KR")
        # 검색도 추가 (선택적)
        # youtube_search = await fetch_youtube_search(query="trending")
        collected_data["youtube"] = youtube_trending
        logger.info(f"✅ YouTube: {len(collected_data['youtube'])}개 수집")
    except Exception as e:
        logger.error(f"❌ YouTube 수집 실패: {e}")
    
    total_items = sum(len(items) for items in collected_data.values())
    logger.info(f"📊 전체 수집 완료! 총 {total_items}개 아이템")
    
    return collected_data

