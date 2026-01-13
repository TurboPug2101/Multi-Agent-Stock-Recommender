"""
Social Media Tools
Tools for fetching social media mentions (Twitter, Reddit).
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
from .sentiment_schemas import NewsArticle

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


def fetch_news(
    symbol: str,
    company_name: str,
    days: int = 2,
    **kwargs
) -> List[NewsArticle]:
    """
    Fetch news articles from Event Registry News API.
    
    Args:
        symbol: Stock symbol
        company_name: Company name
        days: Number of days to look back (default: 2)
    
    Returns:
        List of NewsArticle objects
    """
    api_key = os.getenv('NEWS_API_KEY')
    api_url = os.getenv('NEWS_API_URL', 'https://eventregistry.org/api/v1/article/getArticles')
    
    if not api_key:
        logger.warning("NEWS_API_KEY not found. News fetching may fail.")
        return []
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Prepare request body
        request_body = {
            "action": "getArticles",
            "keyword": company_name,
            "sourceLocationUri": ["http://en.wikipedia.org/wiki/India"],
            "ignoreSourceGroupUri": "paywall/paywalled_sources",
            "articlesPage": 1,
            "articlesCount": 10,
            "articlesSortBy": "date",
            "articlesSortByAsc": False,
            "dataType": ["news", "pr"],
            "forceMaxDataTimeWindow": days,
            "resultType": "articles",
            "apiKey": api_key,
            "dateStart": start_date.strftime("%Y-%m-%d"),
            "dateEnd": end_date.strftime("%Y-%m-%d"),
            "includeArticleTitle": True,
            "includeArticleBody": True,
            "includeArticleSentiment": True,
            "includeArticleImage": True,
            "includeArticleAuthors": True,
            "includeSourceTitle": True
        }
        
        logger.info(f"Fetching news for {company_name} ({symbol}) from NewsAPI...")
        
        # Make API request
        response = requests.post(
            api_url,
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"NewsAPI request failed with status {response.status_code}: {response.text}")
            return []
        
        data = response.json()
        
        # Parse response
        articles = []
        if 'articles' in data and 'results' in data['articles']:
            for item in data['articles']['results']:
                try:
                    published_date = None
                    if item.get("dateTimePub"):
                        published_date = datetime.fromisoformat(
                            item["dateTimePub"].replace("Z", "+00:00")
                        ).isoformat()
                    
                    source_name = item["source"]["title"]
                    
                    article = NewsArticle(
                        title=item.get('title', ''),
                        description=item.get('body', '')[:500] if item.get('body') else None,
                        published_date=published_date,
                        source=source_name
                    )
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
                    continue
            
            logger.info(f"Fetched {len(articles)} news articles for {company_name}")
        else:
            logger.warning(f"No articles found in response for {company_name}")
        
        return articles
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from NewsAPI for {company_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching news for {company_name}: {e}", exc_info=True)
        return []


@dataclass
class SocialMention:
    """Represents a social media mention."""
    platform: str
    text: str
    author: Optional[str] = None
    timestamp: Optional[str] = None
    url: Optional[str] = None
    engagement: Optional[Dict[str, int]] = None  # likes, retweets, comments, etc.
    
    def to_news_article(self) -> NewsArticle:
        """Convert to NewsArticle format for compatibility."""
        return NewsArticle(
            title=f"{self.platform} mention",
            description=self.text,
            published_date=self.timestamp,
            source=self.platform
        )


def fetch_twitter_mentions(
    symbol: str,
    company_name: str,
    days: int = 30,
    max_results: int = 50
) -> List[SocialMention]:
    """
    Fetch Twitter/X mentions about a stock.
    
    TODO: Implement Twitter API integration when API access is available.
    Currently redirects to Reddit as a fallback.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS")
        company_name: Company name
        days: Number of days to look back
        max_results: Maximum number of results to return
    
    Returns:
        List of SocialMention objects (from Reddit as fallback)
    """
    logger.warning("Twitter API integration is WIP. Redirecting to Reddit API instead.")
    logger.info(f"Agent requested Twitter mentions for {symbol}, using Reddit as alternative")
    
    # Redirect to Reddit
    return fetch_reddit_mentions(symbol, company_name, days, max_results)


def fetch_reddit_mentions(
    symbol: str,
    company_name: str,
    days: int = 30,
    max_results: int = 50
) -> List[SocialMention]:
    """
    Fetch Reddit mentions about a stock.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS")
        company_name: Company name
        days: Number of days to look back
        max_results: Maximum number of results to return
    
    Returns:
        List of SocialMention objects
    """
    logger.info(f"Fetching Reddit mentions for {symbol} ({company_name})")
    
    try:
        # Reddit API (no auth required for read-only)
        # Search in relevant subreddits
        subreddits = ["stocks", "investing", "StockMarket", "IndianStockMarket"]
        
        mentions = []
        
        for subreddit in subreddits:
            try:
                # Reddit search API
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                
                # Build search query
                query = f"{company_name} OR {symbol}"
                
                params = {
                    "q": query,
                    "restrict_sr": "true",
                    "limit": min(25, max_results // len(subreddits)),
                    "sort": "relevance",
                    "t": "month" if days <= 30 else "year"
                }
                
                headers = {
                    "User-Agent": "TradingAgent/1.0 (by /u/tradingagent)"
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Reddit API error for r/{subreddit}: {response.status_code}")
                    continue
                
                data = response.json()
                posts = data.get("data", {}).get("children", [])
                
                for post_data in posts:
                    post = post_data.get("data", {})
                    
                    # Check if post is within time range
                    created_utc = post.get("created_utc", 0)
                    post_date = datetime.fromtimestamp(created_utc)
                    if (datetime.now() - post_date).days > days:
                        continue
                    
                    mention = SocialMention(
                        platform=f"reddit/r/{subreddit}",
                        text=f"{post.get('title', '')} - {post.get('selftext', '')[:500]}",
                        author=post.get("author", "unknown"),
                        timestamp=post_date.isoformat(),
                        url=f"https://reddit.com{post.get('permalink', '')}",
                        engagement={
                            "upvotes": post.get("ups", 0),
                            "comments": post.get("num_comments", 0),
                            "score": post.get("score", 0)
                        }
                    )
                    mentions.append(mention)
                    
                    if len(mentions) >= max_results:
                        break
                
                if len(mentions) >= max_results:
                    break
                    
            except Exception as e:
                logger.warning(f"Error fetching from r/{subreddit}: {e}")
                continue
        
        logger.info(f"Fetched {len(mentions)} Reddit mentions for {symbol}")
        return mentions[:max_results]
        
    except Exception as e:
        logger.error(f"Error fetching Reddit mentions for {symbol}: {e}", exc_info=True)
        return []


def fetch_gnews_articles(
    symbol: str,
    company_name: str,
    days: int = 90,
    max_results: int = 50
) -> List[NewsArticle]:
    """
    Fetch news articles from GNews API.
    
    Args:
        symbol: Stock symbol
        company_name: Company name
        days: Number of days to look back
        max_results: Maximum number of results
    
    Returns:
        List of NewsArticle objects
    """
    logger.info(f"Fetching GNews articles for {symbol} ({company_name})")
    
    api_key = os.getenv('GNEWS_API_KEY')
    if not api_key:
        logger.warning("GNEWS_API_KEY not found. GNews articles will be skipped.")
        return []
    
    try:
        # GNews API endpoint
        url = "https://gnews.io/api/v4/search"
        
        # Build query
        query = f"{company_name} {symbol}"
        
        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        params = {
            "q": query,
            "token": api_key,
            "lang": "en",
            "max": min(max_results, 100),
            "from": from_date,
            "sortby": "publishedAt"
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"GNews API error: {response.status_code} - {response.text}")
            return []
        
        data = response.json()
        articles_data = data.get("articles", [])
        
        articles = []
        for article_data in articles_data:
            article = NewsArticle(
                title=article_data.get("title", ""),
                description=article_data.get("description", ""),
                published_date=article_data.get("publishedAt"),
                source=article_data.get("source", {}).get("name", "GNews")
            )
            articles.append(article)
        
        logger.info(f"Fetched {len(articles)} GNews articles for {symbol}")
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching GNews articles for {symbol}: {e}", exc_info=True)
        return []
