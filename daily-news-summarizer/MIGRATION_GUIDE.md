# Updated Agent Implementation - Migration Guide

## Changes Made

Your Daily News Summarizer has been updated to use **LangChain's `create_agent` function** with **Perplexity AI** model instead of Ollama.

### Key Updates

#### 1. **Agent Implementation (`src/agent/agents.py`)**
- ✅ Replaced `ChatOllama` with `ChatPerplexity`
- ✅ Using `create_agent()` from `langchain.agents`
- ✅ Simplified message-based interface
- ✅ Updated system prompt for better news summarization

#### 2. **Configuration Changes**
- **Old**: `ollama_base_url`, `ollama_model`
- **New**: `perplexity_api_key`, `perplexity_model`

#### 3. **Code Pattern**
```python
from langchain.agents import create_agent
from langchain_community.chat_models import ChatPerplexity

# Create agent
agent = create_agent(
    model=self.llm,  # Perplexity model
    tools=[search_news, filter_articles, summarize_articles],
    system_prompt="You are a helpful research assistant."
)

# Invoke agent
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Research AI safety trends"}
    ]
})
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

Add your Perplexity API key:
```
PERPLEXITY_API_KEY=your_actual_api_key_here
```

### 3. Get Perplexity API Key
1. Visit [Perplexity AI](https://www.perplexity.ai/)
2. Sign up for an account
3. Navigate to API settings
4. Generate an API key

## Usage Examples

### Basic Usage
```python
from src.agent.agents import create_news_agent

# Create agent
agent = create_news_agent(
    perplexity_model="llama-3.1-sonar-small-128k-online"
)

# Define sources and topics
sources = [
    {"name": "TechCrunch", "enabled": True}
]

topics = {
    "topics": ["AI", "machine learning"],
    "keywords": ["AI", "ML"]
}

# Run summary
result = agent.run_daily_summary_sync(sources, topics)
print(result)
```

### Run the Example
```bash
python example_usage.py
```

### Run Tests
```bash
pytest tests/test_agent.py -v
```

## Available Perplexity Models

- `llama-3.1-sonar-small-128k-online` (recommended for cost-effective usage)
- `llama-3.1-sonar-large-128k-online` (more powerful)
- `llama-3.1-sonar-huge-128k-online` (most capable)

## Migration Checklist

- [x] Updated `agents.py` to use `create_agent`
- [x] Replaced Ollama with Perplexity
- [x] Updated test files
- [x] Updated configuration parameters
- [x] Created example usage file
- [x] Added environment variable template

## Benefits of This Change

1. **Simplified API**: Message-based interface is cleaner
2. **Cloud-based**: No need to run local Ollama instance
3. **Better Performance**: Perplexity optimized for search tasks
4. **Real-time Data**: Access to current information via Perplexity

## Troubleshooting

### Import Errors
If you see import errors, ensure all dependencies are installed:
```bash
pip install --upgrade langchain langchain-community langchain-core
```

### API Key Issues
- Ensure `PERPLEXITY_API_KEY` is set in `.env` file
- Check API key is valid and has available credits
- Verify `.env` file is in the project root

### Rate Limits
If hitting rate limits:
- Reduce `max_results` in search queries
- Add delays between API calls
- Upgrade to higher tier Perplexity plan

## Next Steps

1. Add your Perplexity API key to `.env`
2. Run `python example_usage.py` to test
3. Run tests: `pytest tests/test_agent.py -v`
4. Customize sources and topics in `config/` directory
5. Run full workflow: `python src/main.py`

## Questions?

Check the following files for reference:
- `example_usage.py` - Complete working example
- `tests/test_agent.py` - Test cases showing usage patterns
- `src/agent/agents.py` - Full implementation

Happy coding! 🚀
