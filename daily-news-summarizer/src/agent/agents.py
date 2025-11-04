"""
LangChain Agent Implementation for Daily News Summarizer

Yeh file main agent logic ko implement karti hai using LangChain's create_agent function.
Agent tools ko orchestrate karta hai for searching, filtering, and summarizing news.
"""

from typing import List, Dict, Any, Optional
from langchain.agents import create_agent
from langchain_community.chat_models import ChatPerplexity
from langchain_core.messages import HumanMessage, SystemMessage
import logging
import os
from datetime import datetime

from .tools import (
    search_news_with_perplexity,
    filter_articles_with_ollama,
    summarize_articles_with_ollama,
    save_raw_data,
    save_summary
)
from .middleware.pii_redaction import PIIMiddleware
from .middleware.summarization import SummarizationMiddleware
from .middleware.human_in_loop import HumanInTheLoopMiddleware

logger = logging.getLogger(__name__)


class NewsAgentChain:
    """
    Main agent chain for news summarization workflow.
    
    Yeh class puri news summarization process ko manage karta hai:
    1. Sources se news search karna
    2. Articles ko filter karna based on topics
    3. Summaries generate karna
    4. Results ko save karna
    """
    
    def __init__(
        self,
        perplexity_api_key: Optional[str] = None,
        perplexity_model: str = "sonar",
        temperature: float = 0.3
    ):
        """
        Initialize the news agent chain.
        
        Args:
            perplexity_api_key: API key for Perplexity (reads from env if not provided)
            perplexity_model: Perplexity model name to use
            temperature: Temperature setting for LLM (lower = more focused)
        """
        self.perplexity_model = perplexity_model
        self.temperature = temperature
        self.perplexity_api_key = perplexity_api_key or os.getenv("PERPLEXITY_API_KEY")
        
        # Initialize Perplexity LLM
        self.llm = ChatPerplexity(
            model=perplexity_model,
            temperature=temperature,
            perplexity_api_key=self.perplexity_api_key
        )
        
        # Create agent with tools using LangChain's create_agent
        self.agent = self._create_agent()

        logger.info(f"NewsAgentChain initialized with Perplexity model: {perplexity_model}")
    
    def _get_tools(self) -> List:
        """Get list of tools available to the agent."""
        return [
            search_news_with_perplexity,
            filter_articles_with_ollama,
            summarize_articles_with_ollama,
            save_raw_data,
            save_summary
        ]
    
    def _create_agent(self):
        """
        Create an agent using LangChain's create_agent function.
        
        Returns:
            Configured agent ready for execution
        """
        # Define the system prompt for the agent
        system_prompt = """You are a helpful news research assistant specializing in daily news summarization.

Your responsibilities:
1. Search for latest news articles from configured sources
2. Filter articles based on relevance to specified topics and keywords
3. Generate concise, informative summaries of filtered articles
4. Save results in structured formats for easy consumption

Workflow to follow:
- Use search_news_with_perplexity to fetch articles from news sources
- Use filter_articles_with_ollama to identify relevant content
- Use summarize_articles_with_ollama to create summaries
- Use save_raw_data and save_summary to store results

Always provide accurate, unbiased summaries and cite your sources.
Work systematically through: search -> filter -> summarize -> save.
Focus on actionable insights and key information."""
        
        # Get tools for the agent
        tools = self._get_tools()

        # Initialize middleware instances
        middleware = [
            PIIMiddleware(),
            SummarizationMiddleware(),
            HumanInTheLoopMiddleware(sensitive_tools=["save_summary", "save_raw_data"]),
        ]

        # Try to initialize a LangGraph client for state & checkpoints (optional)
        graph = None
        try:
            import langgraph
            # a very small, safe usage pattern: get/create a graph client if available
            graph = getattr(langgraph, "GraphClient", None)
        except Exception:
            # LangGraph not available in all environments; continue without it
            graph = None

        # Create the agent using LangChain's create_agent function, passing middleware
        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt,
            middleware=middleware,
            graph=graph,
        )

        return agent
    
    async def run_daily_summary(
        self,
        sources: List[Dict[str, Any]],
        topics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the complete daily news summarization workflow asynchronously.
        
        Args:
            sources: List of news sources from config
            topics: Topics configuration with keywords and filters
            
        Returns:
            Dictionary with summary results and statistics
        """
        try:
            logger.info("Starting daily news summarization workflow (async)...")
            
            # Prepare user message for agent
            user_message = self._create_user_message(sources, topics)
            
            # Execute agent with message-based interface. Prefer structured output.
            payload = {"messages": [{"role": "user", "content": user_message}]}
            result = await self.agent.ainvoke(payload)
            # Normalize result to a dict if agent returned a JSON string
            if isinstance(result, str):
                try:
                    import json
                    parsed = json.loads(result)
                    result = parsed
                except Exception:
                    # leave as string
                    pass
            
            logger.info("Daily summary workflow completed successfully")
            return {
                "status": "success",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in daily summary workflow: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_daily_summary_sync(
        self,
        sources: List[Dict[str, Any]],
        topics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synchronous version of daily summary workflow.
        
        Args:
            sources: List of news sources from config
            topics: Topics configuration
            
        Returns:
            Dictionary with summary results
        """
        try:
            logger.info("Starting daily news summarization workflow (sync)...")
            
            # Prepare user message for agent
            user_message = self._create_user_message(sources, topics)
            
            # Execute agent with message-based interface. Prefer structured output.
            payload = {"messages": [{"role": "user", "content": user_message}]}
            result = self.agent.invoke(payload)
            if isinstance(result, str):
                try:
                    import json
                    parsed = json.loads(result)
                    result = parsed
                except Exception:
                    pass
            
            logger.info("Daily summary workflow completed")
            return {
                "status": "success",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in workflow: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_user_message(
        self,
        sources: List[Dict[str, Any]],
        topics: Dict[str, Any]
    ) -> str:
        """
        Create user message for the agent.
        
        Args:
            sources: News sources to search
            topics: Topics and keywords
            
        Returns:
            Formatted user message
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        sources_str = ", ".join([s.get("name", "") for s in sources if s.get("enabled", True)])
        topics_str = ", ".join(topics.get("topics", []))
        keywords_str = ", ".join(topics.get("keywords", []))
        
        message = f"""Please perform a daily news summary for {date_str} with the following parameters:

Sources: {sources_str}
Topics: {topics_str}
Keywords: {keywords_str}

Follow these steps systematically:
1. Search for the latest articles from these sources about the specified topics
2. Filter articles for relevance and quality based on topics and keywords
3. Generate concise, informative summaries for the top filtered articles
4. Save the raw data and final summaries

Provide a comprehensive report with source citations."""
        
        return message


def create_news_agent(
    perplexity_api_key: Optional[str] = None,
    perplexity_model: str = "llama-3.1-sonar-small-128k-online",
    temperature: float = 0.3
) -> NewsAgentChain:
    """
    Factory function to create a configured news agent.
    
    Args:
        perplexity_api_key: API key for Perplexity (reads from env if not provided)
        perplexity_model: Perplexity model name
        temperature: Temperature for model responses
        
    Returns:
        Configured NewsAgentChain instance
    """
    return NewsAgentChain(
        perplexity_api_key=perplexity_api_key,
        perplexity_model=perplexity_model,
        temperature=temperature
    )
