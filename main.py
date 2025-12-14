from pathlib import Path
from collections import defaultdict
from index_builder import build_index
from parse_help import normalize_text, tokenize
import math

def get_candidate_docs_dict(inverted_index, tokens):
    if not inverted_index:
        print("No inverted index")
        return None
    if not tokens:
        print("No token list")
        return None

    docs = {}

    for token in tokens:
        if token not in inverted_index:
            continue
        print(f"token being looked up {token}")
        for doc_id, freq in inverted_index[token].items():
            print(f"Document id is {doc_id} and frequence is {freq}")
            if doc_id not in docs:
                docs[doc_id] = {token: freq}
            
            docs[doc_id][token] = freq

    return docs

def score_docs(inverted_index, doc_len_dict, cand_dict, tokens):
    n = 19000

    score = defaultdict(float)
    
    for doc_id in cand_dict:
        score[doc_id] = 0.0

        for token in cand_dict[doc_id]:
            term_freq = cand_dict[doc_id][token]
            doc_freq = len(inverted_index[token])
            doc_len = doc_len_dict[doc_id]
            
            ratio = n/(1 + doc_freq)
            idf = math.log(ratio)

            score[doc_id] += (term_freq/doc_len)*idf  

    return dict(score)



def main():
    DIR_NAME = "datasets/docs"

    path = Path(DIR_NAME)

    inverted_index, doc_len_dict = build_index(path)

    print(len(inverted_index))

    count = 0

    for key, val in inverted_index.items():
        if count >= 5:
            break

        print(f"{key} : {val}")
        count += 1

    query = "computer science"

    query_text = normalize_text(query)
    query_tokens = tokenize(query_text)

    candidate_docs = get_candidate_docs_dict(inverted_index, query_tokens)
    score = score_docs(inverted_index, doc_len_dict, candidate_docs, query_tokens)
    
    sorted_score = sorted(score.items(), key= lambda item: item[1], reverse=True)
    #print(candidate_docs)
    print(sorted_score[:10])

    print(f"candidate docs num {len(candidate_docs)} and score size is {len(score)}")



if __name__ == "__main__":
    main()
