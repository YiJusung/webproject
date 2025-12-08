"""
개별 수집기 테스트
각 수집기가 정상 작동하는지 확인합니다.
"""
import asyncio
import sys
from app.services.collector import fetch_google_trends, fetch_reddit_subreddit
from app.services.news_collector import fetch_multiple_news_sources
from app.services.github_collector import fetch_github_trending
from app.services.youtube_collector import fetch_youtube_trending

# Windows에서 SelectorEventLoop 사용
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_collectors():
    """
    각 수집기를 개별적으로 테스트합니다.
    """
    print("=" * 70)
    print("📥 개별 수집기 테스트")
    print("=" * 70)
    
    # 1. Reddit Popular
    print("\n🔴 [1] Reddit Popular 수집 테스트")
    print("-" * 70)
    try:
        reddit_trends = await fetch_google_trends()
        if reddit_trends:
            print(f"✅ 성공: {len(reddit_trends)}개 수집")
            for i, trend in enumerate(reddit_trends[:3], 1):
                print(f"  {i}. {trend}")
        else:
            print("⚠️  수집된 데이터가 없습니다.")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 2. Reddit 서브레딧
    print("\n🔴 [2] Reddit 서브레딧 수집 테스트 (r/technology)")
    print("-" * 70)
    try:
        subreddit_posts = await fetch_reddit_subreddit("technology", limit=5)
        if subreddit_posts:
            print(f"✅ 성공: {len(subreddit_posts)}개 수집")
            for i, post in enumerate(subreddit_posts[:3], 1):
                title = post.get('title', 'N/A')[:60]
                print(f"  {i}. {title}...")
                print(f"     Upvotes: {post.get('upvotes', 0)}")
        else:
            print("⚠️  수집된 데이터가 없습니다.")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 3. 뉴스 수집
    print("\n📰 [3] 뉴스 수집 테스트")
    print("-" * 70)
    try:
        news_items = await fetch_multiple_news_sources()
        if news_items:
            print(f"✅ 성공: {len(news_items)}개 수집")
            # 소스별 개수
            sources = {}
            for item in news_items:
                source = item.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"  소스별 개수:")
            for source, count in list(sources.items())[:5]:
                print(f"    - {source}: {count}개")
            
            # 샘플 출력
            print(f"\n  샘플 (상위 3개):")
            for i, item in enumerate(news_items[:3], 1):
                title = item.get('title', 'N/A')[:50]
                print(f"    {i}. [{item.get('source', 'N/A')}] {title}...")
        else:
            print("⚠️  수집된 데이터가 없습니다.")
    except Exception as e:
        print(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. GitHub Trending
    print("\n💻 [4] GitHub Trending 수집 테스트")
    print("-" * 70)
    try:
        github_repos = await fetch_github_trending()
        if github_repos:
            print(f"✅ 성공: {len(github_repos)}개 수집")
            for i, repo in enumerate(github_repos[:3], 1):
                name = repo.get('title', 'N/A')
                stars = repo.get('stars', 0)
                print(f"  {i}. {name} (⭐ {stars})")
        else:
            print("⚠️  수집된 데이터가 없습니다.")
    except Exception as e:
        print(f"❌ 실패: {e}")
    
    # 5. YouTube Trending
    print("\n📺 [5] YouTube Trending 수집 테스트")
    print("-" * 70)
    try:
        youtube_videos = await fetch_youtube_trending(region_code="KR")
        if youtube_videos:
            print(f"✅ 성공: {len(youtube_videos)}개 수집")
            for i, video in enumerate(youtube_videos[:3], 1):
                title = video.get('title', 'N/A')[:50]
                views = video.get('views', 0)
                print(f"  {i}. {title}...")
                print(f"     조회수: {views:,}")
        else:
            print("⚠️  수집된 데이터가 없습니다. (API Key 확인 필요)")
    except Exception as e:
        print(f"❌ 실패: {e}")
        print("  (YouTube API Key가 설정되지 않았을 수 있습니다)")
    
    print("\n" + "=" * 70)
    print("✅ 개별 수집기 테스트 완료!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_collectors())




