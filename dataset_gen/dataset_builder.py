import os

from sklearn.datasets import fetch_20newsgroups

data = fetch_20newsgroups(remove=('headers','footers','quotes'))
print(type(data))

os.makedirs("docs", exist_ok=True)

for i, text in enumerate(data.data):
    print(f"document{i} being written\n")
    with open(f"docs/{i}.txt", "w", encoding="utf-8") as f:
        f.write(text)
