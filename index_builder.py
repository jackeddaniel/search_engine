from pathlib import Path
from collections import defaultdict, Counter
from parse_help import normalize, tokenize


def build_index(directory_path):
    inverted_index = defaultdict(dict)
    doc_len_dict = defaultdict(int)
    dir_path = Path(directory_path)

    print("starting processing")

    for entry in dir_path.iterdir():
        if entry.is_file():
            print(entry)
            doc_id = int(entry.stem)
            print(f"processing doc_id= {doc_id}")

            text = normalize(entry)
            tokens = tokenize(text)

            doc_len_dict[doc_id] = len(tokens)

            freq = Counter(tokens)

            for term, count in freq.items():
                inverted_index[term][doc_id] = count
    print("indexing complete")


    return dict(inverted_index), dict(doc_len_dict)




