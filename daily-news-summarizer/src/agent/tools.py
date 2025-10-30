"""
Custom LangChain Tools for News Summarization

Yeh file custom tools define karti hai jo agent use karega:
- Perplexity se news search karne ke liye
- Ollama se filtering karne ke liye
- Ollama se summarization ke liye
- Data save karne ke liye
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
import logging
import json
import os
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


@tool
def search_news_with_perplexity(
    query: str,
    source_name: str = "",
    max_results: int = 5
) -> str:
    """
    Search for news articles using Perplexity API.
    
    Use this tool to fetch latest news articles from various sources.
    Perplexity will intelligently search and return relevant articles.
    
    Args:
        query: Search query (e.g., "latest AI news from TechCrunch")
        source_name: Optional source name to focus search
        max_results: Maximum number of results to return
        
    Returns:
        JSON string with list of articles containing title, url, snippet, and source
    """
    try:
        from ..utils.scraping import fetch_news_from_perplexity
        
        logger.info(f"Searching news with query: {query}")
        
        # Call the actual Perplexity search function
        articles = fetch_news_from_perplexity(
            query=query,
            source_name=source_name,
            max_results=max_results
        )
        
        logger.info(f"Found {len(articles)} articles")
        return json.dumps({
            "status": "success",
            "count": len(articles),
            "articles": articles
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "articles": []
        })


@tool
def filter_articles_with_ollama(
    articles_json: str,
    topics: str,
    keywords: str = ""
) -> str:
    """
    Filter articles based on relevance to topics using Ollama LLM.
    
    Use this tool to identify which articles are relevant to specified topics.
    The LLM will analyze each article and provide a relevance score.
    
    Args:
        articles_json: JSON string containing articles to filter
        topics: Comma-separated list of topics of interest
        keywords: Optional comma-separated list of keywords
        
    Returns:
        JSON string with filtered articles and relevance scores
    """
    try:
        from ..utils.filtering import filter_articles_by_relevance
        
        logger.info(f"Filtering articles for topics: {topics}")
        
        # Parse articles
        articles_data = json.loads(articles_json)
        articles = articles_data.get("articles", [])
        
        # Parse topics and keywords
        topics_list = [t.strip() for t in topics.split(",")]
        keywords_list = [k.strip() for k in keywords.split(",")] if keywords else []
        
        # Filter articles
        filtered = filter_articles_by_relevance(
            articles=articles,
            topics=topics_list,
            keywords=keywords_list
        )
        
        logger.info(f"Filtered to {len(filtered)} relevant articles")
        return json.dumps({
            "status": "success",
            "original_count": len(articles),
            "filtered_count": len(filtered),
            "articles": filtered
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error filtering articles: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "articles": []
        })


@tool
def summarize_articles_with_ollama(articles_json: str) -> str:
    """
    Generate concise summaries for articles using Ollama LLM.
    
    Use this tool to create bullet-point summaries of filtered articles.
    Each article will get a structured summary with key points.
    
    Args:
        articles_json: JSON string containing articles to summarize
        
    Returns:
        JSON string with articles and their summaries
    """
    try:
        from ..utils.summarizing import generate_article_summaries
        
        logger.info("Generating summaries for articles")
        
        # Parse articles
        articles_data = json.loads(articles_json)
        articles = articles_data.get("articles", [])
        
        # Generate summaries
        summarized = generate_article_summaries(articles)
        
        logger.info(f"Generated summaries for {len(summarized)} articles")
        return json.dumps({
            "status": "success",
            "count": len(summarized),
            "summaries": summarized
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating summaries: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e),
            "summaries": []
        })


@tool
def save_raw_data(articles_json: str, filename: str = "") -> str:
    """
    Save raw article data to disk for archival purposes.
    
    Use this tool to store the complete article data before processing.
    Data is saved in JSON format in the data/raw directory.
    
    Args:
        articles_json: JSON string containing articles to save
        filename: Optional custom filename (default: raw_YYYY-MM-DD.json)
        
    Returns:
        Status message with saved file path
    """
    try:
        # Parse articles
        articles_data = json.loads(articles_json)
        
        # Generate filename
        if not filename:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"raw_{date_str}.json"
        
        # Ensure directory exists
        raw_dir = os.path.join("data", "raw")
        os.makedirs(raw_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(raw_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved raw data to {filepath}")
        return json.dumps({
            "status": "success",
            "filepath": filepath,
            "count": len(articles_data.get("articles", []))
        })
        
    except Exception as e:
        logger.error(f"Error saving raw data: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


@tool
def save_summary(summaries_json: str, format_type: str = "both") -> str:
    """
    Save article summaries in CSV and/or Markdown format.
    
    Use this tool to save the final summaries to disk.
    Supports CSV (for analysis) and Markdown (for reading) formats.
    
    Args:
        summaries_json: JSON string containing article summaries
        format_type: Output format - "csv", "markdown", or "both" (default)
        
    Returns:
        Status message with saved file paths
    """
    try:
        import pandas as pd
        
        # Parse summaries
        summaries_data = json.loads(summaries_json)
        summaries = summaries_data.get("summaries", [])
        
        # Generate filename base
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Ensure directory exists
        summary_dir = os.path.join("data", "summaries")
        os.makedirs(summary_dir, exist_ok=True)
        
        saved_files = []
        
        # Save as CSV
        if format_type in ["csv", "both"]:
            csv_path = os.path.join(summary_dir, f"summary_{date_str}.csv")
            df = pd.DataFrame(summaries)
            df.to_csv(csv_path, index=False, encoding="utf-8")
            saved_files.append(csv_path)
            logger.info(f"Saved CSV to {csv_path}")
        
        # Save as Markdown
        if format_type in ["markdown", "both"]:
            md_path = os.path.join(summary_dir, f"summary_{date_str}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(f"# Daily News Summary - {date_str}\n\n")
                for idx, summary in enumerate(summaries, 1):
                    f.write(f"## {idx}. {summary.get('title', 'No Title')}\n\n")
                    f.write(f"**Source:** {summary.get('source', 'Unknown')}\n\n")
                    f.write(f"**URL:** {summary.get('url', 'N/A')}\n\n")
                    f.write(f"**Summary:**\n{summary.get('summary', 'No summary')}\n\n")
                    f.write("---\n\n")
            saved_files.append(md_path)
            logger.info(f"Saved Markdown to {md_path}")
        
        return json.dumps({
            "status": "success",
            "files": saved_files,
            "count": len(summaries)
        })
        
    except Exception as e:
        logger.error(f"Error saving summaries: {str(e)}")
        return json.dumps({
            "status": "error",
            "error": str(e)
        })
