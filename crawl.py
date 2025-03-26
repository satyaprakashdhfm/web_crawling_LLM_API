import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from typing import Set

class SimpleLinkCrawler:
    """A simple web crawler to find URLs not listed in a sitemap."""
    
    def __init__(self, base_url: str, sitemap_path: str):
        """
        Initialize the crawler with a base URL and sitemap path.
        
        :param base_url: The starting URL for the crawl (e.g., 'https://www.example.com')
        :param sitemap_path: Path to the local sitemap.xml file
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(self.base_url).netloc
        self.sitemap_urls = self._parse_sitemap(sitemap_path)
        self.discovered_urls = set()

    def _parse_sitemap(self, sitemap_path: str) -> Set[str]:
        """
        Parse the sitemap.xml file and extract URLs.
        
        :param sitemap_path: Path to the sitemap.xml file
        :return: Set of URLs from the sitemap
        """
        try:
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = {elem.text.strip() for elem in root.findall('.//ns:loc', namespace) if elem.text}
            return urls
        except FileNotFoundError:
            print(f"Error: Sitemap file not found at {sitemap_path}")
            return set()
        except ET.ParseError:
            print(f"Error: Failed to parse sitemap XML at {sitemap_path}")
            return set()
        except Exception as e:
            print(f"Unexpected error parsing sitemap: {e}")
            return set()

    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and within the same domain.
        
        :param url: URL to validate
        :return: True if valid and in-domain, False otherwise
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            if parsed.netloc != self.domain:
                return False
            # Exclude non-HTML file extensions
            invalid_extensions = {'.pdf', '.jpg', '.png', '.gif', '.zip'}
            return not any(url.lower().endswith(ext) for ext in invalid_extensions)
        except ValueError:
            return False

    def extract_links(self, url: str) -> Set[str]:
        """
        Extract links from a given URL.
        
        :param url: URL to extract links from
        :return: Set of valid extracted links
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Non-200 status code for {url}: {response.status_code}")
                return set()

            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()
            for anchor in soup.find_all('a', href=True):
                full_url = urljoin(url, anchor['href'])
                if self.is_valid_url(full_url):
                    links.add(full_url)
            return links
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return set()

    def find_new_links(self) -> Set[str]:
        """
        Crawl the website and find URLs not in the sitemap.
        
        :return: Set of URLs discovered during crawl but not in sitemap
        """
        to_crawl = [self.base_url]
        crawled = set()
        
        while to_crawl:
            url = to_crawl.pop(0)
            if url in crawled:
                continue
                
            crawled.add(url)
            new_links = self.extract_links(url)
            self.discovered_urls.update(new_links)
            
            # Add new links to crawl queue (up to 10 per page)
            to_crawl.extend(
                link for link in new_links 
                if link not in crawled and link not in to_crawl
            )[:10]
        
        return self.discovered_urls - self.sitemap_urls

def main():
    """Main function to run the crawler."""
    crawler = SimpleLinkCrawler(
        base_url='https://www.acg-world.com',
        sitemap_path=r"C:\Users\surya\Downloads\sitemap.xml"
    )
    new_urls = crawler.find_new_links()
    print("URLs found but not in sitemap:")
    for url in sorted(new_urls):
        print(url)

if __name__ == "__main__":
    main()