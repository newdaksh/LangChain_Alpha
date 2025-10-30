"""
Example Usage of News Agent with create_agent

This demonstrates how to use the updated NewsAgentChain with
LangChain's create_agent function and Perplexity model.
"""

from src.agent.agents import create_news_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main example function."""
    
    # Create news agent with Perplexity model
    agent = create_news_agent(
        perplexity_model="sonar",
        temperature=0.3
    )
    
    print("✅ Agent created successfully!")
    print(f"Model: {agent.perplexity_model}")
    print(f"Temperature: {agent.temperature}")
    
    # Example sources configuration
    sources = [
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com",
            "enabled": True
        },
        {
            "name": "The Verge",
            "url": "https://theverge.com",
            "enabled": True
        }
    ]
    
    # Example topics configuration
    topics = {
        "topics": ["artificial intelligence", "machine learning"],
        "keywords": ["AI", "ML", "neural networks", "deep learning"]
    }
    
    # Run synchronous summary
    print("\n📰 Running daily news summary...")
    result = agent.run_daily_summary_sync(sources, topics)
    
    print(f"\n✅ Status: {result['status']}")
    print(f"📅 Date: {result['date']}")
    print(f"🕒 Timestamp: {result['timestamp']}")
    
    if result['status'] == 'success':
        print("\n✨ Summary generated successfully!")
        print(f"Result: {result['result']}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
