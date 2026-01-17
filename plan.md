1. Crawling

This is how the search engine collects documents/webpages.

A crawler (spider) starts with seed URLs.

Downloads HTML pages.

Extracts links and visits them.

Stores all pages (raw HTML or cleaned text).

➡️ Output: raw documents

2. Parsing & Indexing

Creating a structure so search becomes fast.

Steps:

2.1 Parsing

Clean HTML → extract text

Normalize text (lowercase, remove punctuation, numbers etc.)

Tokenize (split into words)

Remove stopwords

Stem/lemmatize (optional)

➡️ Output: list of tokens per document

2.2 Indexing

Building data structures so searching is fast.

The core structure is:

📌 The Inverted Index

Maps each word → list of documents containing the word

Example:

Word	DocIDs
“apple”	[3, 7, 10]
“phone”	[3, 4, 9, 10]

This allows instant lookup instead of scanning all documents.

➡️ Output: an inverted index stored on disk

3. Query Processing

When the user types a search query:

Parse the query using same rules as documents

Convert query words into index lookups

Find candidate docs

4. Ranking

Rank documents using scoring models.

TF-IDF

BM25

PageRank (large distributed engines)

Neural models (transformers, embeddings)

➡️ Output: ordered list of documents

5. Retrieval

Return final results to the user.1. Crawling

