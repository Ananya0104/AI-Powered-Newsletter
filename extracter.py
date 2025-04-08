import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
from huggingface_hub import InferenceClient

# Hugging Face setup
HF_TOKEN = "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"
client = InferenceClient(token=HF_TOKEN)

# Topic-specific RSS feeds
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

# BBC country-specific news
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

def parse_user_input(text):
    pattern = r"(.+?)\((.+?),\s*(\d+),\s*(.+?)\)"
    match = re.match(pattern, text)
    if not match:
        raise ValueError("Input must follow: Name(Profession/Interest, Age, Country)")
    
    name, profession, age, country = match.groups()
    return {
        "name": name.strip(),
        "profession": profession.strip(),
        "age": int(age),
        "country": country.strip().lower()
    }

def get_relevant_category(text, categories):
    prompt = (
        f"From these categories: {', '.join(categories)}, "
        f"choose the most relevant one for: \"{text}\". "
        f"Only return the category name."
    )
    try:
        response = client.text_generation(prompt, max_new_tokens=10, do_sample=False)
        cleaned = re.sub(r'[^a-zA-Z]', '', response.lower())
        return cleaned if cleaned in categories else "technology"
    except Exception as e:
        print(f"Category error: {e}")
        return "technology"

def get_feeds_for_user(user):
    profession_key = get_relevant_category(user["profession"], list(PROFESSION_FEEDS.keys()))
    profession_feed = PROFESSION_FEEDS.get(profession_key)
    country_feed = BBC_COUNTRY_FEEDS.get(user["country"], "https://feeds.bbci.co.uk/news/world/rss.xml")
    
    print(f"Profession category: {profession_key}")
    print(f"Country: {user['country'].capitalize()}")
    
    return profession_feed, country_feed

def fetch_rss_articles(rss_url, limit=5):
    try:
        res = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all(["item", "entry"])[:limit]
        
        articles = []
        for item in items:
            title = item.title.text if item.title else "No Title"
            link = item.link.text if item.link else item.link.get("href", "")
            pub_date = item.pubDate.text if item.pubDate else "N/A"
            articles.append({
                "title": title.strip(),
                "url": link.strip(),
                "pub_date": pub_date,
                "source": urlparse(rss_url).netloc
            })
        return articles
    except Exception as e:
        print(f"RSS error: {e}")
        return []

def extract_article_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "footer", "nav", "aside"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.body
        return " ".join(article.stripped_strings) if article else ""
    except Exception as e:
        print(f"Text extraction failed: {e}")
        return ""

def summarize(text):
    try:
        trimmed = text[:2000]
        response = client.summarization(trimmed, model="facebook/bart-large-cnn", parameters={
            "max_length": 150,
            "min_length": 30,
            "do_sample": False
        })
        if isinstance(response, dict):
            return response.get("summary_text", "")
        return response.summary_text if hasattr(response, "summary_text") else str(response)
    except Exception as e:
        print(f"Summarization error: {e}")
        return "Summary unavailable."

def process_feed_articles(feed_url):
    articles = fetch_rss_articles(feed_url)
    for article in articles:
        print(f"{article['title']}")
        content = extract_article_text(article["url"])
        article["summary"] = summarize(content) if content else "No content available."
    return articles

def format_article(article):
    return (
        f"### {article['title']}\n\n"
        f"*Source: {article['source']} | Published: {article['pub_date']}*\n\n"
        f"{article['summary']}\n\n"
        f"[Read full article]({article['url']})\n\n---\n"
    )

def build_newsletter(user, profession_articles, country_articles):
    output = f"# Hello, {user['name']}!\n\n"
    output += "## Highlights\n\n"
    
    highlights = profession_articles[:2] + country_articles[:1]
    for idx, article in enumerate(highlights, 1):
        preview = article["summary"]
        if len(preview) > 150:
            preview = preview[:150] + "..."
        output += f"{idx}. **[{article['title']}]({article['url']})**  \n   {preview}\n\n"
    
    output += f"## {user['profession'].capitalize()} News\n\n"
    for a in profession_articles:
        output += format_article(a)
    
    output += f"## {user['country'].capitalize()} News\n\n"
    for a in country_articles:
        output += format_article(a)
    return output

def save_to_file(content, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved newsletter as {filename}")

if __name__ == "__main__":
    user_input = input("Enter details in format: Name(Profession, Age, Country):\n> ")
    
    try:
        user = parse_user_input(user_input)
        print(f"\n Profile: {user['name']}, {user['profession']}, {user['age']}, {user['country']}")
        
        prof_feed, country_feed = get_feeds_for_user(user)
        
        print("\nFetching articles...")
        prof_articles = process_feed_articles(prof_feed)
        country_articles = process_feed_articles(country_feed)
        
        newsletter = build_newsletter(user, prof_articles, country_articles)
        filename = f"{user['name'].replace(' ', '_')}_Newsletter.md"
        save_to_file(newsletter, filename)
        
    except ValueError as ve:
        print(f"Error: {ve}")