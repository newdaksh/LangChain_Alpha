# Daily News Summarizer

An automated news aggregation and summarization system using LangChain 1.0 Alpha agents, Perplexity API for intelligent searching, and Ollama API for filtering and summarization.

## 🚀 Features

- **Intelligent News Search**: Uses Perplexity API to fetch latest articles and relevant snippets
- **LLM-Powered Filtering**: Ollama-based filtering to identify relevant articles based on topics
- **Smart Summarization**: Generates concise bullet-point summaries using Ollama
- **Multi-Output**: Saves summaries as both CSV and Markdown formats
- **Email Delivery**: Automated email digests of daily summaries
- **Configurable**: Easy-to-update JSON configuration for sources and topics
- **LangChain 1.0 Alpha**: Built with modern agent chains and LCEL patterns

## 📋 Requirements

- Python 3.10+
- Ollama installed locally or access to remote Ollama instance
- Perplexity API key
- SMTP credentials for email delivery

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Perplexity API
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com

# Optional: Slack (if implementing)
# SLACK_WEBHOOK_URL=your_slack_webhook_url
```

### 3. Configure Sources and Topics

Edit `config/sources.json` to add your news sources:
```json
{
  "sources": [
    {
      "name": "TechCrunch",
      "url": "https://techcrunch.com",
      "category": "technology"
    }
  ]
}
```

Edit `config/topics.json` to define topics of interest:
```json
{
  "topics": [
    "artificial intelligence",
    "machine learning",
    "startup funding"
  ],
  "keywords": ["AI", "ML", "funding", "acquisition"]
}
```

### 4. Install Ollama (if running locally)

```bash
# Visit https://ollama.ai to download and install
# Then pull a model:
ollama pull llama3.2
```

## 🎯 Usage

### Run the Daily News Summarizer

```bash
python src/main.py
```

### Run with Custom Config

```bash
python src/main.py --sources config/custom_sources.json --topics config/custom_topics.json
```

## 📁 Project Structure

```
daily-news-summarizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── config/
│   ├── sources.json         # News source configuration
│   └── topics.json          # Topics and keywords configuration
├── src/
│   ├── main.py              # Main entry point
│   ├── agent/
│   │   ├── agents.py        # LangChain agent implementation
│   │   └── tools.py         # Custom tools for agent
│   ├── utils/
│   │   ├── scraping.py      # Perplexity-based news fetching
│   │   ├── filtering.py     # Ollama-based content filtering
│   │   └── summarizing.py   # Ollama-based summarization
│   └── output/
│       ├── emailer.py       # Email delivery module
│       └── slack.py         # Slack integration (optional)
├── data/
│   ├── raw/                 # Raw scraped content
│   └── summaries/           # Generated summaries
└── tests/
    ├── test_tools.py        # Unit tests for tools
    └── test_agent.py        # Integration tests for agent
```

## 📊 Output

The system generates two types of output files in `data/summaries/`:

1. **Markdown Format**: `summary_YYYY-MM-DD.md` - Human-readable summary
2. **CSV Format**: `summary_YYYY-MM-DD.csv` - Structured data for analysis

## 🧪 Testing

Run unit tests:
```bash
pytest tests/test_tools.py -v
```

Run integration tests:
```bash
pytest tests/test_agent.py -v
```

Run all tests:
```bash
pytest tests/ -v
```

## 🔧 How It Works

1. **Configuration Loading**: Reads sources and topics from JSON files
2. **News Search**: Uses Perplexity API to search for relevant articles based on sources
3. **Content Filtering**: Ollama LLM filters articles based on configured topics and keywords
4. **Summarization**: Ollama generates concise bullet-point summaries
5. **Storage**: Saves raw data and summaries to disk
6. **Delivery**: Sends email digest with daily summaries

## 🎨 Customization

### Adding New Tools

Create custom tools in `src/agent/tools.py`:

```python
@tool
def my_custom_tool(query: str) -> str:
    """Tool description for the agent."""
    # Implementation
    return result
```

### Modifying Agent Behavior

Edit `src/agent/agents.py` to customize the agent chain logic.

## 🐛 Troubleshooting

**Ollama Connection Issues**:
- Ensure Ollama is running: `ollama serve`
- Check the OLLAMA_BASE_URL in .env

**Perplexity API Errors**:
- Verify your API key is valid
- Check rate limits on your plan

**Email Delivery Issues**:
- Use app-specific passwords for Gmail
- Verify SMTP settings

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on the repository.
