import spacy
from collections import defaultdict

nlp = spacy.load("pt_core_news_lg")


def make_consult(query_file: str, base_file: str) -> set:
    with open(query_file, "r") as file:
        query = file.read().strip()

    inverted_index = build_inverted_index(base_file)

    return __process_query(query, inverted_index, base_file)


def build_inverted_index(base_file: str) -> defaultdict:
    inverted_index = defaultdict(list)

    with open(base_file, "r") as file:
        documents = file.read().splitlines()

    for doc_id, doc_path in enumerate(documents, 1):
        with open(doc_path, "r") as file:
            content = file.read()

        tokens = __retrieve_tokens(content)

        for token in set(tokens):
            count = tokens.count(token)
            inverted_index[token].append((doc_id, count))

    with open("indice.txt", "w") as file:
        for term, doc_list in sorted(inverted_index.items()):
            postings = " ".join(f"{doc_id},{count}" for doc_id, count in doc_list)
            file.write(f"{term}: {postings}\n")

    return inverted_index


def __process_query(query: str, inverted_index: defaultdict, base_file: str) -> set:
    terms = query.lower().split()

    with open(base_file, "r") as file:
        documents = file.read().splitlines()

    result_docs = set()
    result_docs_aux = set()
    result_docs_constant = set(range(1, len(documents) + 1))
    unions = set()
    differences = set()

    i = 0
    k = 0
    sub_queries = []
    current_sub_query = []

    while k < len(terms):
        if terms[k] == "|":
            if current_sub_query:
                sub_queries.append(current_sub_query)
                current_sub_query = []
        else:
            current_sub_query.append(terms[k])
        k += 1

    if current_sub_query:
        sub_queries.append(current_sub_query)

    while i < len(sub_queries):
        if len(sub_queries[i]) == 1:
            if sub_queries[i][0][0] == "!":
                token = sub_queries[i][0][1:]
                result_docs_aux = set(
                    doc_id for doc_id, _ in inverted_index.get(token, [])
                )
                unions = unions.union(result_docs_constant - result_docs_aux)
            else:
                unions = unions.union(
                    set(
                        doc_id
                        for doc_id, _ in inverted_index.get(sub_queries[i][0], [])
                    )
                )
        else:
            token = sub_queries[i][0]
            if token[0] == "!":
                result_docs_aux = set(
                    doc_id for doc_id, _ in inverted_index.get(token[1:], [])
                )
                differences = differences.union(result_docs_constant - result_docs_aux)
            else:
                result_docs_aux = set(
                    doc_id for doc_id, _ in inverted_index.get(token, [])
                )
                differences = differences.union(result_docs_aux)
            for j in range(2, len(sub_queries[i]), 2):
                token = sub_queries[i][j]
                if token[0] == "!":
                    token = token[1:]
                    result_docs_aux = set(
                        doc_id for doc_id, _ in inverted_index.get(token, [])
                    )
                    differences = differences.difference(result_docs_aux)
                else:
                    differences = differences.intersection(
                        set(doc_id for doc_id, _ in inverted_index.get(token, []))
                    )
            unions = unions.union(differences)
        i += 1
    result_docs = result_docs.union(unions)

    with open("resposta.txt", "w") as file:
        file.write(f"{len(result_docs)}\n")
        for doc_id in sorted(result_docs):
            file.write(f"{documents[doc_id - 1]}\n")

    return sorted(result_docs)


def __retrieve_tokens(text: str) -> list:
    doc = nlp(text.lower())
    return [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and token.lemma_.strip()
        and " " not in token.lemma_
    ]


if _name_ == "_main_":
    import sys

    base_file = sys.argv[1]
    query_file = sys.argv[2]

    make_consult(query_file, base_file)