import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("hourly_pulse")

async def fetch_reddit_subreddit(subreddit: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Reddit 특정 서브레딧에서 인기 게시물을 수집합니다.
    
    Args:
        subreddit: 서브레딧 이름 (예: "worldnews", "technology", "korea")
        limit: 수집할 게시물 수
    
    Returns:
        게시물 정보 리스트 (title, url, upvotes 등 포함)
    """
    headers = {
        "User-Agent": "HourlyPulse/1.0 (by /u/hourlypulse)"
    }
    
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    
    logger.info(f"🔴 Reddit r/{subreddit} 수집 시작...")
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            if "data" in data and "children" in data["data"]:
                for post_data in data["data"]["children"]:
                    post = post_data.get("data", {})
                    if post.get("title"):
                        post_item = {
                            "source": f"Reddit r/{subreddit}",
                            "title": post.get("title", "")[:200],  # 최대 200자
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "upvotes": post.get("ups", 0),
                            "comments": post.get("num_comments", 0),
                            "subreddit": subreddit,
                            "collected_at": datetime.now().isoformat()
                        }
                        posts.append(post_item)
            
            if posts:
                logger.info(f"✅ r/{subreddit} 수집 성공! {len(posts)}개 게시물 발견")
            return posts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ r/{subreddit} HTTP 오류 ({e.response.status_code}): {e}")
            return []
        except Exception as e:
            logger.error(f"❌ r/{subreddit} 수집 실패: {type(e).__name__} - {e}")
            return []


async def fetch_google_trends() -> List[Dict[str, Any]]:
    """
    Reddit의 인기 게시물을 가져와서 트렌딩 토픽 리스트를 반환합니다.
    구글 트렌드 RSS가 더 이상 제공되지 않아 Reddit API로 대체했습니다.
    API Key가 필요 없어 바로 테스트하기 좋습니다.
    
    Returns:
        인기 게시물 정보 리스트 (title, url, upvotes, comments 포함)
    """
    # Reddit API는 User-Agent가 필수입니다
    headers = {
        "User-Agent": "HourlyPulse/1.0 (by /u/hourlypulse)"
    }
    
    # Reddit의 인기 게시물 (r/popular 또는 특정 서브레딧)
    # JSON 형식으로 반환됩니다 (4K RPM 활용하여 수집량 증가)
    url = "https://www.reddit.com/r/popular/hot.json?limit=50"  # 10 -> 50으로 증가
    
    logger.info("🌍 Reddit 인기 게시물 데이터 수집 시작...")
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            # Reddit JSON 구조: data -> children -> data -> title, upvotes, comments 등
            posts = []
            if "data" in data and "children" in data["data"]:
                for post_data in data["data"]["children"]:
                    post = post_data.get("data", {})
                    if post.get("title"):
                        title = post.get("title", "")
                        # 너무 긴 제목은 잘라내기
                        if len(title) > 200:
                            title = title[:197] + "..."
                        
                        post_item = {
                            "source": "Reddit Popular",
                            "title": title,
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "upvotes": post.get("ups", 0),
                            "comments": post.get("num_comments", 0),  # 댓글 수 추가
                            "subreddit": post.get("subreddit", "popular"),
                            "collected_at": datetime.now().isoformat()
                        }
                        posts.append(post_item)
            
            if posts:
                logger.info(f"✅ 수집 성공! 총 {len(posts)}개의 인기 게시물을 찾았습니다.")
                return posts[:50]  # 상위 50개 반환
            else:
                logger.warning("⚠️ 데이터를 찾을 수 없습니다.")
                return []
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP 오류 ({e.response.status_code}): {e}")
            return []
        except Exception as e:
            logger.error(f"❌ 수집 중 에러 발생: {type(e).__name__} - {e}")
            return []

