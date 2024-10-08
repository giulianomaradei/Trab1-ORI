import sys
import os
import spacy
from collections import defaultdict

nlp = spacy.load("pt_core_news_lg")

def read_base(base_file):
    with open(base_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]

def read_query(query_file):
    with open(query_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def preprocess_text(text):
    doc = nlp(text.lower())
    return [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and token.lemma_.strip()
        and " " not in token.lemma_
    ]

def generate_inverted_index(base_file):
    index = defaultdict(list)

    with open(base_file, 'r', encoding='utf-8') as f:
        documents = f.read().splitlines()

    for doc_id, doc_path in enumerate(documents, 1):
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        terms = preprocess_text(content)

        for term in set(terms):
            count = terms.count(term)
            index[term].append((doc_id, count))

    save_index(index)

    return index

def save_index(index):
    with open('index.txt', 'w', encoding='utf-8') as f:
        for term, doc_list in sorted(index.items()):
            postings = " ".join(f"{doc_id},{count}" for doc_id, count in doc_list)
            f.write(f"{term}: {postings}\n")

def process_query(query, index, files):
    terms = query.lower().split()
    result_docs = set()
    result_docs_aux = set()
    result_docs_constant = set(range(1, len(files) + 1))
    unions = set()
    differences = set()

    sub_queries = []
    current_sub_query = []

    for term in terms:
        if term == "|":
            if current_sub_query:
                sub_queries.append(current_sub_query)
                current_sub_query = []
        else:
            current_sub_query.append(term)

    if current_sub_query:
        sub_queries.append(current_sub_query)

    for sub_query in sub_queries:
        if len(sub_query) == 1:
            term = sub_query[0]
            if term.startswith("!"):
                token = term[1:]
                result_docs_aux = set(doc_id for doc_id, _ in index.get(token, []))
                unions = unions.union(result_docs_constant - result_docs_aux)
            else:
                unions = unions.union(set(doc_id for doc_id, _ in index.get(term, [])))
        else:
            differences = set()
            for i, term in enumerate(sub_query):
                if i % 2 == 0:  # Term, not operator
                    if term.startswith("!"):
                        token = term[1:]
                        result_docs_aux = set(doc_id for doc_id, _ in index.get(token, []))
                        if i == 0:
                            differences = result_docs_constant - result_docs_aux
                        else:
                            differences = differences.difference(result_docs_aux)
                    else:
                        if i == 0:
                            differences = set(doc_id for doc_id, _ in index.get(term, []))
                        else:
                            differences = differences.intersection(set(doc_id for doc_id, _ in index.get(term, [])))
            unions = unions.union(differences)

    result_docs = result_docs.union(unions)
    return result_docs

def save_response(documents, files):
    with open('response.txt', 'w', encoding='utf-8') as f:
        f.write(f"{len(documents)}\n")
        for doc_id in sorted(documents):
            f.write(f"{files[doc_id - 1]}\n")

def main(base_file, query_file):
    index = generate_inverted_index(base_file)
    query = read_query(query_file)

    documents = process_query(query, index, base_file)
    save_response(documents, base_file)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python boolean_model.py <base_file> <query_file>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])