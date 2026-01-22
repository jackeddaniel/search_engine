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


def download_file(url, save_dir, doc_id):
    """
    Download HTML content from a URL and save it to a file.
    Returns the saved file path if successful, None otherwise.
    """
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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


def bfs(url_queue, save_dir, max_urls, max_depth=2):
    """
    Perform BFS crawling starting from seed URLs.
    
    Args:
        url_queue: deque of (url, depth) tuples
        save_dir: directory to save downloaded HTML files
        max_urls: maximum number of URLs to crawl
        max_depth: maximum depth to crawl (0 = seed URLs only)
    """
    if not url_queue:
        print("No URLs to crawl.")
        return
    
    visited = set()  # Track visited URLs to avoid duplicates
    doc_id = 0  # Document ID counter
    crawled_count = 0
    
    print(f"Starting BFS crawl with max_urls={max_urls}, max_depth={max_depth}")
    
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
        
        print(f"[{crawled_count + 1}/{max_urls}] Crawling (depth {depth}): {normalized_url}")
        
        # Download the page
        saved_file_path = download_file(normalized_url, save_dir, doc_id)
        
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
        
        # Be polite - add a small delay between requests
        time.sleep(0.5)
    
    print(f"\nCrawl complete! Crawled {crawled_count} URLs, saved to {save_dir}")


# Implementation
if __name__ == "__main__":
    file_name = 'crawler/seed/urls.txt'
    save_directory = 'docs'  # Directory to save crawled HTML files
    max_urls_to_crawl = 30  # Maximum number of URLs to crawl
    max_crawl_depth = 2  # Maximum depth from seed URLs
    
    my_urls = load_urls_to_deque(file_name)
    
    if my_urls:
        bfs(my_urls, save_directory, max_urls_to_crawl, max_crawl_depth)
    else:
        print("No seed URLs loaded. Exiting.")
