from bs4 import BeautifulSoup
import requests
from huggingface_hub import InferenceClient
from urllib.parse import urlparse
from datetime import datetime
from collections import defaultdict
import os
import re

# Initialize Hugging Face client
HF_TOKEN = "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"
client = InferenceClient(token=HF_TOKEN)

# Profession/Interest to RSS feed mapping
PROFESSION_FEEDS = {
    "technology": "https://www.wired.com/feed/rss",
    "ai": "https://www.wired.com/feed/category/ai/latest/rss",
    "science": "https://www.sciencedaily.com/rss/all.xml",
    "business": "https://feeds.a.dj.com/rss/RSSBusinessNews.xml",
    "health": "https://www.medicalnewstoday.com/rss",
    "sports": "https://www.espn.com/espn/rss/news",
    "entertainment": "https://www.hollywoodreporter.com/feed/rss/news",
    "politics": "https://www.politico.com/rss/politicopicks.xml",
    "education": "https://www.ed.gov/feed",
    "environment": "https://www.greenpeace.org/international/publication/rss/"
}

# Country to BBC RSS feed mapping
BBC_COUNTRY_FEEDS = {
    "india": "https://feeds.bbci.co.uk/news/world/asia/india/rss.xml",
    "us": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
    "uk": "https://feeds.bbci.co.uk/news/england/rss.xml",
    "canada": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
    "australia": "https://feeds.bbci.co.uk/news/world/australia/rss.xml",
    "japan": "https://feeds.bbci.co.uk/news/world/asia/rss.xml",
    "germany": "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
    "france": "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
    "brazil": "https://feeds.bbci.co.uk/news/world/latin_america/rss.xml",
    "china": "https://feeds.bbci.co.uk/news/world/asia/rss.xml"
}

def parse_user_input(user_input: str) -> dict:
    """Parse user input in format 'Name(Profession/Interest, Age, Country)'"""
    pattern = r"(.+?)\((.+?),\s*(\d+),\s*(.+?)\)"
    match = re.match(pattern, user_input)
    if not match:
        raise ValueError("Invalid input format. Expected: Name(Profession/Interest, Age, Country)")
    
    name = match.group(1).strip()
    profession = match.group(2).strip()
    age = int(match.group(3))
    country = match.group(4).strip().lower()
    
    return {
        'name': name,
        'profession': profession,
        'age': age,
        'country': country
    }

def get_most_relevant_category(text: str, categories: list[str]) -> str:
    """Use LLM to determine the most relevant category for the given text."""
    prompt = f"""From these categories: {', '.join(categories)}, 
    select the SINGLE most relevant one for: "{text}".
    Return ONLY the category name, nothing else."""
    
    try:
        response = client.text_generation(
            prompt,
            max_new_tokens=10,
            do_sample=False
        )
        # Clean up the response
        category = response.strip().lower()
        category = re.sub(r'[^a-zA-Z]', '', category)  # Remove non-alphabetic characters
        return category
    except Exception as e:
        print(f"🤖 LLM category selection error: {e}")
        return "general"

def get_relevant_feeds(user: dict) -> tuple[str, str]:
    """Get relevant RSS feeds based on user's profession and country."""
    # Get profession/interest feed
    profession_categories = list(PROFESSION_FEEDS.keys())
    profession_category = get_most_relevant_category(user['profession'], profession_categories)
    
    if profession_category in PROFESSION_FEEDS:
        profession_feed = PROFESSION_FEEDS[profession_category]
        print(f"🔍 Selected '{profession_category}' feed for: {user['profession']}")
    else:
        profession_feed = PROFESSION_FEEDS['technology']
        print(f"⚠️ Defaulting to 'technology' feed for: {user['profession']}")
    
    # Get country feed
    country_feed = BBC_COUNTRY_FEEDS.get(user['country'], 
                                      "https://feeds.bbci.co.uk/news/world/rss.xml")
    print(f"🌍 Using country feed for: {user['country'].capitalize()}")
    
    return profession_feed, country_feed

def generate_ai_summary(text: str) -> str:
    """Generate article summary using Hugging Face's summarization API."""
    try:
        response = client.summarization(
            text[:2000], 
            model="facebook/bart-large-cnn",
            parameters={
                "max_length": 150,
                "min_length": 30,
                "do_sample": False
            }
        )
        if isinstance(response, dict):
            return response.get("summary_text", "Could not generate summary")
        elif hasattr(response, "summary_text"):
            return response.summary_text
        return str(response)
    except Exception as e:
        print(f"🤖 AI summary error: {e}")
        return "Could not generate AI summary"

def extract_article_text(url: str) -> str:
    """Extract main content text from a news article URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'aside']):
            element.decompose()
        
        article = soup.find('article') or soup.find('main') or soup.body
        return ' '.join(article.stripped_strings) if article else ""
    except Exception as e:
        print(f"🌐 Error extracting article: {e}")
        return ""

def get_rss_feed(rss_url: str, limit: int = 5) -> list[dict]:
    """Parse an RSS feed and extract article information."""
    try:
        response = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        articles = []
        
        for item in soup.find_all(['item', 'entry'])[:limit]:
            title = item.title.text.strip() if item.title else "No title"
            url = item.link.text.strip() if item.link else item.link.get('href', '').strip()
            pub_date = item.pubDate.text.strip() if item.pubDate else None
            
            if url:
                articles.append({
                    'title': title,
                    'url': url,
                    'source': urlparse(rss_url).netloc,
                    'pub_date': pub_date,
                    'feed_source': rss_url
                })
        
        return articles
    except Exception as e:
        print(f"📡 Error processing RSS feed: {e}")
        return []

def process_articles(profession_feed: str, country_feed: str) -> tuple[list[dict], list[dict]]:
    """Process articles from both feeds separately."""
    print(f"\n📚 Fetching profession/interest articles from: {urlparse(profession_feed).netloc}")
    profession_articles = []
    for article in get_rss_feed(profession_feed, limit=5):
        print(f"  📰 Processing: {article['title'][:60]}...")
        full_text = extract_article_text(article['url'])
        article['summary'] = generate_ai_summary(full_text) if full_text else "Could not extract content"
        profession_articles.append(article)
    
    print(f"\n🌐 Fetching country news from: {urlparse(country_feed).netloc}")
    country_articles = []
    for article in get_rss_feed(country_feed, limit=5):
        print(f"  📰 Processing: {article['title'][:60]}...")
        full_text = extract_article_text(article['url'])
        article['summary'] = generate_ai_summary(full_text) if full_text else "Could not extract content"
        country_articles.append(article)
    
    return profession_articles, country_articles

def generate_newsletter_md(user: dict, profession_articles: list[dict], country_articles: list[dict]) -> str:
    """Generate a formatted newsletter in Markdown format."""
    md_content = f"""# 📰 Hi {user['name']}
    
## 🔍 Top Stories Summary

"""

    # Top 3 articles mix (2 from profession, 1 from country)
    top_articles = profession_articles[:2] + country_articles[:1]
    for i, article in enumerate(top_articles, 1):
        summary_text = article['summary'][:150] + '...' if len(article['summary']) > 150 else article['summary']
        md_content += f"{i}. **[{article['title']}]({article['url']})**  \n"
        md_content += f"   {summary_text}  \n\n"

    # Profession/Interest Section
    md_content += f"## 🧑‍💻 {user['profession']} News\n\n"
    for article in profession_articles:
        md_content += format_article_md(article)
    
    # Country News Section
    md_content += f"## 🌍 {user['country'].capitalize()} News\n\n"
    for article in country_articles:
        md_content += format_article_md(article)
    
    md_content += "---\n"

    
    return md_content

def format_article_md(article: dict) -> str:
    """Format a single article in Markdown."""
    return f"""### {article['title']}

*Source: {article['source']} | Published: {article.get('pub_date', 'N/A')}*

{article['summary']}

[Read full article]({article['url']})  

---
"""

def save_newsletter_to_file(content: str, filename: str):
    """Save newsletter to a Markdown file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Newsletter saved to {filename}")

if __name__ == "__main__":
    # Example input: "Alex Parker(Software Engineer, 35, India)"
    user_input = input("Enter user details (Name(Profession/Interest, Age, Country)): ")
    
    try:
        user = parse_user_input(user_input)
        print(f"\n👤 User profile:")
        print(f"Name: {user['name']}")
        print(f"Profession/Interest: {user['profession']}")
        print(f"Age: {user['age']}")
        print(f"Country: {user['country']}")
        
        profession_feed, country_feed = get_relevant_feeds(user)
        
        print("\n🚀 Generating personalized newsletter...")
        profession_articles, country_articles = process_articles(profession_feed, country_feed)
        
        if profession_articles or country_articles:
            newsletter = generate_newsletter_md(user, profession_articles, country_articles)
            print("\n" + "="*80)
            print(newsletter[:1000] + "...")  # Print preview
            print("="*80)
            
            filename = f"{user['name'].replace(' ', '_')}_Newsletter.md"
            save_newsletter_to_file(newsletter, filename)
        else:
            print("❌ No articles were processed successfully")
    
    except ValueError as e:
        print(f"❌ Error: {e}")