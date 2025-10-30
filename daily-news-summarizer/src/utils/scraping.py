"""
News Scraping Utility using Perplexity API

Yeh module Perplexity API ko use karke news articles fetch karta hai.
Perplexity ek powerful search engine hai jo real-time web data access karta hai.
"""

from typing import List, Dict, Any, Optional
import os
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def fetch_news_from_perplexity(
    query: str,
    source_name: str = "",
    max_results: int = 5,
    time_range: str = "1d"
) -> List[Dict[str, Any]]:
    """
    Fetch news articles using Perplexity API.
    
    Perplexity API ko call karke latest news articles fetch karta hai.
    API real-time web search perform karta hai aur structured results return karta hai.
    
    Args:
        query: Search query (e.g., "AI startup funding news")
        source_name: Optional source name to focus on (e.g., "TechCrunch")
        max_results: Maximum number of articles to return
        time_range: Time range for articles (e.g., "1d", "7d", "1m")
        
    Returns:
        List of article dictionaries with title, url, snippet, source, date
        
    Raises:
        Exception: If API call fails or returns error
    """
    try:
        # Get API key from environment
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        # Construct search query
        search_query = query
        if source_name:
            search_query = f"{query} site:{source_name.lower()}"
        
        # Add time constraint to query
        if time_range:
            search_query = f"{search_query} (published in last {time_range})"
        
        # Perplexity API endpoint
        url = "https://api.perplexity.ai/chat/completions"
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload - use correct Perplexity API parameters
        payload = {
            "model": "sonar",  # Online model for web search
            "messages": [
                {
                    "role": "system",
                    "content": "You are a news aggregator. Return news articles in structured JSON format."
                },
                {
                    "role": "user",
                    "content": f"""Find the {max_results} most recent news articles about: {search_query}

For each article, provide:
- title: Article headline
- url: Article URL
- snippet: Brief excerpt (2-3 sentences)
- source: Publication name
- published_date: Publication date (YYYY-MM-DD format)

Return as JSON array with these fields."""
                }
            ],
            "temperature": 0.2,
            "return_citations": True
        }
        
        logger.info(f"Calling Perplexity API with query: {search_query}")
        
        # Make API call
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Log response for debugging
        if response.status_code != 200:
            logger.error(f"Perplexity API error response: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        
        # Extract articles from response
        articles = _parse_perplexity_response(result, source_name)
        
        logger.info(f"Successfully fetched {len(articles)} articles from Perplexity")
        return articles[:max_results]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling Perplexity API: {str(e)}")
        raise Exception(f"Failed to fetch news from Perplexity: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error fetching news from Perplexity: {str(e)}")
        raise


def _parse_perplexity_response(
    response: Dict[str, Any],
    source_name: str = ""
) -> List[Dict[str, Any]]:
    """
    Parse Perplexity API response and extract article data.
    
    Args:
        response: Raw API response from Perplexity
        source_name: Source name for fallback
        
    Returns:
        List of structured article dictionaries
    """
    articles = []
    
    try:
        # Extract content from response
        choices = response.get("choices", [])
        if not choices:
            logger.warning("No choices in Perplexity response")
            return articles
        
        content = choices[0].get("message", {}).get("content", "")
        citations = response.get("citations", [])
        
        # Try to parse as JSON
        import json
        try:
            # Look for JSON in content
            start_idx = content.find("[")
            end_idx = content.rfind("]") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                parsed_articles = json.loads(json_str)
                
                # Validate and structure articles
                for article in parsed_articles:
                    if isinstance(article, dict):
                        articles.append({
                            "title": article.get("title", "No Title"),
                            "url": article.get("url", ""),
                            "snippet": article.get("snippet", ""),
                            "source": article.get("source", source_name or "Unknown"),
                            "published_date": article.get("published_date", datetime.now().strftime("%Y-%m-%d")),
                            "fetched_at": datetime.now().isoformat()
                        })
        
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from Perplexity response")
        
        # Fallback: Use citations if JSON parsing failed
        if not articles and citations:
            for citation in citations:
                articles.append({
                    "title": _extract_title_from_url(citation),
                    "url": citation,
                    "snippet": content[:200] if content else "",
                    "source": source_name or _extract_domain(citation),
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                    "fetched_at": datetime.now().isoformat()
                })
        
        # If still no articles, create one from content
        if not articles and content:
            articles.append({
                "title": "Perplexity Search Result",
                "url": "",
                "snippet": content[:500],
                "source": source_name or "Perplexity",
                "published_date": datetime.now().strftime("%Y-%m-%d"),
                "fetched_at": datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error parsing Perplexity response: {str(e)}")
    
    return articles


def _extract_title_from_url(url: str) -> str:
    """Extract a readable title from URL."""
    try:
        parts = url.split("/")
        title = parts[-1] if parts[-1] else parts[-2]
        # Clean up
        title = title.replace("-", " ").replace("_", " ")
        return title.title()
    except:
        return "Article"


def _extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain.split(".")[0].title()
    except:
        return "Unknown"


def search_multiple_sources(
    sources: List[Dict[str, Any]],
    topics: List[str],
    max_per_source: int = 5
) -> List[Dict[str, Any]]:
    """
    Search multiple news sources for relevant articles.
    
    Multiple sources se parallel search karta hai aur results combine karta hai.
    
    Args:
        sources: List of source configurations
        topics: List of topics to search for
        max_per_source: Max articles per source
        
    Returns:
        Combined list of articles from all sources
    """
    all_articles = []
    
    for source in sources:
        if not source.get("enabled", True):
            logger.info(f"Skipping disabled source: {source['name']}")
            continue
        
        try:
            # Create search query for this source
            query = f"latest news about {', '.join(topics)}"
            
            articles = fetch_news_from_perplexity(
                query=query,
                source_name=source.get("url", ""),
                max_results=max_per_source
            )
            
            # Add source metadata
            for article in articles:
                article["source_category"] = source.get("category", "general")
                article["source_config"] = source["name"]
            
            all_articles.extend(articles)
            logger.info(f"Fetched {len(articles)} articles from {source['name']}")
            
        except Exception as e:
            logger.error(f"Error fetching from {source['name']}: {str(e)}")
            continue
    
    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles
