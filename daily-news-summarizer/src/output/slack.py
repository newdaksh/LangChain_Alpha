"""
Slack Integration Module

Yeh module summaries ko Slack mein post karta hai.
Webhook ke through formatted messages send karta hai.
"""

from typing import List, Dict, Any, Optional
import os
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack notifier for daily news summaries.
    
    Incoming webhooks ke through Slack mein messages post karta hai.
    """
    
    def __init__(self, webhook_url: str = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack incoming webhook URL
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
    
    def send_daily_summary(
        self,
        articles: List[Dict[str, Any]],
        channel: str = None
    ) -> bool:
        """
        Send daily summary to Slack channel.
        
        Args:
            articles: List of summarized articles
            channel: Optional channel override
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        try:
            # Create Slack message
            message = self._create_slack_message(articles, channel)
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            
            logger.info("Sent daily summary to Slack")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending to Slack: {str(e)}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False
    
    def _create_slack_message(
        self,
        articles: List[Dict[str, Any]],
        channel: str = None
    ) -> Dict[str, Any]:
        """
        Create formatted Slack message with blocks.
        """
        date_str = datetime.now().strftime("%B %d, %Y")
        
        # Start with header
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📰 Daily News Digest - {date_str}",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            }
        ]
        
        # Add digest summary
        if articles:
            from utils.summarizing import generate_digest_summary
            digest = generate_digest_summary(articles, "executive")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔍 Executive Summary*\n{digest}"
                }
            })
            blocks.append({"type": "divider"})
        
        # Add article count
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📌 {len(articles)} Articles Today*"
            }
        })
        
        # Add articles (limit to top 10 to avoid message size limits)
        for idx, article in enumerate(articles[:10], 1):
            title = article.get('title', 'No Title')
            source = article.get('source', 'Unknown')
            url = article.get('url', '')
            summary = article.get('summary', 'No summary')
            relevance = article.get('relevance_score', 0)
            
            # Format summary (take first 200 chars if too long)
            if len(summary) > 200:
                summary = summary[:200] + "..."
            
            # Create article block
            article_text = f"*{idx}. {title}*\n"
            article_text += f"_Source: {source}"
            
            if relevance > 0:
                article_text += f" | Relevance: {relevance:.0%}"
            
            article_text += f"_\n{summary}"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": article_text
                }
            })
            
            # Add button to read more if URL available
            if url:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Read More →",
                                "emoji": True
                            },
                            "url": url,
                            "action_id": f"read_article_{idx}"
                        }
                    ]
                })
            
            blocks.append({"type": "divider"})
        
        # Add footer
        if len(articles) > 10:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Showing top 10 of {len(articles)} articles_"
                    }
                ]
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Generated by Daily News Summarizer | Powered by LangChain, Perplexity & Ollama_"
                }
            ]
        })
        
        # Create message
        message = {
            "blocks": blocks
        }
        
        if channel:
            message["channel"] = channel
        
        return message
    
    def send_simple_notification(
        self,
        text: str,
        title: str = None
    ) -> bool:
        """
        Send a simple text notification to Slack.
        
        Args:
            text: Message text
            title: Optional title
            
        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        try:
            message = {
                "text": text
            }
            
            if title:
                message["blocks"] = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": title
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text
                        }
                    }
                ]
            
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info("Sent notification to Slack")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def send_error_notification(self, error_message: str) -> bool:
        """
        Send error notification to Slack.
        
        Args:
            error_message: Error description
            
        Returns:
            True if sent successfully
        """
        return self.send_simple_notification(
            text=f"⚠️ *Error in Daily News Summarizer*\n```{error_message}```",
            title="Error Alert"
        )


def send_to_slack(
    articles: List[Dict[str, Any]],
    webhook_url: str = None
) -> bool:
    """
    Convenience function to send articles to Slack.
    
    Args:
        articles: List of summarized articles
        webhook_url: Optional webhook URL override
        
    Returns:
        True if sent successfully
    """
    notifier = SlackNotifier(webhook_url)
    return notifier.send_daily_summary(articles)


def notify_completion(success: bool = True, article_count: int = 0) -> bool:
    """
    Send a simple completion notification.
    
    Args:
        success: Whether the process completed successfully
        article_count: Number of articles processed
        
    Returns:
        True if sent successfully
    """
    notifier = SlackNotifier()
    
    if success:
        text = f"✅ Daily news summary completed successfully!\n📊 Processed {article_count} articles."
    else:
        text = "❌ Daily news summary failed. Check logs for details."
    
    return notifier.send_simple_notification(text)
