"""
뉴스 사이트 RSS 피드를 수집하는 모듈
"""
import httpx
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger("hourly_pulse")

async def fetch_news_rss(url: str, source_name: str) -> List[Dict[str, str]]:
    """
    RSS 피드에서 뉴스 헤드라인을 수집합니다.
    
    Args:
        url: RSS 피드 URL
        source_name: 뉴스 소스 이름 (예: "BBC", "CNN")
    
    Returns:
        뉴스 아이템 리스트 (title, link, pubDate 포함)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    logger.info(f"📰 {source_name} 뉴스 수집 시작...")
    
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            news_items = []
            
            # RSS 구조: channel -> item
            # RSS 네임스페이스 처리 (일부 사이트는 확장 필드 사용)
            namespaces = {
                'slash': 'http://purl.org/rss/1.0/modules/slash/',
                'wfw': 'http://wellformedweb.org/CommentAPI/',
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                description_elem = item.find("description")
                
                # 댓글 수 필드 찾기 (다양한 네임스페이스 시도)
                comments_count = 0
                # 표준 필드
                comments_elem = item.find("comments")
                if comments_elem is not None and comments_elem.text:
                    try:
                        comments_count = int(comments_elem.text)
                    except (ValueError, TypeError):
                        pass
                
                # Slash 네임스페이스 (일부 사이트 사용)
                if comments_count == 0:
                    slash_comments = item.find("slash:comments", namespaces)
                    if slash_comments is not None and slash_comments.text:
                        try:
                            comments_count = int(slash_comments.text)
                        except (ValueError, TypeError):
                            pass
                
                # 기타 확장 필드 시도
                if comments_count == 0:
                    # 모든 자식 요소에서 "comment"가 포함된 필드 찾기
                    for child in item:
                        tag = child.tag.lower() if hasattr(child, 'tag') else ''
                        text = child.text if hasattr(child, 'text') and child.text else ''
                        if 'comment' in tag and text:
                            try:
                                comments_count = int(text)
                                break
                            except (ValueError, TypeError):
                                pass
                
                if title_elem is not None and title_elem.text:
                    news_item = {
                        "source": source_name,
                        "title": title_elem.text.strip(),
                        "url": link_elem.text if link_elem is not None else "",
                        "published": pub_date_elem.text if pub_date_elem is not None else "",
                        "description": description_elem.text if description_elem is not None else "",
                        "comments": comments_count,  # 댓글 수 추가 (있으면)
                        "collected_at": datetime.now().isoformat()
                    }
                    news_items.append(news_item)
            
            logger.info(f"✅ {source_name} 수집 성공! {len(news_items)}개 기사 발견")
            return news_items[:50]  # 상위 50개 반환 (10 -> 50으로 증가, 4K RPM 활용)
            
        except Exception as e:
            logger.error(f"❌ {source_name} 수집 실패: {type(e).__name__} - {e}")
            return []


async def fetch_multiple_news_sources() -> List[Dict[str, str]]:
    """
    여러 뉴스 소스에서 데이터를 수집합니다.
    """
    news_sources = [
        # 국제 뉴스 (작동 확인됨)
        ("https://feeds.bbci.co.uk/news/rss.xml", "BBC"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", "NYTimes"),
        ("https://rss.cbc.ca/lineup/topstories.xml", "CBC"),
        ("https://feeds.washingtonpost.com/rss/world", "WashingtonPost"),
        ("https://www.theguardian.com/world/rss", "TheGuardian"),
        
        # 기술 뉴스 (작동 확인됨)
        ("https://hnrss.org/frontpage", "HackerNews"),
        ("https://techcrunch.com/feed/", "TechCrunch"),
        ("https://www.theverge.com/rss/index.xml", "TheVerge"),
        ("https://www.wired.com/feed/rss", "Wired"),
        ("https://feeds.arstechnica.com/arstechnica/index", "ArsTechnica"),
        ("https://www.engadget.com/rss.xml", "Engadget"),
        
        # 경제 뉴스
        ("https://feeds.bloomberg.com/markets/news.rss", "Bloomberg"),
    ]
    
    all_news = []
    for url, source in news_sources:
        news = await fetch_news_rss(url, source)
        all_news.extend(news)
    
    return all_news

