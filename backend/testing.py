"""
Simple test script - just shows RAW JSON response
"""

import requests
import json
from datetime import datetime, timedelta

# CONFIGURATION
API_KEY = "5afba31c-a8f1-448b-b025-c03852f0f565"  # ← REPLACE THIS
API_URL = "https://eventregistry.org/api/v1/article/getArticles"

COMPANY_NAME = "Reliance Industries"
DAYS_BACK = 30

# Calculate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

# Request body
request_body = {
    "action": "getArticles",
    "keyword": COMPANY_NAME,
    "sourceLocationUri": ["http://en.wikipedia.org/wiki/India"],
    "ignoreSourceGroupUri": "paywall/paywalled_sources",
    "articlesPage": 1,
    "articlesCount": 5,  # Just 5 articles
    "articlesSortBy": "date",
    "articlesSortByAsc": False,
    "dataType": ["news", "pr"],
    "dateStart": start_date.strftime("%Y-%m-%d"),
    "dateEnd": end_date.strftime("%Y-%m-%d"),
    "includeArticleTitle": True,
    "includeArticleBody": True,
    "includeArticleSentiment": True,
    "includeArticleImage": True,
    "includeArticleAuthors": True,
    "includeSourceTitle": True,
    "apiKey": API_KEY
}

print("Sending request...\n")

try:
    response = requests.post(API_URL, json=request_body, timeout=30)
    
    print(f"Status Code: {response.status_code}\n")
    print("="*80)
    print("RAW JSON RESPONSE:")
    print("="*80)
    
    # Pretty print the entire response
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"Error: {e}")