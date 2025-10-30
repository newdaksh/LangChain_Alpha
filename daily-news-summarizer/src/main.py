"""
Main Entry Point for Daily News Summarizer

Yeh file main workflow orchestrate karti hai:
1. Configuration load karna
2. Agent setup karna  
3. News fetch aur summarize karna
4. Email/Slack bhejana
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# from agent.agents import create_news_agent
from utils.scraping import search_multiple_sources
from utils.filtering import filter_articles_by_relevance, apply_exclude_filters
from utils.summarizing import generate_article_summaries
from output.emailer import send_daily_digest
from output.slack import send_to_slack, notify_completion


# Configure logging with UTF-8 encoding for Windows
import sys
import io

# Set stdout to use UTF-8 encoding to handle emojis on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_summarizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to JSON config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {str(e)}")
        raise


def save_results(
    articles: List[Dict[str, Any]],
    output_format: str = "both"
) -> None:
    """
    Save results to disk in specified format(s).
    
    Args:
        articles: List of articles with summaries
        output_format: "csv", "markdown", or "both"
    """
    import pandas as pd
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Ensure directories exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/summaries", exist_ok=True)
    
    # Save raw data as JSON
    raw_path = f"data/raw/raw_{date_str}.json"
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw data to {raw_path}")
    
    # Save summaries as CSV
    if output_format in ["csv", "both"]:
        csv_path = f"data/summaries/summary_{date_str}.csv"
        df = pd.DataFrame(articles)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Saved summary CSV to {csv_path}")
    
    # Save summaries as Markdown
    if output_format in ["markdown", "both"]:
        from utils.summarizing import format_summary_for_markdown
        
        md_path = f"data/summaries/summary_{date_str}.md"
        md_content = format_summary_for_markdown(articles)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        logger.info(f"Saved summary Markdown to {md_path}")


def run_workflow(
    sources_config: Dict[str, Any],
    topics_config: Dict[str, Any],
    send_email: bool = True,
    send_slack: bool = False
) -> Dict[str, Any]:
    """
    Run the complete news summarization workflow.
    
    Yeh function puri process ko execute karta hai step by step.
    
    Args:
        sources_config: Sources configuration
        topics_config: Topics configuration
        send_email: Whether to send email digest
        send_slack: Whether to send Slack notification
        
    Returns:
        Summary of results
    """
    results = {
        "status": "started",
        "timestamp": datetime.now().isoformat(),
        "articles_found": 0,
        "articles_filtered": 0,
        "articles_summarized": 0
    }
    
    try:
        logger.info("=" * 60)
        logger.info("Starting Daily News Summarization Workflow")
        logger.info("=" * 60)
        
        # Step 1: Fetch news from sources using Perplexity
        logger.info("\n📡 Step 1: Fetching news from sources...")
        sources = sources_config.get("sources", [])
        topics = topics_config.get("topics", [])
        max_per_source = sources_config.get("search_settings", {}).get("max_results_per_source", 5)
        
        articles = search_multiple_sources(
            sources=sources,
            topics=topics,
            max_per_source=max_per_source
        )
        
        results["articles_found"] = len(articles)
        logger.info(f"✓ Found {len(articles)} articles")
        
        if not articles:
            logger.warning("No articles found. Exiting.")
            results["status"] = "completed_no_articles"
            return results
        
        # Step 2: Filter articles using Ollama LLM
        logger.info("\n🔍 Step 2: Filtering articles by relevance...")
        keywords = topics_config.get("keywords", [])
        min_score = topics_config.get("filtering_settings", {}).get("min_relevance_score", 0.6)
        use_llm = topics_config.get("filtering_settings", {}).get("use_llm_filtering", True)
        
        filtered_articles = filter_articles_by_relevance(
            articles=articles,
            topics=topics,
            keywords=keywords,
            min_score=min_score,
            use_llm=use_llm
        )
        
        # Apply exclude filters
        exclude_keywords = topics_config.get("exclude_keywords", [])
        if exclude_keywords:
            filtered_articles = apply_exclude_filters(filtered_articles, exclude_keywords)
        
        results["articles_filtered"] = len(filtered_articles)
        logger.info(f"✓ Filtered to {len(filtered_articles)} relevant articles")
        
        if not filtered_articles:
            logger.warning("No relevant articles after filtering.")
            results["status"] = "completed_no_relevant"
            return results
        
        # Step 3: Generate summaries using Ollama
        logger.info("\n📝 Step 3: Generating summaries...")
        summarized_articles = generate_article_summaries(
            articles=filtered_articles,
            summary_style="bullet_points"
        )
        
        results["articles_summarized"] = len(summarized_articles)
        logger.info(f"✓ Generated {len(summarized_articles)} summaries")
        
        # Step 4: Save results
        logger.info("\n💾 Step 4: Saving results...")
        save_results(summarized_articles, output_format="both")
        logger.info("✓ Results saved")
        
        # Step 5: Send email digest
        if send_email:
            logger.info("\n📧 Step 5: Sending email digest...")
            try:
                email_sent = send_daily_digest(
                    articles=summarized_articles,
                    include_attachments=True
                )
                results["email_sent"] = email_sent
                if email_sent:
                    logger.info("✓ Email sent successfully")
                else:
                    logger.warning("✗ Email sending failed")
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                results["email_sent"] = False
        
        # Step 6: Send Slack notification
        if send_slack:
            logger.info("\n💬 Step 6: Sending Slack notification...")
            try:
                slack_sent = send_to_slack(summarized_articles)
                results["slack_sent"] = slack_sent
                if slack_sent:
                    logger.info("✓ Slack notification sent")
                else:
                    logger.warning("✗ Slack sending failed")
            except Exception as e:
                logger.error(f"Error sending to Slack: {str(e)}")
                results["slack_sent"] = False
        
        results["status"] = "completed_success"
        logger.info("\n" + "=" * 60)
        logger.info("✅ Workflow completed successfully!")
        logger.info(f"📊 Summary: {results['articles_found']} found, "
                   f"{results['articles_filtered']} filtered, "
                   f"{results['articles_summarized']} summarized")
        logger.info("=" * 60)
        
        # Send completion notification
        if send_slack:
            notify_completion(success=True, article_count=len(summarized_articles))
        
        return results
        
    except Exception as e:
        logger.error(f"\n❌ Error in workflow: {str(e)}", exc_info=True)
        results["status"] = "error"
        results["error"] = str(e)
        
        # Send error notification
        if send_slack:
            notify_completion(success=False)
        
        return results


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Daily News Summarizer - Automated news aggregation with LangChain"
    )
    parser.add_argument(
        "--sources",
        default="config/sources.json",
        help="Path to sources configuration file"
    )
    parser.add_argument(
        "--topics",
        default="config/topics.json",
        help="Path to topics configuration file"
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip sending email digest"
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Send Slack notification"
    )
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Send test email and exit"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Test email if requested
    if args.test_email:
        from output.emailer import EmailSender
        sender = EmailSender()
        success = sender.send_test_email()
        sys.exit(0 if success else 1)
    
    # Load configurations
    try:
        sources_config = load_config(args.sources)
        topics_config = load_config(args.topics)
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)
    
    # Run workflow
    results = run_workflow(
        sources_config=sources_config,
        topics_config=topics_config,
        send_email=not args.no_email,
        send_slack=args.slack
    )
    
    # Exit with appropriate code
    if results["status"] == "completed_success":
        sys.exit(0)
    elif results["status"] in ["completed_no_articles", "completed_no_relevant"]:
        sys.exit(0)  # Not an error, just no results
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
