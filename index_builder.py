from pathlib import Path
from collections import defaultdict, Counter
from parse_help import normalize, tokenize


def build_index(directory_path):
    inverted_index = defaultdict(dict)
    dir_path = Path(directory_path)

    print("starting processing")
    doc_id = 0

    for entry in dir_path.iterdir():
        if entry.is_file():
            print(entry)

            text = normalize(entry)
            tokens = tokenize(text)

            freq = Counter(tokens)

            for term, count in freq.items():
                inverted_index[term][doc_id]= count

            doc_id += 1

    return dict(inverted_index)




