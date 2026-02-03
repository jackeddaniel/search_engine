# PRODUCTION WEB CRAWLER FOR SEARCH ENGINE
# Multi-source BFS crawler with proper robots.txt handling, rate limiting, and error recovery

import os
import requests
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from urllib.robotparser import RobotFileParser
import logging
from typing import Set, Deque, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_urls_to_deque(file_path: str) -> Deque[Tuple[str, int]]:
    """Load seed URLs from a file into a deque."""
    url_queue = deque()
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                url = line.strip()
                if url and not url.startswith('#'):  # Allow comments in seed file
                    url_queue.append((url, 0))  # (url, depth)
                    
        logger.info(f"Successfully loaded {len(url_queue)} seed URLs from {file_path}")
        return url_queue
    except FileNotFoundError:
        logger.error(f"Seed file not found: {file_path}")
        return deque()


class RobotChecker:
    """Check robots.txt compliance for URLs with proper caching and error handling."""
    
    def __init__(self, user_agent: str = "SearchEngineBot/1.0", respect_robots: bool = True):
        self.robots_cache = {}  # domain -> RobotFileParser
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.failed_domains = set()  # Track domains where robots.txt failed to load
        
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.respect_robots:
            return True
            
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # If we've already failed to load robots.txt for this domain, allow crawling
            if domain in self.failed_domains:
                return True
            
            # Cache robots.txt parsers per domain
            if domain not in self.robots_cache:
                logger.info(f"Fetching robots.txt for {domain}")
                rp = RobotFileParser()
                robots_url = f"{domain}/robots.txt"
                rp.set_url(robots_url)
                
                try:
                    # Set a timeout for reading robots.txt
                    import socket
                    old_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(10)
                    
                    rp.read()
                    
                    socket.setdefaulttimeout(old_timeout)
                    
                    self.robots_cache[domain] = rp
                    logger.info(f"Successfully loaded robots.txt for {domain}")
                    
                except Exception as e:
                    # If robots.txt doesn't exist or fails to load, mark domain and allow crawling
                    logger.warning(f"Could not read robots.txt for {domain}: {e}. Allowing crawl.")
                    self.failed_domains.add(domain)
                    return True
            
            robot = self.robots_cache.get(domain)
            if robot is None:
                return True
            
            can_crawl = robot.can_fetch(self.user_agent, url)
            
            if not can_crawl:
                logger.info(f"Blocked by robots.txt: {url}")
            
            return can_crawl
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}. Allowing crawl.")
            return True


class DomainRateLimiter:
    """Rate limit requests per domain to be respectful."""
    
    def __init__(self, default_delay: float = 1.0):
        self.domain_last_request = {}
        self.default_delay = default_delay
    
    def wait_if_needed(self, url: str):
        """Wait if needed based on domain rate limiting."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain in self.domain_last_request:
            elapsed = time.time() - self.domain_last_request[domain]
            if elapsed < self.default_delay:
                wait_time = self.default_delay - elapsed
                time.sleep(wait_time)
        
        self.domain_last_request[domain] = time.time()


def download_file(url: str, save_dir: str, doc_id: int, 
                 rate_limiter: DomainRateLimiter, 
                 robot_checker: RobotChecker) -> Optional[str]:
    """
    Download HTML content from a URL and save it to a file.
    Returns the saved file path if successful, None otherwise.
    """
    try:
        # Check robots.txt compliance
        if not robot_checker.can_fetch(url):
            return None
        
        # Apply rate limiting
        rate_limiter.wait_if_needed(url)
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        # Only process HTML content
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type:
            logger.info(f"Skipping non-HTML content: {url} (type: {content_type})")
            return None
        
        # Create save directory if it doesn't exist
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        # Save file with doc_id as filename
        file_path = Path(save_dir) / f"{doc_id}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Also save metadata
        metadata_path = Path(save_dir) / f"{doc_id}.meta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(f"url: {url}\n")
            f.write(f"status: {response.status_code}\n")
            f.write(f"content-type: {content_type}\n")
            f.write(f"size: {len(response.text)}\n")
        
        logger.info(f"✓ Downloaded: {url} -> {file_path} ({len(response.text)} bytes)")
        return str(file_path)
    
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout downloading {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error downloading {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving {url}: {e}")
        return None


def parse_url(file_path: str, base_url: str) -> List[str]:
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
            
            # Skip non-HTTP links
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'data:')):
                continue
            
            # Convert to absolute URL
            absolute_url = urljoin(base_url, href)
            normalized = normalize_url(absolute_url)
            
            if normalized:
                links.append(normalized)
        
        # Remove duplicates while preserving order
        unique_links = list(dict.fromkeys(links))
        logger.debug(f"Extracted {len(unique_links)} unique links from {file_path}")
        
        return unique_links
    
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return []


def normalize_url(url: str) -> Optional[str]:
    """
    Normalize and validate URLs.
    """
    try:
        parsed = urlparse(url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return None
        
        # Only HTTP/HTTPS
        if parsed.scheme not in ('http', 'https'):
            return None
        
        # Remove fragments and normalize
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Add query string if present
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        # Remove trailing slash for consistency (except for root)
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        
        return normalized
        
    except Exception:
        return None


def bfs(url_queue: Deque[Tuple[str, int]], 
        save_dir: str, 
        max_urls: int, 
        max_depth: int = 2, 
        delay_between_requests: float = 1.0, 
        same_domain_only: bool = False,
        respect_robots: bool = True,
        user_agent: str = "SearchEngineBot/1.0") -> dict:
    """
    Perform BFS crawling starting from seed URLs.
    
    Returns:
        dict with crawl statistics
    """
    if not url_queue:
        logger.error("No URLs to crawl")
        return {}
    
    visited: Set[str] = set()
    doc_id = 0
    crawled_count = 0
    failed_count = 0
    blocked_count = 0
    
    robot_checker = RobotChecker(user_agent=user_agent, respect_robots=respect_robots)
    rate_limiter = DomainRateLimiter(default_delay=delay_between_requests)
    
    # Extract seed domains if same_domain_only is enabled
    seed_domains: Set[str] = set()
    if same_domain_only:
        for url, _ in list(url_queue):
            parsed = urlparse(url)
            seed_domains.add(parsed.netloc)
    
    logger.info("="*60)
    logger.info("Starting BFS Web Crawl")
    logger.info("="*60)
    logger.info(f"Max URLs: {max_urls}")
    logger.info(f"Max depth: {max_depth}")
    logger.info(f"Delay per domain: {delay_between_requests}s")
    logger.info(f"Same domain only: {same_domain_only}")
    logger.info(f"Respect robots.txt: {respect_robots}")
    logger.info(f"User agent: {user_agent}")
    if same_domain_only:
        logger.info(f"Seed domains: {seed_domains}")
    logger.info("="*60)
    
    start_time = time.time()
    
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
        
        logger.info(f"[{crawled_count + 1}/{max_urls}] Depth {depth}: {normalized_url}")
        
        # Mark as visited before attempting (to avoid re-queuing on failure)
        visited.add(normalized_url)
        
        # Download the page
        saved_file_path = download_file(normalized_url, save_dir, doc_id, rate_limiter, robot_checker)
        
        if saved_file_path:
            crawled_count += 1
            
            # Parse and extract links if we haven't reached max depth
            if depth < max_depth:
                links = parse_url(saved_file_path, normalized_url)
                
                # Add new links to queue
                for link in links:
                    if link not in visited:
                        url_queue.append((link, depth + 1))
            
            doc_id += 1
        else:
            # Check if it was blocked by robots.txt
            if not robot_checker.can_fetch(normalized_url):
                blocked_count += 1
            else:
                failed_count += 1
    
    elapsed_time = time.time() - start_time
    
    stats = {
        'crawled': crawled_count,
        'failed': failed_count,
        'blocked': blocked_count,
        'total_visited': len(visited),
        'elapsed_time': elapsed_time,
        'avg_time_per_url': elapsed_time / max(crawled_count, 1)
    }
    
    logger.info("="*60)
    logger.info("Crawl Complete!")
    logger.info("="*60)
    logger.info(f"Successfully crawled: {crawled_count} URLs")
    logger.info(f"Failed: {failed_count} URLs")
    logger.info(f"Blocked by robots.txt: {blocked_count} URLs")
    logger.info(f"Total visited: {len(visited)} URLs")
    logger.info(f"Documents saved: {doc_id}")
    logger.info(f"Time elapsed: {elapsed_time:.2f}s")
    logger.info(f"Average time per URL: {stats['avg_time_per_url']:.2f}s")
    logger.info(f"Saved to: {save_dir}")
    logger.info("="*60)
    
    return stats


if __name__ == "__main__":
    # Configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    seed_file = os.path.join(script_dir, 'seed', 'urls.txt')
    save_directory = 'docs'
    
    # ==========================================
    # CRAWLER CONFIGURATION
    # ==========================================
    
    max_urls_to_crawl = 100         # Maximum number of URLs to crawl
    max_crawl_depth = 2             # Maximum depth from seed URLs
    delay_between_requests = 1.0    # Delay in seconds between requests per domain
    same_domain_only = False        # Set to True to only crawl seed domains
    
    # robots.txt settings
    respect_robots_txt = True       # Should respect robots.txt
    user_agent_string = "SearchEngineBot/1.0 (+http://yoursite.com/bot)"  # Identify your bot
    
    # Load seed URLs
    url_queue = load_urls_to_deque(seed_file)
    
    if url_queue:
        stats = bfs(
            url_queue, 
            save_directory, 
            max_urls_to_crawl, 
            max_crawl_depth, 
            delay_between_requests, 
            same_domain_only,
            respect_robots=respect_robots_txt,
            user_agent=user_agent_string
        )
        
        logger.info(f"\nCrawl statistics: {stats}")
    else:
        logger.error("No seed URLs loaded. Exiting.")
