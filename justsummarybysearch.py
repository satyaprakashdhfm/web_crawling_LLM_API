import warnings
import re
import requests
from bs4 import BeautifulSoup
from googlesearch import search


# Suppress SSL warnings for testing
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_page_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            raw_text = soup.get_text(separator=" ", strip=True)
            return clean_text(raw_text)
        else:
            return f"Error: Status code {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def simple_summary(text, word_limit=100):
    words = text.split()
    if len(words) <= word_limit:
        return text
    return " ".join(words[:word_limit]) + "..."

def search_acg_world(query, domain="acg-world.com", num_results=2):
    search_query = f"site:{domain} {query}"
    print(f"Searching for: {search_query}")
    raw_results = list(search(search_query, num_results=num_results))
    # Filter only absolute URLs (those that start with http)
    results = [url for url in raw_results if url.startswith("http")]
    return results

def main():
    query = input("Enter your query: ").strip()
    results = search_acg_world(query)
    
    if not results:
        print("Currently, we don't have information about it.")
        return

    summaries = []
    print("\nTop ACG-World results:")
    for url in results:
        print(f"Found: {url}")
        content = get_page_content(url)
        if content and not content.startswith("Error"):
            summary = simple_summary(content, word_limit=100)
            summaries.append({"url": url, "summary": summary})
        else:
            print(f"Could not extract content from {url}")
    
    if summaries:
        print("\nSummaries of top results:")
        for res in summaries:
            print("URL:", res["url"])
            print("Summary:", res["summary"])
            print("\n" + "="*80 + "\n")
    else:
        print("No content could be extracted from the found pages.")

if __name__ == "__main__":
    main()
