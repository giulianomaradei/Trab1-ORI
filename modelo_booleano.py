import sys
import os
import spacy
import string

nlp = spacy.load("pt_core_news_lg")

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
    lemas = set()  # Usamos um conjunto para garantir unicidade
    for token in doc:
        if (not token.is_stop and ' ' not in token.lemma_ and not token.is_punct):
            lemas.add(token.lemma_.lower())  # Convertemos para minúsculas aqui
    return list(lemas)

def gerar_indice_invertido(arquivos):
    indice = {}
    for arquivo in arquivos:
        with open(arquivo, 'r', encoding='utf-8') as f:
            texto = f.read()
        termos = preprocessar_texto(texto)  # Já retorna uma lista de lemas únicos
        for termo in termos:
            if termo not in indice:
                indice[termo] = {}
            indice[termo][arquivo] = indice[termo].get(arquivo, 0) + 1
    return indice

def processar_consulta(consulta, indice, arquivos):
    def avaliar_termo(termo, negado=False):
        termo_processado = nlp(termo.lower())[0].lemma_.lower()  # Convertemos para minúsculas aqui
        resultado = set(indice.get(termo_processado, {}).keys())
        return set(arquivos) - resultado if negado else resultado

    termos = consulta.split()
    resultado = set(arquivos)
    operacao_atual = '&'

    for termo in termos:
        if termo in {'&', '|'}:
            operacao_atual = termo
        elif termo == '!':
            continue
        else:
            negado = termos[termos.index(termo) - 1] == '!' if termos.index(termo) > 0 else False
            termo_resultado = avaliar_termo(termo, negado)

            if operacao_atual == '&':
                resultado &= termo_resultado
            elif operacao_atual == '|':
                resultado |= termo_resultado

    return resultado

def salvar_indice(indice):
    arquivos_unicos = sorted(set(doc for termo in indice.values() for doc in termo.keys()))
    arquivo_para_numero = {arquivo: i+1 for i, arquivo in enumerate(arquivos_unicos)}

    with open('indice.txt', 'w', encoding='utf-8') as f:
        for termo in sorted(indice.keys(), key=lambda x: x.lower()):  # Ordenamos ignorando maiúsculas/minúsculas
            doc_freq_pairs = sorted(
                [(arquivo_para_numero[doc], freq) for doc, freq in indice[termo].items()],
                key=lambda x: x[0]
            )
            if doc_freq_pairs:
                linha = f"{termo.lower()}: " + " ".join([f"{doc},{freq}" for doc, freq in doc_freq_pairs])  # Salvamos o termo em minúsculas
                f.write(linha + '\n')
            else:
                print(f"Warning: Term '{termo}' has no associated documents and will be skipped.")

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