"""
Article Summarization Utility using Ollama LLM

Yeh module Ollama LLM ka use karke articles ke concise summaries generate karta hai.
Bullet-point format mein structured summaries create karta hai.
"""

from typing import List, Dict, Any, Optional
import os
import logging
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


def generate_article_summaries(
    articles: List[Dict[str, Any]],
    summary_style: str = "bullet_points"
) -> List[Dict[str, Any]]:
    """
    Generate concise summaries for articles using Ollama LLM.
    
    Har article ke liye structured summary generate karta hai.
    Key points aur insights extract karta hai.
    
    Args:
        articles: List of article dictionaries to summarize
        summary_style: Style of summary - "bullet_points", "paragraph", or "brief"
        
    Returns:
        List of articles with added summary field
    """
    if not articles:
        logger.warning("No articles to summarize")
        return []
    
    try:
        # Initialize Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        llm = ChatOllama(
            base_url=ollama_url,
            model=ollama_model,
            temperature=0.4  # Moderate temperature for creative but focused summaries
        )
        
        summarized_articles = []
        
        logger.info(f"Generating summaries for {len(articles)} articles")
        
        for idx, article in enumerate(articles, 1):
            try:
                # Prepare content
                title = article.get("title", "No title")
                snippet = article.get("snippet", "")
                source = article.get("source", "Unknown")
                
                # Create summary prompt based on style
                summary = _generate_summary_with_llm(
                    llm=llm,
                    title=title,
                    snippet=snippet,
                    source=source,
                    style=summary_style
                )
                
                # Add summary to article
                article["summary"] = summary
                article["summary_style"] = summary_style
                article["summarized_at"] = _get_timestamp()
                
                summarized_articles.append(article)
                logger.debug(f"Summarized article {idx}/{len(articles)}")
                
            except Exception as e:
                logger.error(f"Error summarizing article {idx}: {str(e)}")
                # Add fallback summary
                article["summary"] = _generate_fallback_summary(article)
                article["summary_style"] = "fallback"
                summarized_articles.append(article)
        
        logger.info(f"Successfully summarized {len(summarized_articles)} articles")
        return summarized_articles
        
    except Exception as e:
        logger.error(f"Error in summarization process: {str(e)}")
        # Return articles with fallback summaries
        return [_add_fallback_summary(a) for a in articles]


def _generate_summary_with_llm(
    llm: ChatOllama,
    title: str,
    snippet: str,
    source: str,
    style: str
) -> str:
    """
    Use LLM to generate summary in specified style.
    """
    # Define style-specific instructions
    style_instructions = {
        "bullet_points": """Generate a summary with 3-5 bullet points.
Each point should be concise and capture a key insight.
Format:
• Point 1
• Point 2
• Point 3""",
        
        "paragraph": """Generate a concise paragraph (3-4 sentences) summarizing the article.
Focus on the main message and key takeaways.""",
        
        "brief": """Generate a one-sentence summary capturing the essence of the article."""
    }
    
    instruction = style_instructions.get(style, style_instructions["bullet_points"])
    
    # Create messages
    system_msg = SystemMessage(content="""You are an expert news summarizer.
Your summaries are concise, informative, and highlight key insights.
Focus on facts and actionable information.
Avoid fluff and marketing speak.""")
    
    human_msg = HumanMessage(content=f"""Summarize this news article:

Title: {title}
Source: {source}
Content: {snippet}

{instruction}

Summary:""")
    
    # Generate summary
    response = llm.invoke([system_msg, human_msg])
    summary = response.content.strip()
    
    return summary


def _generate_fallback_summary(article: Dict[str, Any]) -> str:
    """Generate simple fallback summary when LLM fails."""
    snippet = article.get("snippet", "")
    
    if len(snippet) > 200:
        return snippet[:200] + "..."
    elif snippet:
        return snippet
    else:
        return f"Article from {article.get('source', 'Unknown source')}: {article.get('title', 'No title')}"


def _add_fallback_summary(article: Dict[str, Any]) -> Dict[str, Any]:
    """Add fallback summary to article."""
    article["summary"] = _generate_fallback_summary(article)
    article["summary_style"] = "fallback"
    return article


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()


def generate_digest_summary(
    articles: List[Dict[str, Any]],
    digest_style: str = "executive"
) -> str:
    """
    Generate an overall digest summary of all articles.
    
    Multiple articles ko combine karke ek high-level summary banata hai.
    Email ya notifications ke liye useful hai.
    
    Args:
        articles: List of summarized articles
        digest_style: Style - "executive" (brief), "detailed", or "highlights"
        
    Returns:
        Overall digest summary as string
    """
    if not articles:
        return "No articles to summarize."
    
    try:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        llm = ChatOllama(
            base_url=ollama_url,
            model=ollama_model,
            temperature=0.5
        )
        
        # Prepare input
        articles_text = "\n\n".join([
            f"{idx}. {article.get('title', 'No title')}\n   {article.get('summary', 'No summary')}"
            for idx, article in enumerate(articles, 1)
        ])
        
        # Style-specific prompts
        if digest_style == "executive":
            prompt = f"""Create a brief executive summary (3-4 sentences) of today's news:

{articles_text}

Executive Summary:"""
        
        elif digest_style == "detailed":
            prompt = f"""Create a detailed digest of today's news, organized by themes:

{articles_text}

Detailed Digest:"""
        
        else:  # highlights
            prompt = f"""List the top 5 highlights from today's news:

{articles_text}

Top Highlights:
1."""
        
        system_msg = SystemMessage(content="You are a news editor creating daily digests.")
        human_msg = HumanMessage(content=prompt)
        
        response = llm.invoke([system_msg, human_msg])
        digest = response.content.strip()
        
        logger.info(f"Generated {digest_style} digest summary")
        return digest
        
    except Exception as e:
        logger.error(f"Error generating digest: {str(e)}")
        # Fallback
        return f"Today's news covers {len(articles)} articles on various topics."


def format_summary_for_email(
    articles: List[Dict[str, Any]],
    include_digest: bool = True
) -> str:
    """
    Format summaries for email delivery.
    
    Email-friendly HTML/text format mein summaries format karta hai.
    
    Args:
        articles: List of summarized articles
        include_digest: Whether to include overall digest
        
    Returns:
        Formatted string ready for email
    """
    from datetime import datetime
    
    output = []
    
    # Header
    date_str = datetime.now().strftime("%B %d, %Y")
    output.append(f"📰 Daily News Digest - {date_str}")
    output.append("=" * 60)
    output.append("")
    
    # Digest summary
    if include_digest and articles:
        digest = generate_digest_summary(articles, "executive")
        output.append("🔍 Executive Summary:")
        output.append(digest)
        output.append("")
        output.append("-" * 60)
        output.append("")
    
    # Individual articles
    output.append(f"📌 {len(articles)} Articles Today:")
    output.append("")
    
    for idx, article in enumerate(articles, 1):
        output.append(f"{idx}. {article.get('title', 'No Title')}")
        output.append(f"   Source: {article.get('source', 'Unknown')}")
        
        if article.get('url'):
            output.append(f"   Link: {article['url']}")
        
        output.append(f"\n   Summary:")
        summary = article.get('summary', 'No summary available')
        # Indent summary
        for line in summary.split('\n'):
            output.append(f"   {line}")
        
        if article.get('relevance_score'):
            output.append(f"   Relevance: {article['relevance_score']:.0%}")
        
        output.append("")
    
    # Footer
    output.append("-" * 60)
    output.append("Generated by Daily News Summarizer")
    
    return "\n".join(output)


def format_summary_for_markdown(articles: List[Dict[str, Any]]) -> str:
    """
    Format summaries in Markdown format.
    
    Args:
        articles: List of summarized articles
        
    Returns:
        Markdown formatted string
    """
    from datetime import datetime
    
    output = []
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    output.append(f"# Daily News Summary - {date_str}\n")
    
    # Digest
    if articles:
        digest = generate_digest_summary(articles, "highlights")
        output.append("## 📋 Today's Highlights\n")
        output.append(digest)
        output.append("\n---\n")
    
    # Articles
    output.append(f"## 📰 Articles ({len(articles)})\n")
    
    for idx, article in enumerate(articles, 1):
        output.append(f"### {idx}. {article.get('title', 'No Title')}\n")
        output.append(f"**Source:** {article.get('source', 'Unknown')}  ")
        
        if article.get('url'):
            output.append(f"**URL:** [{article['url']}]({article['url']})  ")
        
        if article.get('published_date'):
            output.append(f"**Date:** {article['published_date']}  ")
        
        output.append(f"\n**Summary:**\n")
        output.append(article.get('summary', 'No summary'))
        output.append("\n")
        
        if article.get('relevance_score'):
            output.append(f"*Relevance Score: {article['relevance_score']:.0%}*\n")
        
        output.append("---\n")
    
    return "\n".join(output)
