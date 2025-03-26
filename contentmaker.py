import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", InsecureRequestWarning)

import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin

def parse_filtered_sitemap(file_path):
    """Parse the filtered sitemap.xml and return a list of URLs."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    urls = set()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for loc in root.findall("sm:url/sm:loc", ns):
        if loc.text:
            urls.add(loc.text.strip())
    return list(urls)

def clean_text(text):
    """
    Clean the text to keep neat English:
    - Remove all non-alphanumeric characters (except spaces).
    - Collapse multiple spaces into one.
    """
    cleaned = re.sub(r'[^A-Za-z0-9\s]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def crawl_urls(urls, delay=1):
    """
    Crawl each URL in the list, extract the title (if available) and page text,
    clean the text, and return a list of dictionaries containing the URL,
    title, and cleaned content.
    Also, prints progress logs in the format "x/997 done".
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    total = len(urls)
    for idx, url in enumerate(urls, start=1):
        print(f"{idx}/{total} done - Fetching: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else ""
                raw_text = soup.get_text(separator=" ", strip=True)
                neat_text = clean_text(raw_text)
                results.append({
                    "url": url,
                    "title": title,
                    "content": neat_text
                })
            else:
                print(f"Non-200 response for {url}: {response.status_code}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        time.sleep(delay)
    return results

def save_to_json(data, output_file="vector_data.json"):
    """Save the list of crawled records to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} records to {output_file}")

if __name__ == "__main__":
    sitemap_file = r"C:\Users\surya\Desktop\webcrawling\filtered_sitemap.xml"  # Your filtered XML file with ~997 URLs
    urls = parse_filtered_sitemap(sitemap_file)
    print(f"Parsed {len(urls)} URLs from filtered sitemap.")
    
    # Crawl the URLs, printing progress as "x/997 done"
    crawled_data = crawl_urls(urls, delay=1)
    
    # Save the crawled and cleaned content to a JSON file
    save_to_json(crawled_data, output_file="vector_data.json")
