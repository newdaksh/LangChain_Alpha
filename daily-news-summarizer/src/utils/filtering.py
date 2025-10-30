"""
Article Filtering Utility using Ollama LLM

Yeh module Ollama LLM ka use karke articles ko filter karta hai.
LLM-based filtering se hum accurately relevant articles identify kar sakte hain.
"""

from typing import List, Dict, Any, Optional
import os
import logging
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


def filter_articles_by_relevance(
    articles: List[Dict[str, Any]],
    topics: List[str],
    keywords: List[str] = None,
    min_score: float = 0.6,
    use_llm: bool = True
) -> List[Dict[str, Any]]:
    """
    Filter articles based on relevance to topics using Ollama LLM.
    
    LLM ko use karke har article ki relevance analyze karta hai.
    Relevant articles ko score ke saath return karta hai.
    
    Args:
        articles: List of article dictionaries to filter
        topics: List of relevant topics
        keywords: Optional list of important keywords
        min_score: Minimum relevance score (0.0 to 1.0)
        use_llm: Whether to use LLM for filtering (True) or keyword matching (False)
        
    Returns:
        List of filtered articles with relevance scores
    """
    if not articles:
        logger.warning("No articles to filter")
        return []
    
    if use_llm:
        return _filter_with_llm(articles, topics, keywords, min_score)
    else:
        return _filter_with_keywords(articles, topics, keywords, min_score)


def _filter_with_llm(
    articles: List[Dict[str, Any]],
    topics: List[str],
    keywords: List[str],
    min_score: float
) -> List[Dict[str, Any]]:
    """
    Use Ollama LLM to analyze article relevance.
    
    LLM se har article ko analyze karwate hain aur relevance score lete hain.
    """
    try:
        # Initialize Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        llm = ChatOllama(
            base_url=ollama_url,
            model=ollama_model,
            temperature=0.1  # Low temperature for consistent filtering
        )
        
        filtered_articles = []
        
        logger.info(f"Filtering {len(articles)} articles using LLM")
        
        # Process each article
        for idx, article in enumerate(articles, 1):
            try:
                # Prepare content for analysis
                content = f"""
Title: {article.get('title', 'No title')}
Snippet: {article.get('snippet', 'No snippet')}
Source: {article.get('source', 'Unknown')}
"""
                
                # Create prompt for LLM
                system_msg = SystemMessage(content="""You are an expert content analyzer. 
Your job is to determine if a news article is relevant to specified topics.
Return ONLY a JSON object with: {"relevant": true/false, "score": 0.0-1.0, "reason": "brief explanation"}
Be strict but fair in your assessment.""")
                
                topics_str = ", ".join(topics)
                keywords_str = ", ".join(keywords) if keywords else "None specified"
                
                human_msg = HumanMessage(content=f"""Analyze this article:

{content}

Topics of Interest: {topics_str}
Keywords: {keywords_str}

Is this article relevant? Provide relevance score (0.0-1.0) and brief reason.
Return JSON only: {{"relevant": boolean, "score": float, "reason": string}}""")
                
                # Get LLM response
                response = llm.invoke([system_msg, human_msg])
                response_text = response.content
                
                # Parse response
                result = _parse_llm_response(response_text)
                
                relevance_score = result.get("score", 0.0)
                is_relevant = result.get("relevant", False)
                reason = result.get("reason", "No reason provided")
                
                # Add to filtered list if meets threshold
                if is_relevant and relevance_score >= min_score:
                    article["relevance_score"] = relevance_score
                    article["relevance_reason"] = reason
                    article["filter_method"] = "llm"
                    filtered_articles.append(article)
                    logger.debug(f"Article {idx} relevant (score: {relevance_score:.2f})")
                else:
                    logger.debug(f"Article {idx} filtered out (score: {relevance_score:.2f})")
                
            except Exception as e:
                logger.error(f"Error filtering article {idx}: {str(e)}")
                # On error, use fallback keyword filtering
                if _keyword_match(article, topics, keywords):
                    article["relevance_score"] = 0.7
                    article["relevance_reason"] = "Keyword match (LLM failed)"
                    article["filter_method"] = "keyword_fallback"
                    filtered_articles.append(article)
        
        logger.info(f"LLM filtering: {len(filtered_articles)}/{len(articles)} articles passed")
        return filtered_articles
        
    except Exception as e:
        logger.error(f"Error in LLM filtering: {str(e)}")
        logger.warning("Falling back to keyword filtering")
        return _filter_with_keywords(articles, topics, keywords, min_score)


def _filter_with_keywords(
    articles: List[Dict[str, Any]],
    topics: List[str],
    keywords: List[str],
    min_score: float
) -> List[Dict[str, Any]]:
    """
    Simple keyword-based filtering as fallback.
    
    Keywords aur topics ko match karke articles filter karta hai.
    """
    filtered_articles = []
    
    logger.info(f"Filtering {len(articles)} articles using keyword matching")
    
    for article in articles:
        if _keyword_match(article, topics, keywords):
            # Calculate simple score based on matches
            score = _calculate_keyword_score(article, topics, keywords)
            
            if score >= min_score:
                article["relevance_score"] = score
                article["relevance_reason"] = "Keyword match"
                article["filter_method"] = "keyword"
                filtered_articles.append(article)
    
    logger.info(f"Keyword filtering: {len(filtered_articles)}/{len(articles)} articles passed")
    return filtered_articles


def _keyword_match(
    article: Dict[str, Any],
    topics: List[str],
    keywords: List[str]
) -> bool:
    """Check if article matches any topic or keyword."""
    # Combine title and snippet for matching
    text = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
    
    # Check topics
    for topic in topics:
        if topic.lower() in text:
            return True
    
    # Check keywords
    if keywords:
        for keyword in keywords:
            if keyword.lower() in text:
                return True
    
    return False


def _calculate_keyword_score(
    article: Dict[str, Any],
    topics: List[str],
    keywords: List[str]
) -> float:
    """Calculate relevance score based on keyword matches."""
    text = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
    
    # Count matches
    topic_matches = sum(1 for topic in topics if topic.lower() in text)
    keyword_matches = sum(1 for kw in keywords if kw.lower() in text) if keywords else 0
    
    # Calculate score (weighted)
    total_items = len(topics) + (len(keywords) if keywords else 0)
    if total_items == 0:
        return 0.5
    
    score = ((topic_matches * 2) + keyword_matches) / (total_items * 2)
    return min(score, 1.0)


def _parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response to extract relevance information."""
    try:
        # Try to find JSON in response
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)
            
            # Validate required fields
            if "relevant" in result and "score" in result:
                return result
        
        # Fallback: Try to extract info from text
        relevant = "relevant" in response_text.lower() and "not relevant" not in response_text.lower()
        
        # Try to extract score
        import re
        score_match = re.search(r'(\d+\.\d+)', response_text)
        score = float(score_match.group(1)) if score_match else (0.7 if relevant else 0.3)
        
        return {
            "relevant": relevant,
            "score": score,
            "reason": "Parsed from text response"
        }
        
    except Exception as e:
        logger.error(f"Error parsing LLM response: {str(e)}")
        return {
            "relevant": False,
            "score": 0.0,
            "reason": "Parse error"
        }


def apply_exclude_filters(
    articles: List[Dict[str, Any]],
    exclude_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Remove articles containing excluded keywords.
    
    Args:
        articles: List of articles
        exclude_keywords: Keywords that indicate irrelevant content
        
    Returns:
        Filtered list without excluded articles
    """
    if not exclude_keywords:
        return articles
    
    filtered = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
        
        # Check if any exclude keyword present
        has_excluded = any(kw.lower() in text for kw in exclude_keywords)
        
        if not has_excluded:
            filtered.append(article)
        else:
            logger.debug(f"Excluded article: {article.get('title', 'No title')}")
    
    logger.info(f"Excluded {len(articles) - len(filtered)} articles")
    return filtered
