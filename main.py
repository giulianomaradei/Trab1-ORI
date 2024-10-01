import sys
import os
import spacy
import string

nlp = spacy.load("pt_core_news_sm")

def ler_base(arquivo_base):
    print(f"Current working directory: {os.getcwd()}")
    print(f"Trying to open file: {arquivo_base}")

    # List files in the current directory
    print("Files in the current directory:")
    print(os.listdir())

    try:
        with open(arquivo_base, 'r', encoding='utf-8') as f:
            return [linha.strip() for linha in f]
    except FileNotFoundError:
        print(f"Error: The file '{arquivo_base}' was not found.")
        # You might want to exit the program here or handle the error differently
        raise

def ler_consulta(arquivo_consulta):
    with open(arquivo_consulta, 'r', encoding='utf-8') as f:
        return f.read().strip()

def preprocessar_texto(texto):
    doc = nlp(texto.lower())
    return [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]

def gerar_indice_invertido(arquivos):
    indice = {}
    for arquivo in arquivos:
        with open(arquivo, 'r', encoding='utf-8') as f:
            texto = f.read()
        termos = preprocessar_texto(texto)
        for termo in termos:
            if termo not in indice:
                indice[termo] = {}
            if arquivo not in indice[termo]:
                indice[termo][arquivo] = 0
            indice[termo][arquivo] += 1
    return indice

def processar_consulta(consulta, indice, arquivos):
    def not_op(conjunto):
        return set(arquivos) - conjunto

    def and_op(conjunto1, conjunto2):
        return conjunto1 & conjunto2

    def or_op(conjunto1, conjunto2):
        return conjunto1 | conjunto2

    def avaliar_termo(termo):
        return set(indice.get(termo, {}).keys())

    termos = consulta.split()
    pilha = []
    for termo in termos:
        if termo == '&':
            op2, op1 = pilha.pop(), pilha.pop()
            pilha.append(and_op(op1, op2))
        elif termo == '|':
            while len(pilha) >= 3 and pilha[-2] == '&':
                op3, op2, op1 = pilha.pop(), pilha.pop(), pilha.pop()
                pilha.append(and_op(op1, op3))
            pilha.append(termo)
        elif termo.startswith('!'):
            pilha.append(not_op(avaliar_termo(nlp(termo[1:].lower())[0].lemma_)))
        else:
            pilha.append(avaliar_termo(nlp(termo.lower())[0].lemma_))

    while len(pilha) > 1:
        op2, op, op1 = pilha.pop(), pilha.pop(), pilha.pop()
        if op == '&':
            pilha.append(and_op(op1, op2))
        elif op == '|':
            pilha.append(or_op(op1, op2))

    return pilha[0]

def salvar_indice(indice):
    # Criar um mapeamento de nomes de arquivo para números
    arquivos_unicos = sorted(set(doc for termo in indice.values() for doc in termo.keys()))
    arquivo_para_numero = {arquivo: i+1 for i, arquivo in enumerate(arquivos_unicos)}

    with open('indice.txt', 'w', encoding='utf-8') as f:
        for termo in sorted(indice.keys()):
            # Criar uma lista de pares "documento,frequência" ordenada por número do documento
            doc_freq_pairs = sorted(
                [(arquivo_para_numero[doc], freq) for doc, freq in indice[termo].items()],
                key=lambda x: x[0]
            )
            # Formatar a linha de saída
            linha = f"{termo}: " + " ".join([f"{doc},{freq}" for doc, freq in doc_freq_pairs])
            f.write(linha + '\n')

def salvar_resposta(documentos):
    with open('resposta.txt', 'w', encoding='utf-8') as f:
        f.write(f"{len(documentos)}\n")
        for doc in sorted(documentos):
            f.write(f"{os.path.basename(doc)}\n")

def main(arquivo_base, arquivo_consulta):
    arquivos = ler_base(arquivo_base)
    consulta = ler_consulta(arquivo_consulta)

    indice = gerar_indice_invertido(arquivos)
    salvar_indice(indice)

    documentos = processar_consulta(consulta, indice, arquivos)
    salvar_resposta(documentos)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python modelo_booleano.py <arquivo_base> <arquivo_consulta>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])