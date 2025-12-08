"""
GitHub Trending 저장소를 수집하는 모듈
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger("hourly_pulse")

async def fetch_github_trending(language: str = None, days: int = 7) -> List[Dict[str, str]]:
    """
    GitHub의 인기 저장소를 수집합니다.
    
    Args:
        language: 프로그래밍 언어 필터 (예: "python", "javascript", None=전체)
        days: 최근 며칠간의 데이터 (기본 7일)
    
    Returns:
        인기 저장소 리스트
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "HourlyPulse/1.0"
    }
    
    # 최근 N일간 생성된 저장소 중 스타가 많은 순
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"created:>{since_date} sort:stars"
    if language:
        query += f" language:{language}"
    
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=100"  # 10 -> 100으로 증가 (4K RPM 활용)
    
    logger.info(f"💻 GitHub Trending 수집 시작... (언어: {language or '전체'})")
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            trending_repos = []
            
            for repo in data.get("items", [])[:100]:  # 10 -> 100으로 증가
                repo_item = {
                    "source": "GitHub",
                    "title": repo.get("full_name", ""),
                    "description": repo.get("description", ""),
                    "url": repo.get("html_url", ""),
                    "language": repo.get("language", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),  # 포크 수 추가
                    "watchers": repo.get("watchers_count", 0),  # 워처 수 추가
                    "collected_at": datetime.now().isoformat()
                }
                trending_repos.append(repo_item)
            
            logger.info(f"✅ GitHub Trending 수집 성공! {len(trending_repos)}개 저장소 발견")
            return trending_repos
            
        except Exception as e:
            logger.error(f"❌ GitHub Trending 수집 실패: {type(e).__name__} - {e}")
            return []


