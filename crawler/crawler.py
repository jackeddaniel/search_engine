# PLAN:
# We run a multi-source bfs
# We prepare a queue (since python we're using double ended queue
# We load up the queue with the seed urls
# Then we run a bfs upto certain depth and at each level store the html and collect the links from the HTML 

import os
import requests
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen

def load_urls_to_deque(file_path):
    """Load seed URLs from a file into a deque."""
    url_queue = deque()
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                url = line.strip()
                
                if url:
                    url_queue.append((url, 0))  # (url, depth)
                    
        print(f"Successfully loaded {len(url_queue)} seed URLs.")
        return url_queue

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return deque()


class RobotChecker:
    """Check robots.txt compliance for URLs."""
    def __init__(self):
        self.robots_cache = {}
        self.user_agent = "search-engine-crawler/1.0"
    
    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # Cache robots.txt parsers per domain
            if domain not in self.robots_cache:
                rp = RobotFileParser()
                robots_url = f"{domain}/robots.txt"
                rp.set_url(robots_url)
                try:
                    rp.read()
                except:
                    # If robots.txt doesn't exist, assume we can fetch
                    rp = None
                self.robots_cache[domain] = rp
            
            robot = self.robots_cache[domain]
            if robot is None:
                return True
            
            return robot.can_fetch(self.user_agent, url)
        except Exception as e:
            print(f"Error checking robots.txt for {url}: {e}")
            # Be conservative - don't crawl if we can't verify
            return False


class DomainRateLimiter:
    """Rate limit requests per domain."""
    def __init__(self, default_delay=1.0):
        self.domain_last_request = {}
        self.default_delay = default_delay
    
    def wait_if_needed(self, url):
        """Wait if needed based on domain rate limiting."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain in self.domain_last_request:
            elapsed = time.time() - self.domain_last_request[domain]
            if elapsed < self.default_delay:
                wait_time = self.default_delay - elapsed
                time.sleep(wait_time)
        
        self.domain_last_request[domain] = time.time()


def download_file(url, save_dir, doc_id, rate_limiter, robot_checker):
    """
    Download HTML content from a URL and save it to a file.
    Returns the saved file path if successful, None otherwise.
    Respects robots.txt and implements rate limiting.
    """
    try:
        # Check robots.txt compliance
        if not robot_checker.can_fetch(url):
            print(f"Blocked by robots.txt: {url}")
            return None
        
        # Apply rate limiting
        rate_limiter.wait_if_needed(url)
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Create save directory if it doesn't exist
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        # Save file with doc_id as filename
        file_path = Path(save_dir) / f"{doc_id}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return str(file_path)
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None
    except Exception as e:
        print(f"Error saving {url}: {e}")
        return None


def parse_url(file_path, base_url):
    """
    Parse HTML file and extract all links.
    Converts relative URLs to absolute URLs using base_url.
    Returns a list of absolute URLs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # Extract all <a> tags with href attributes
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            
            # Skip javascript:, mailto:, and other non-http links
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            
            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)
            normalized = normalize_url(absolute_url)
            
            if normalized:
                links.append(normalized)
        
        return links
    
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def normalize_url(url, base_url=None):
    """
    Normalize and validate URLs.
    Convert relative URLs to absolute if base_url is provided.
    """
    try:
        # If base_url is provided and url is relative, make it absolute
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # Parse and validate URL
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            # Remove fragments
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{('?' + parsed.query) if parsed.query else ''}"
        return None
    except Exception:
        return None


def bfs(url_queue, save_dir, max_urls, max_depth=2, delay_between_requests=1.0, same_domain_only=False):
    """
    Perform BFS crawling starting from seed URLs.
    
    Args:
        url_queue: deque of (url, depth) tuples
        save_dir: directory to save downloaded HTML files
        max_urls: maximum number of URLs to crawl
        max_depth: maximum depth to crawl (0 = seed URLs only)
        delay_between_requests: delay in seconds between requests per domain
        same_domain_only: if True, only crawl URLs from the same domain as seed URLs
    """
    if not url_queue:
        print("No URLs to crawl.")
        return
    
    visited = set()  # Track visited URLs to avoid duplicates
    doc_id = 0  # Document ID counter
    crawled_count = 0
    failed_count = 0
    
    robot_checker = RobotChecker()
    rate_limiter = DomainRateLimiter(default_delay=delay_between_requests)
    
    # Extract seed domains if same_domain_only is enabled
    seed_domains = set()
    if same_domain_only:
        for url, _ in url_queue:
            parsed = urlparse(url)
            seed_domains.add(parsed.netloc)
    
    print(f"Starting BFS crawl with max_urls={max_urls}, max_depth={max_depth}")
    if same_domain_only:
        print(f"Restricting to seed domains: {seed_domains}")
    print(f"Delay between requests: {delay_between_requests}s")
    print(f"Respecting robots.txt: Yes\n")
    
    while url_queue and crawled_count < max_urls:
        url, depth = url_queue.popleft()
        
        # Skip if depth exceeds max_depth
        if depth > max_depth:
            continue
        
        # Normalize URL first
        normalized_url = normalize_url(url)
        if not normalized_url:
            continue
        
        # Skip if already visited
        if normalized_url in visited:
            continue
        
        # Check domain restriction
        if same_domain_only:
            parsed = urlparse(normalized_url)
            if parsed.netloc not in seed_domains:
                continue
        
        print(f"[{crawled_count + 1}/{max_urls}] Crawling (depth {depth}): {normalized_url}")
        
        # Download the page
        saved_file_path = download_file(normalized_url, save_dir, doc_id, rate_limiter, robot_checker)
        
        if saved_file_path:
            visited.add(normalized_url)
            crawled_count += 1
            
            # Parse and extract links if we haven't reached max depth
            if depth < max_depth:
                links = parse_url(saved_file_path, normalized_url)
                
                # Add new links to queue (already normalized in parse_url)
                for link in links:
                    if link not in visited:
                        url_queue.append((link, depth + 1))
            
            doc_id += 1
        else:
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Crawl complete!")
    print(f"Successfully crawled: {crawled_count} URLs")
    print(f"Failed: {failed_count} URLs")
    print(f"Total documents: {doc_id}")
    print(f"Saved to: {save_dir}")
    print(f"{'='*60}")


# Implementation
if __name__ == "__main__":
    # Get the absolute path to the seed URLs file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = os.path.join(script_dir, 'seed', 'urls.txt')
    save_directory = 'docs'  # Directory to save crawled HTML files
    
    # Crawler configuration
    max_urls_to_crawl = 10          # Maximum number of URLs to crawl
    max_crawl_depth = 1             # Maximum depth from seed URLs (0 = seed only, 1 = seed + direct links, etc.)
    delay_between_requests = 2.0    # Delay in seconds between requests per domain (avoid rate limiting)
    same_domain_only = True         # Only crawl URLs from the same domain as seed URLs
    
    my_urls = load_urls_to_deque(file_name)
    
    if my_urls:
        bfs(my_urls, save_directory, max_urls_to_crawl, max_crawl_depth, delay_between_requests, same_domain_only)
    else:
        print("No seed URLs loaded. Exiting.")
