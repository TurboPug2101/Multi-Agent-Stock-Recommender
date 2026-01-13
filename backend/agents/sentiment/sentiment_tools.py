"""
Sentiment Analysis Tools
Pure business logic functions for sentiment analysis using Groq Qwen model.
No side effects, stateless, and deterministic.
"""

from typing import Optional, List
import logging
from groq import Groq
from .sentiment_schemas import NewsArticle, SentimentAnalysisResult
import re
import json

logger = logging.getLogger(__name__)


def analyze_sentiment_with_groq(
    symbol: str,
    company_name: str,
    news_articles: List[NewsArticle],
    groq_client: Optional[Groq] = None,
    model_name: str = "qwen/qwen3-32b"
) -> Optional[SentimentAnalysisResult]:
    """
    Analyze sentiment of news articles using Groq Qwen reasoning model.
    
    Args:
        symbol: Stock symbol
        company_name: Company name
        news_articles: List of news articles
        groq_client: Optional Groq client instance
        model_name: Groq model name (default: "qwen/qwen3-32b")
    
    Returns:
        SentimentAnalysisResult or None
    """
    if not news_articles:
        logger.warning(f"No news articles found for {symbol}")
        return None
    
    try:
        
        groq_client = Groq()
        
        # Prepare news content for analysis
        news_content = []
        for article in news_articles:
            article_text = f"Title: {article.title}\n"
            if article.description:
                article_text += f"Description: {article.description}\n"
            if article.published_date:
                article_text += f"Date: {article.published_date}\n"
            news_content.append(article_text)
        
        combined_news = "\n\n---\n\n".join(news_content)
        
        # Create prompt for sentiment analysis
        prompt = f"""You are a financial sentiment analysis expert. Analyze the following news articles about {company_name} ({symbol}) from the past 3 months.

News Articles:
{combined_news}

Please provide:
1. A concise summary in 5-7 bullet points highlighting the most important news and developments
2. An overall sentiment assessment: 'very_positive', 'positive', 'neutral', 'negative', or 'very_negative'
3. A sentiment score from -1.0 (very negative) to 1.0 (very positive)
4. A confidence level from 0.0 to 1.0 indicating how confident you are in your assessment
5. Key insights (3-5 points) that would be relevant for investment decisions
6. A final recommendation: 'strong_buy', 'buy', 'hold', 'sell', or 'strong_sell' based on the sentiment

Format your response as JSON with the following structure:
{{
    "summary_points": ["point 1", "point 2", ...],
    "overall_sentiment": "positive",
    "sentiment_score": 0.65,
    "confidence": 0.85,
    "key_insights": ["insight 1", "insight 2", ...],
    "recommendation": "buy"
}}"""

        logger.info(f"Analyzing sentiment for {symbol} using Groq Qwen model...")
        logger.debug(f"Number of news articles: {len(news_articles)}")
        
        # Call Groq API with Qwen reasoning model
        logger.info(f"Using Groq model: {model_name}")
        
        completion = groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_completion_tokens=4096,
            top_p=0.95,
            stream=False
        )
        
        # Extract response
        response_text = completion.choices[0].message.content
        logger.debug(f"Groq response received for {symbol}")

        logger.info(f"response_text : {response_text}")
        
        # Parse JSON response
        import json
        try:
            # Try to extract JSON from response (might have markdown formatting)
            response_text = response_text.strip()

            # Remove markdown
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            # Remove Qwen reasoning
            response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL).strip()
            logger.info(f"response_text after removing Qwen reasoning: {response_text}")
            analysis_data = json.loads(response_text)
            logger.info(f"analysis_data: {analysis_data}")
            
            # Create result
            result = SentimentAnalysisResult(
                symbol=symbol,
                name=company_name,
                news_count=len(news_articles),
                summary_points=analysis_data.get('summary_points', []),
                overall_sentiment=analysis_data.get('overall_sentiment', 'Cant say'),
                sentiment_score=float(analysis_data.get('sentiment_score', 0.0)),
                confidence=float(analysis_data.get('confidence', 0.5)),
                key_insights=analysis_data.get('key_insights', []),
                recommendation=analysis_data.get('recommendation', 'hold')
            )
            
            logger.info(f"✓ {symbol}: Sentiment analyzed - {result.overall_sentiment.upper()}, Score: {result.sentiment_score:.2f}, Recommendation: {result.recommendation.upper()}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {symbol}: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            # Fallback: try to extract information from text
            # return _parse_text_response(symbol, company_name, news_articles, response_text)
            
    except Exception as e:
        logger.error(f"Error analyzing sentiment for {symbol}: {e}", exc_info=True)
        return None

