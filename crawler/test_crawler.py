from collections import deque

def load_urls_to_deque(file_path):
    url_queue = deque()

    with open(file_path, 'r') as file:
        for line in file:
            url = line.strip()
            if url:
                url_queue.append(url)

        return url_queue


def bfs_search(url_queue, max_depth=3):
    visited = set()
    current_depth = 0
    while url_queue and current_depth <= max_depth:
        current_url = url_queue.popleft()
        if current_url in visited:
            continue
        visited.add(current_url)
        print(f"Visiting: {current_url}")
        current_depth += 1
        url_queue.extend(get_links(current_url))

def get_links(url):
    return []
