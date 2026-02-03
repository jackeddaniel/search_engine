#!/usr/bin/env python3
"""
robots.txt Checker - Test which of your seed URLs allow crawling
Run this BEFORE crawling to know which sites to expect issues with
"""

import sys
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import socket


def check_robots_txt(url, user_agent="*"):
    """
    Check if a URL allows crawling according to robots.txt
    
    Returns:
        tuple: (can_fetch: bool, reason: str)
    """
    try:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{domain}/robots.txt"
        
        # Create parser
        rp = RobotFileParser()
        rp.set_url(robots_url)
        
        # Set timeout
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10)
        
        try:
            rp.read()
            socket.setdefaulttimeout(old_timeout)
        except Exception as e:
            socket.setdefaulttimeout(old_timeout)
            return True, f"No robots.txt or read failed ({e})"
        
        # Check if URL can be fetched
        can_fetch = rp.can_fetch(user_agent, url)
        
        if can_fetch:
            return True, "Allowed by robots.txt"
        else:
            return False, "Blocked by robots.txt"
            
    except Exception as e:
        return None, f"Error checking: {e}"


def check_seed_file(seed_file, user_agent="*"):
    """
    Check all URLs in a seed file
    """
    print(f"\n{'='*80}")
    print(f"Checking robots.txt for seed URLs")
    print(f"User-Agent: {user_agent}")
    print(f"{'='*80}\n")
    
    try:
        with open(seed_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"❌ Seed file not found: {seed_file}")
        return
    
    allowed = []
    blocked = []
    errors = []
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Checking: {url}")
        can_fetch, reason = check_robots_txt(url, user_agent)
        
        if can_fetch is True:
            print(f"  ✅ {reason}")
            allowed.append(url)
        elif can_fetch is False:
            print(f"  ❌ {reason}")
            blocked.append(url)
        else:
            print(f"  ⚠️  {reason}")
            errors.append(url)
        print()
    
    # Summary
    print(f"{'='*80}")
    print(f"Summary")
    print(f"{'='*80}")
    print(f"Total URLs checked: {len(urls)}")
    print(f"✅ Allowed: {len(allowed)}")
    print(f"❌ Blocked: {len(blocked)}")
    print(f"⚠️  Errors: {len(errors)}")
    print(f"{'='*80}\n")
    
    if blocked:
        print("🚫 Blocked URLs:")
        for url in blocked:
            print(f"  - {url}")
        print()
    
    if errors:
        print("⚠️  URLs with errors:")
        for url in errors:
            print(f"  - {url}")
        print()
    
    if allowed:
        print("✅ URLs you can crawl:")
        for url in allowed:
            print(f"  - {url}")
        print()
    
    # Recommendations
    print("💡 Recommendations:")
    if blocked:
        print("  - Remove blocked URLs from your seed file, OR")
        print("  - Use their APIs instead (if available), OR")
        print("  - Accept that you'll skip those sites")
    if allowed:
        print(f"  - Start with the {len(allowed)} allowed URLs")
        print("  - These sites welcome crawlers!")
    if errors:
        print("  - Check error URLs manually")
        print("  - They might be down or have network issues")


def check_single_url(url, user_agent="*"):
    """Check a single URL"""
    print(f"\nChecking: {url}")
    print(f"User-Agent: {user_agent}\n")
    
    can_fetch, reason = check_robots_txt(url, user_agent)
    
    if can_fetch is True:
        print(f"✅ {reason}")
        print("You can crawl this URL!")
    elif can_fetch is False:
        print(f"❌ {reason}")
        print("This site blocks your crawler.")
        print("\nAlternatives:")
        print("  1. Check if they have an API")
        print("  2. Try a different user agent (e.g., 'Googlebot')")
        print("  3. Skip this site")
    else:
        print(f"⚠️  {reason}")
        print("Could not determine robots.txt status.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check robots.txt for seed URLs")
    parser.add_argument(
        "input",
        nargs="?",
        help="Seed file path or single URL to check"
    )
    parser.add_argument(
        "-u", "--user-agent",
        default="*",
        help="User agent string to test (default: '*')"
    )
    
    args = parser.parse_args()
    
    if not args.input:
        # Default to seed file
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        seed_file = os.path.join(script_dir, 'seed', 'urls.txt')
        
        if os.path.exists(seed_file):
            check_seed_file(seed_file, args.user_agent)
        else:
            print(f"No seed file found at {seed_file}")
            print("\nUsage:")
            print(f"  {sys.argv[0]} seed/urls.txt")
            print(f"  {sys.argv[0]} https://example.com")
    elif args.input.startswith('http://') or args.input.startswith('https://'):
        # Single URL
        check_single_url(args.input, args.user_agent)
    else:
        # Seed file
        check_seed_file(args.input, args.user_agent)
