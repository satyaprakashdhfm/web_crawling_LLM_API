import warnings
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Suppress SSL warnings about certificate verification
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Function to parse the initial sitemap.xml file and extract URLs
def parse_sitemap(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    urls = set()
    for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
        if loc.text:
            urls.add(loc.text.strip())
    return list(urls)

# Function to crawl only acg-world.com pages
def crawl(seed_urls, max_links=1000):
    domain_filter = "acg-world.com"
    discovered = set(url for url in seed_urls if domain_filter in url)
    queue = [url for url in seed_urls if domain_filter in url]
    
    while queue and len(discovered) < max_links:
        current_url = queue.pop(0)
        print(f"Crawling: {current_url} (Total discovered: {len(discovered)})")
        try:
            response = requests.get(current_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10, verify=False)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a.get("href")
                    absolute_url = urljoin(current_url, href)
                    parsed = urlparse(absolute_url)
                    # Only allow URLs that contain 'acg-world.com'
                    if parsed.scheme in ["http", "https"] and domain_filter in parsed.netloc:
                        if absolute_url not in discovered:
                            queue.append(absolute_url)
                            discovered.add(absolute_url)
                            print(f"New website found: {absolute_url}")
            else:
                print(f"Status code {response.status_code} for {current_url}")
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")
        time.sleep(1)  # Delay to avoid overloading the server
    return discovered

# Function to save discovered URLs to an XML sitemap file
def save_sitemap(urls, output_file="expanded_sitemap.xml"):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in urls:
        url_el = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_el, "loc")
        loc.text = url
    tree = ET.ElementTree(urlset)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Saved {len(urls)} URLs to {output_file}")

if __name__ == "__main__":
    sitemap_file = r"C:\Users\surya\Downloads\sitemap.xml"  # Make sure your sitemap.xml is in the same folder or provide full path
    seed_urls = parse_sitemap(sitemap_file)
    print("Seed URLs from sitemap:", seed_urls)
    
    # Crawl only URLs under acg-world.com up to 1000 links
    discovered_urls = crawl(seed_urls, max_links=1000)
    
    # Save the filtered URLs into an XML sitemap
    save_sitemap(discovered_urls, output_file="expanded_sitemap.xml")
