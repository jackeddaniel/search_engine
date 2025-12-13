from pathlib import Path
from index_builder import build_index
from parse_help import normalize_text, tokenize


def get_candidate_docs(inverted_index, tokens):
    if not inverted_index:
        print("No inverted index")
        return None
    if not tokens:
        print("No token list")
        return None

    docs = []

    for token in tokens:
        for doc_id, freq in inverted_index[token].items():
            print(f"Document id is {doc_id} and frequence is {freq}")
            docs.append([doc_id, freq])

    return docs

def main():
    DIR_NAME = "datasets/docs"

    path = Path(DIR_NAME)

    inverted_index = build_index(path)

    print(len(inverted_index))

    count = 0

    for key, val in inverted_index.items():
        if count >= 5:
            break

        print(f"{key} : {val}")
        count += 1

    query = "dogs"

    query_text = normalize_text(query)
    query_tokens = tokenize(query_text)

    candidate_docs = get_candidate_docs(inverted_index, query_tokens)

    print(candidate_docs)



if __name__ == "__main__":
    main()
