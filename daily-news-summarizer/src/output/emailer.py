"""
Email Delivery Module

Yeh module daily summaries ko email ke through deliver karta hai.
SMTP ke through professional looking emails send karta hai.
"""

from typing import List, Dict, Any, Optional
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Email sender for daily news summaries.
    
    SMTP ke through formatted emails send karta hai with attachments support.
    """
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        email_from: str = None
    ):
        """
        Initialize email sender with SMTP configuration.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            email_from: Sender email address
        """
        # Load from environment if not provided
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.email_from = email_from or os.getenv("EMAIL_FROM", self.smtp_user)
        
        # Validate configuration
        if not all([self.smtp_user, self.smtp_password]):
            logger.warning("Email credentials not fully configured")
    
    def send_daily_summary(
        self,
        articles: List[Dict[str, Any]],
        recipients: List[str] = None,
        include_attachments: bool = False
    ) -> bool:
        """
        Send daily summary email to recipients.
        
        Args:
            articles: List of summarized articles
            recipients: List of recipient email addresses
            include_attachments: Whether to attach CSV/JSON files
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Get recipients from env if not provided
            if not recipients:
                email_to = os.getenv("EMAIL_TO", "")
                recipients = [r.strip() for r in email_to.split(",") if r.strip()]
            
            if not recipients:
                logger.error("No recipients specified")
                return False
            
            # Create email
            msg = self._create_email_message(articles, recipients)
            
            # Add attachments if requested
            if include_attachments:
                self._add_attachments(msg)
            
            # Send email
            return self._send_email(msg, recipients)
            
        except Exception as e:
            logger.error(f"Error sending daily summary email: {str(e)}")
            return False
    
    def _create_email_message(
        self,
        articles: List[Dict[str, Any]],
        recipients: List[str]
    ) -> MIMEMultipart:
        """
        Create formatted email message.
        """
        from utils.summarizing import format_summary_for_email
        
        # Create message
        msg = MIMEMultipart("alternative")
        
        # Subject
        date_str = datetime.now().strftime("%B %d, %Y")
        msg["Subject"] = f"📰 Daily News Digest - {date_str}"
        msg["From"] = self.email_from
        msg["To"] = ", ".join(recipients)
        
        # Generate email body
        text_content = format_summary_for_email(articles, include_digest=True)
        html_content = self._convert_to_html(text_content, articles)
        
        # Attach both text and HTML versions
        part_text = MIMEText(text_content, "plain")
        part_html = MIMEText(html_content, "html")
        
        msg.attach(part_text)
        msg.attach(part_html)
        
        return msg
    
    def _convert_to_html(
        self,
        text_content: str,
        articles: List[Dict[str, Any]]
    ) -> str:
        """
        Convert text content to HTML for better formatting.
        """
        date_str = datetime.now().strftime("%B %d, %Y")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .digest {{
            background-color: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin-bottom: 20px;
        }}
        .article {{
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
        .article-title {{
            color: #2c3e50;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .article-meta {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .article-summary {{
            margin: 10px 0;
        }}
        .relevance {{
            display: inline-block;
            background-color: #27ae60;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            color: #95a5a6;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 Daily News Digest</h1>
        <p>{date_str}</p>
    </div>
"""
        
        # Add digest if available
        if articles:
            from utils.summarizing import generate_digest_summary
            digest = generate_digest_summary(articles, "executive")
            html += f"""
    <div class="digest">
        <h2>🔍 Executive Summary</h2>
        <p>{digest}</p>
    </div>
"""
        
        # Add articles
        html += f"<h2>📌 {len(articles)} Articles Today</h2>\n"
        
        for idx, article in enumerate(articles, 1):
            title = article.get('title', 'No Title')
            source = article.get('source', 'Unknown')
            url = article.get('url', '')
            summary = article.get('summary', 'No summary').replace('\n', '<br>')
            relevance = article.get('relevance_score', 0)
            
            html += f"""
    <div class="article">
        <div class="article-title">{idx}. {title}</div>
        <div class="article-meta">
            <strong>Source:</strong> {source}
"""
            
            if url:
                html += f' | <a href="{url}" target="_blank">Read More →</a>'
            
            html += "</div>\n"
            
            html += f"""
        <div class="article-summary">
            <strong>Summary:</strong><br>
            {summary}
        </div>
"""
            
            if relevance > 0:
                html += f'<span class="relevance">Relevance: {relevance:.0%}</span>\n'
            
            html += "    </div>\n"
        
        # Footer
        html += """
    <div class="footer">
        <p>Generated by Daily News Summarizer</p>
        <p>Powered by LangChain, Perplexity, and Ollama</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def _add_attachments(self, msg: MIMEMultipart) -> None:
        """
        Add CSV and JSON attachments to email.
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Attach CSV if exists
            csv_path = os.path.join("data", "summaries", f"summary_{date_str}.csv")
            if os.path.exists(csv_path):
                with open(csv_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename=summary_{date_str}.csv"
                    )
                    msg.attach(part)
                    logger.info("Attached CSV file")
            
            # Attach JSON if exists
            json_path = os.path.join("data", "raw", f"raw_{date_str}.json")
            if os.path.exists(json_path):
                with open(json_path, "rb") as f:
                    part = MIMEBase("application", "json")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename=raw_{date_str}.json"
                    )
                    msg.attach(part)
                    logger.info("Attached JSON file")
        
        except Exception as e:
            logger.warning(f"Could not attach files: {str(e)}")
    
    def _send_email(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """
        Send email via SMTP.
        """
        try:
            logger.info(f"Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
            
            # Create SMTP connection
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable TLS
                
                logger.info("Logging in to SMTP server...")
                server.login(self.smtp_user, self.smtp_password)
                
                logger.info(f"Sending email to {len(recipients)} recipients...")
                server.send_message(msg)
            
            logger.info("Email sent successfully!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check username and password.")
            return False
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_test_email(self, recipient: str = None) -> bool:
        """
        Send a test email to verify configuration.
        
        Args:
            recipient: Test recipient email address
            
        Returns:
            True if sent successfully
        """
        try:
            recipient = recipient or os.getenv("EMAIL_TO", self.smtp_user)
            
            msg = MIMEMultipart()
            msg["Subject"] = "Test Email - Daily News Summarizer"
            msg["From"] = self.email_from
            msg["To"] = recipient
            
            body = """
This is a test email from Daily News Summarizer.

If you received this, your email configuration is working correctly!

Configuration:
- SMTP Host: {smtp_host}
- SMTP Port: {smtp_port}
- From: {email_from}

Next steps:
1. Update your sources in config/sources.json
2. Update your topics in config/topics.json
3. Run: python src/main.py

Enjoy your automated news digests!
""".format(
                smtp_host=self.smtp_host,
                smtp_port=self.smtp_port,
                email_from=self.email_from
            )
            
            msg.attach(MIMEText(body, "plain"))
            
            return self._send_email(msg, [recipient])
            
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return False


def send_daily_digest(
    articles: List[Dict[str, Any]],
    recipients: List[str] = None,
    include_attachments: bool = False
) -> bool:
    """
    Convenience function to send daily digest email.
    
    Args:
        articles: List of summarized articles
        recipients: List of recipient emails
        include_attachments: Whether to attach files
        
    Returns:
        True if sent successfully
    """
    sender = EmailSender()
    return sender.send_daily_summary(articles, recipients, include_attachments)
