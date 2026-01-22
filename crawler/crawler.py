# PLAN:
# We run a multi-source bfs
# We prepare a queue (since python we're using double ended queue
# We load up the queue with the seed urls
# Then we run a bfs upto certain depth and at each level store the html and collect the links from the HTML 

from collections import deque

def load_urls_to_deque(file_path):
    url_queue = deque()
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                url = line.strip()
                
                if url:
                    url_queue.append(url)
                    
        print(f"Successfully loaded {len(url_queue)} URLs.")
        return url_queue

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return deque()



# Implementation
file_name = 'seed/urls.txt'
my_urls = load_urls_to_deque(file_name)

def bfs(deque, save_dir, max_urls):
    if not deque:
        return

    counter = 0

    per_file_url_limit = max_urls // len(deque)

    while(deque):
        url = deque.popleft()
        saved_file_path = download_file(url, save_dir)
        url_list = parse_url(file_path)
        counter += 1

        for i in range(0, min(per_file_url_limit, len(deque))):
            deque.push(url_list[i])


if my_urls:
    print(f"First URL in deque: {my_urls[0]}")

print(my_urls)
