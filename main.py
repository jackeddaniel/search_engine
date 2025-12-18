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
            print(f"Token {token} not found ")
            continue
        print(f"token being looked up {token}")
        for doc_id, freq in inverted_index[token].items():
            print(f"Document id is {doc_id} and frequence is {freq}")
            if doc_id not in docs:
                docs[doc_id] = {token: freq}
            
            docs[doc_id][token] = freq

    return docs

def score_docs(inverted_index, doc_len_dict, cand_dict, tokens):
    n = len(doc_len_dict)

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

def score_docs_bm25(inverted_index, doc_len_dict, cand_dict, tokens, avgdl):
    n = len(doc_len_dict)
    score = defaultdict(float)
    k1 = 1.5
    b = 0.75

    for doc_id in cand_dict:
        score[doc_id] = 0.0

        for token in cand_dict[doc_id]:
            term_freq = cand_dict[doc_id][token]
            doc_freq = len(inverted_index[token])
            doc_len = doc_len_dict[doc_id]

            ratio = (n - doc_freq + 0.5) / (doc_freq + 0.5)
            idf = math.log(ratio)

            score[doc_id] += idf * (term_freq * (k1+1)) / (term_freq + k1 * (1 - b + b*(doc_len/ avgdl)))

    return dict(score)


def print_top_docs(sorted_score, docs_dir, top_k=5, preview_len=300):
    print("\n===== TOP SEARCH RESULTS =====\n")

    for rank, (doc_id, score) in enumerate(sorted_score[:top_k], start=1):
        doc_path = docs_dir / f"{doc_id}.txt"

        print(f"Rank {rank}")
        print(f"Doc ID: {doc_id}")
        print(f"Score: {score:.4f}")
        print(f"File: {doc_path.name}")

        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read(preview_len)

            print("\nPreview:")
            print(content.replace("\n", " ")[:preview_len])
        except Exception as e:
            print(f"Could not read document: {e}")

        print("\n" + "-" * 70 + "\n")


def main():
    DIR_NAME = "datasets/docs"

    path = Path(DIR_NAME)

    inverted_index, doc_len_dict, avgdl = build_index(path)

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
    score = score_docs_bm25(inverted_index, doc_len_dict, candidate_docs, query_tokens, avgdl)
    #score = score_docs(inverted_index, doc_len_dict, candidate_docs, query_tokens)
    
    sorted_score = sorted(score.items(), key= lambda item: item[1], reverse=True)
    #print(candidate_docs)
    print(sorted_score[:5])
    
    print_top_docs(sorted_score, path,5, 10000)




if __name__ == "__main__":
    main()
