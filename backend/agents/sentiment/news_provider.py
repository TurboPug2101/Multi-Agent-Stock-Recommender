"""
News Data Provider Interface
Abstracts news data provider implementation to decouple business logic from data sources.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import logging
from .sentiment_schemas import NewsArticle

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


# class NewsDataProvider(ABC):
#     """Abstract interface for news data providers."""
    
#     @abstractmethod
#     def fetch_news(self, symbol: str, company_name: str, days: int = 90) -> List[NewsArticle]:
#         """
#         Fetch news articles for a stock.
        
#         Args:
#             symbol: Stock symbol
#             company_name: Company name
#             days: Number of days to look back (default 90 for 3 months)
        
#         Returns:
#             List of NewsArticle objects
#         """
#         pass


# class NewsAPIProvider(NewsDataProvider):
#     """
#     Event Registry News API implementation.
#     Uses Event Registry API (api.eventregistry.org) to fetch news articles.
#     """
    
#     def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
#         """
#         Initialize Event Registry News API provider.
        
#         Args:
#             api_key: Event Registry API key (optional, can be set via NEWS_API_KEY env var)
#             api_url: API endpoint URL (optional, can be set via NEWS_API_URL env var, defaults to Event Registry endpoint)
#         """
#         self.api_key = api_key or os.getenv('NEWS_API_KEY')
#         self.api_url = api_url or os.getenv('NEWS_API_URL', 'https://eventregistry.org/api/v1/article/getArticles')
        
#         if not self.api_key:
#             logger.warning("NEWS_API_KEY not found. News fetching may fail.")
    
#     def fetch_news(self, symbol: str, company_name: str, days: int = 14) -> List[NewsArticle]:
#         """
#         Fetch news articles for a stock using NewsAPI.
        
#         Args:
#             symbol: Stock symbol
#             company_name: Company name
#             days: Number of days to look back (default 90 for 3 months)
        
#         Returns:
#             List of NewsArticle objects
#         """
#         if not self.api_key:
#             logger.error("NewsAPI key not configured")
#             return []
        
#         try:
#             # Calculate date range
#             end_date = datetime.now()
#             start_date = end_date - timedelta(days=days)
        
#             # Prepare request body
#             request_body = {
#                 "action": "getArticles",
#                 "keyword": company_name,  # Use company name as primary keyword
#                 "sourceLocationUri": [
#                     "http://en.wikipedia.org/wiki/India"
#                 ],
#                 "ignoreSourceGroupUri": "paywall/paywalled_sources",
#                 "articlesPage": 1,
#                 "articlesCount": 10,  
#                 "articlesSortBy": "date",
#                 "articlesSortByAsc": False,
#                 "dataType": ["news", "pr"],
#                 "forceMaxDataTimeWindow": days,
#                 "resultType": "articles",
#                 "apiKey": self.api_key,
#                 "dateStart": start_date.strftime("%Y-%m-%d"),
#                 "dateEnd": end_date.strftime("%Y-%m-%d"),
#                 "includeArticleTitle": True,
#                 "includeArticleBody": True,
#                 "includeArticleSentiment": True,
#                 "includeArticleImage": True,
#                 "includeArticleAuthors": True,
#                 "includeSourceTitle": True
#             }
            
#             logger.info(f"Fetching news for {company_name} ({symbol}) from NewsAPI...")
#             logger.debug(f"Request: {request_body}")
            
#             # Make API request
#             response = requests.post(
#                 self.api_url,
#                 json=request_body,
#                 headers={"Content-Type": "application/json"},
#                 timeout=30
#             )
            
#             if response.status_code != 200:
#                 logger.error(f"NewsAPI request failed with status {response.status_code}: {response.text}")
#                 return []
            
#             data = response.json()
            
#             # Parse response
#             articles = []
#             if 'articles' in data and 'results' in data['articles']:
#                 for item in data['articles']['results']:
#                     try:
#                         published_date = None

#                         # Prefer publication time
#                         if item.get("dateTimePub"):
#                             published_date = datetime.fromisoformat(
#                                 item["dateTimePub"].replace("Z", "+00:00")
#                             ).isoformat()
                        
#                         source_name = item["source"]["title"]
                        
#                         article = NewsArticle(
#                             title=item.get('title', ''),
#                             description=item.get('body', '')[:500] if item.get('body') else None, 
#                             published_date=published_date,
#                             source=source_name
#                         )
#                         articles.append(article)
#                     except Exception as e:
#                         logger.warning(f"Error parsing article: {e}")
#                         continue
                
#                 logger.info(f"Fetched {len(articles)} news articles for {company_name}")
                
#                 logger.info(f"Total articles fetched: {len(articles)}")
#             else:
#                 logger.warning(f"No articles found in response for {company_name}")
            
#             return articles
            
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Error fetching news from NewsAPI for {company_name}: {e}")
#             return []
#         except Exception as e:
#             logger.error(f"Unexpected error fetching news for {company_name}: {e}", exc_info=True)
#             return []
