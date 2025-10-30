"""
Unit Tests for Custom Tools

Tool functions ki functionality test karta hai.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from src.agent.tools import (
    search_news_with_perplexity,
    filter_articles_with_ollama,
    summarize_articles_with_ollama,
    save_raw_data,
    save_summary
)


class TestSearchNewsTool:
    """Tests for Perplexity search tool."""
    
    @patch('src.agent.tools.fetch_news_from_perplexity')
    def test_search_success(self, mock_fetch):
        """Test successful news search."""
        # Mock return data
        mock_articles = [
            {
                "title": "Test Article",
                "url": "https://example.com/article",
                "snippet": "Test snippet",
                "source": "Test Source"
            }
        ]
        mock_fetch.return_value = mock_articles
        
        # Call tool
        result = search_news_with_perplexity.invoke({
            "query": "AI news",
            "source_name": "TechCrunch",
            "max_results": 5
        })
        
        # Parse result
        result_data = json.loads(result)
        
        # Assertions
        assert result_data["status"] == "success"
        assert result_data["count"] == 1
        assert len(result_data["articles"]) == 1
        assert result_data["articles"][0]["title"] == "Test Article"
    
    @patch('src.agent.tools.fetch_news_from_perplexity')
    def test_search_error(self, mock_fetch):
        """Test error handling in search."""
        mock_fetch.side_effect = Exception("API Error")
        
        result = search_news_with_perplexity.invoke({
            "query": "AI news",
            "max_results": 5
        })
        
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert "error" in result_data
        assert result_data["articles"] == []


class TestFilterTool:
    """Tests for article filtering tool."""
    
    @patch('src.agent.tools.filter_articles_by_relevance')
    def test_filter_success(self, mock_filter):
        """Test successful filtering."""
        # Mock articles
        articles = [
            {"title": "AI News", "snippet": "AI content"},
            {"title": "Other News", "snippet": "Other content"}
        ]
        
        # Mock filtered result
        mock_filter.return_value = [articles[0]]
        
        # Call tool
        articles_json = json.dumps({"articles": articles})
        result = filter_articles_with_ollama.invoke({
            "articles_json": articles_json,
            "topics": "AI, machine learning",
            "keywords": "AI, ML"
        })
        
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["filtered_count"] == 1
    
    def test_filter_invalid_json(self):
        """Test error handling with invalid JSON."""
        result = filter_articles_with_ollama.invoke({
            "articles_json": "invalid json",
            "topics": "AI"
        })
        
        result_data = json.loads(result)
        assert result_data["status"] == "error"


class TestSummarizeTool:
    """Tests for summarization tool."""
    
    @patch('src.agent.tools.generate_article_summaries')
    def test_summarize_success(self, mock_summarize):
        """Test successful summarization."""
        articles = [
            {"title": "Test", "snippet": "Content", "summary": "Summary"}
        ]
        
        mock_summarize.return_value = articles
        
        articles_json = json.dumps({"articles": articles})
        result = summarize_articles_with_ollama.invoke({
            "articles_json": articles_json
        })
        
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert result_data["count"] == 1
        assert "summaries" in result_data


class TestSaveTools:
    """Tests for data saving tools."""
    
    def test_save_raw_data(self, tmp_path):
        """Test saving raw data."""
        # Change to temp directory
        os.chdir(tmp_path)
        
        articles_data = {
            "articles": [
                {"title": "Test", "url": "http://test.com"}
            ]
        }
        
        result = save_raw_data.invoke({
            "articles_json": json.dumps(articles_data),
            "filename": "test_raw.json"
        })
        
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert "filepath" in result_data
    
    @patch('pandas.DataFrame.to_csv')
    def test_save_summary_csv(self, mock_to_csv, tmp_path):
        """Test saving summary as CSV."""
        os.chdir(tmp_path)
        
        summaries_data = {
            "summaries": [
                {
                    "title": "Test",
                    "summary": "Summary",
                    "source": "Test Source"
                }
            ]
        }
        
        result = save_summary.invoke({
            "summaries_json": json.dumps(summaries_data),
            "format_type": "csv"
        })
        
        result_data = json.loads(result)
        
        assert result_data["status"] == "success"
        assert len(result_data["files"]) >= 1


class TestToolIntegration:
    """Integration tests for tool workflows."""
    
    @patch('src.agent.tools.fetch_news_from_perplexity')
    @patch('src.agent.tools.filter_articles_by_relevance')
    @patch('src.agent.tools.generate_article_summaries')
    def test_complete_workflow(
        self,
        mock_summarize,
        mock_filter,
        mock_fetch
    ):
        """Test complete workflow from search to summary."""
        # Setup mocks
        articles = [
            {
                "title": "AI Breakthrough",
                "url": "http://test.com",
                "snippet": "AI content",
                "source": "TechCrunch"
            }
        ]
        
        mock_fetch.return_value = articles
        mock_filter.return_value = articles
        mock_summarize.return_value = [
            {**articles[0], "summary": "Test summary"}
        ]
        
        # Step 1: Search
        search_result = search_news_with_perplexity.invoke({
            "query": "AI news",
            "max_results": 5
        })
        search_data = json.loads(search_result)
        
        assert search_data["status"] == "success"
        
        # Step 2: Filter
        filter_result = filter_articles_with_ollama.invoke({
            "articles_json": search_result,
            "topics": "AI"
        })
        filter_data = json.loads(filter_result)
        
        assert filter_data["status"] == "success"
        
        # Step 3: Summarize
        summary_result = summarize_articles_with_ollama.invoke({
            "articles_json": filter_result
        })
        summary_data = json.loads(summary_result)
        
        assert summary_data["status"] == "success"
        assert len(summary_data["summaries"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
