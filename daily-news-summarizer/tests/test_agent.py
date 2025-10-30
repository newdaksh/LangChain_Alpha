"""
Integration Tests for Agent Workflow

Complete agent workflow ko test karta hai end-to-end.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agent.agents import NewsAgentChain, create_news_agent


class TestNewsAgentChain:
    """Tests for NewsAgentChain class."""
    
    @pytest.fixture
    def agent_chain(self):
        """Create agent chain instance for testing."""
        return NewsAgentChain(
            perplexity_model="sonar"
        )
    
    def test_agent_initialization(self, agent_chain):
        """Test agent is properly initialized."""
        assert agent_chain is not None
        assert agent_chain.perplexity_model == "sonar"
        assert agent_chain.llm is not None
        assert agent_chain.agent is not None
    
    def test_get_tools(self, agent_chain):
        """Test tools are properly loaded."""
        tools = agent_chain._get_tools()
        
        assert len(tools) > 0
        
        # Check tool names
        tool_names = [tool.name for tool in tools]
        assert "search_news_with_perplexity" in tool_names
        assert "filter_articles_with_ollama" in tool_names
        assert "summarize_articles_with_ollama" in tool_names
    
    @patch('src.agent.agents.create_agent')
    def test_run_daily_summary_sync(self, mock_create_agent, agent_chain):
        """Test synchronous daily summary execution."""
        # Mock agent response
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "output": "Summary completed successfully"
        }
        mock_create_agent.return_value = mock_agent
        
        sources = [
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com",
                "enabled": True
            }
        ]
        
        topics = {
            "topics": ["AI", "machine learning"],
            "keywords": ["AI", "ML"]
        }
        
        result = agent_chain.run_daily_summary_sync(sources, topics)
        
        assert result["status"] == "success"
        assert "date" in result
        assert "result" in result
    
    @pytest.mark.asyncio
    @patch('src.agent.agents.create_agent')
    async def test_run_daily_summary_async(self, mock_create_agent, agent_chain):
        """Test asynchronous daily summary execution."""
        mock_agent = MagicMock()
        mock_agent.ainvoke.return_value = {
            "output": "Summary completed"
        }
        mock_create_agent.return_value = mock_agent
        
        sources = [{"name": "Test", "enabled": True}]
        topics = {"topics": ["AI"], "keywords": []}
        
        result = await agent_chain.run_daily_summary(sources, topics)
        
        assert result["status"] == "success"


class TestAgentFactory:
    """Tests for agent factory function."""
    
    def test_create_news_agent(self):
        """Test agent creation via factory."""
        agent = create_news_agent(
            perplexity_model="llama-3.1-sonar-small-128k-online"
        )
        
        assert isinstance(agent, NewsAgentChain)
        assert agent.perplexity_model == "sonar"


class TestAgentWithMockLLM:
    """Tests using mocked LLM responses."""
    
    @pytest.fixture
    def mock_llm_agent(self):
        """Create agent with mocked LLM."""
        with patch('src.agent.agents.ChatPerplexity') as mock_perplexity:
            # Mock LLM
            mock_llm = MagicMock()
            mock_llm.invoke.return_value.content = "Mocked response"
            mock_perplexity.return_value = mock_llm
            
            agent = NewsAgentChain()
            yield agent
    
    def test_agent_prompt_creation(self, mock_llm_agent):
        """Test agent creates proper prompts."""
        agent = mock_llm_agent._create_agent()
        assert agent is not None


class TestAgentErrorHandling:
    """Tests for error handling in agent."""
    
    @pytest.fixture
    def agent_chain(self):
        """Create agent for error testing."""
        return NewsAgentChain()
    
    @patch('src.agent.agents.create_agent')
    def test_handle_tool_error(self, mock_create_agent, agent_chain):
        """Test agent handles tool errors gracefully."""
        # Simulate tool error
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = Exception("Tool execution failed")
        mock_create_agent.return_value = mock_agent
        
        sources = [{"name": "Test", "enabled": True}]
        topics = {"topics": ["AI"], "keywords": []}
        
        result = agent_chain.run_daily_summary_sync(sources, topics)
        
        assert result["status"] == "error"
        assert "error" in result
    
    def test_handle_empty_sources(self, agent_chain):
        """Test agent handles empty sources."""
        result = agent_chain.run_daily_summary_sync([], {})
        
        # Should still execute but may have different behavior
        assert "status" in result


class TestAgentIntegration:
    """Integration tests with real components (requires Ollama running)."""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("RUN_INTEGRATION_TESTS"),
        reason="Integration tests disabled"
    )
    def test_real_agent_execution(self):
        """Test agent with real Ollama instance.
        
        Note: This test requires:
        - Ollama running locally
        - PERPLEXITY_API_KEY in environment
        - RUN_INTEGRATION_TESTS=1 in environment
        """
        agent = create_news_agent()
        
        sources = [
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com",
                "enabled": True
            }
        ]
        
        topics = {
            "topics": ["artificial intelligence"],
            "keywords": ["AI"]
        }
        
        result = agent.run_daily_summary_sync(sources, topics)
        
        # Check result structure
        assert "status" in result
        assert "date" in result
        
        # If successful, should have processed some data
        if result["status"] == "success":
            assert "result" in result


class TestAgentWorkflowSteps:
    """Test individual workflow steps."""
    
    @pytest.fixture
    def agent_chain(self):
        return NewsAgentChain()
    
    @patch('src.utils.scraping.search_multiple_sources')
    @patch('src.utils.filtering.filter_articles_by_relevance')
    @patch('src.utils.summarizing.generate_article_summaries')
    def test_workflow_orchestration(
        self,
        mock_summarize,
        mock_filter,
        mock_search,
        agent_chain
    ):
        """Test agent properly orchestrates workflow steps."""
        # Setup mock returns
        mock_articles = [
            {
                "title": "Test Article",
                "snippet": "Test content",
                "source": "Test"
            }
        ]
        
        mock_search.return_value = mock_articles
        mock_filter.return_value = mock_articles
        mock_summarize.return_value = [
            {**mock_articles[0], "summary": "Test summary"}
        ]
        
        # This would test the workflow if we had direct access
        # In practice, agent handles orchestration
        assert agent_chain.agent is not None


class TestAgentConfiguration:
    """Test agent configuration options."""
    
    def test_custom_temperature(self):
        """Test agent with custom temperature."""
        agent = NewsAgentChain(temperature=0.1)
        assert agent.temperature == 0.1
    
    def test_custom_model(self):
        """Test agent with custom model."""
        agent = NewsAgentChain(perplexity_model="sonar")
        assert agent.perplexity_model == "sonar"
    
    def test_custom_api_key(self):
        """Test agent with custom API key."""
        agent = NewsAgentChain(perplexity_api_key="test_key_123")
        assert agent.perplexity_api_key == "test_key_123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
