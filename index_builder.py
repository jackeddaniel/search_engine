import logging

from pathlib import Path
from collections import defaultdict, Counter
from parse_help import normalize, tokenize


def build_index(directory_path):
    inverted_index = defaultdict(dict)
    doc_len_dict = defaultdict(int)
    dir_path = Path(directory_path)

    logging.info("starting processing")
    doc_num = 0
    total_doc_len = 0

    for entry in dir_path.iterdir():
        if entry.is_file():
            logging.debug(f"Entry: {entry}")
            doc_id = int(entry.stem)
            logging.debug(f"processing doc_id= {doc_id}")

            text = normalize(entry)
            tokens = tokenize(text)

            doc_len_dict[doc_id] = len(tokens)
            total_doc_len += doc_len_dict[doc_id]
            doc_num += 1

            freq = Counter(tokens)

            for term, count in freq.items():
                inverted_index[term][doc_id] = count
    logging.info("indexing complete")
    print(inverted_index)

    avgdl = total_doc_len/doc_num


    return dict(inverted_index), dict(doc_len_dict), avgdl




