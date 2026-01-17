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


if my_urls:
    print(f"First URL in deque: {my_urls[0]}")

print(my_urls)
