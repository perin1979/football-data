import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd
import time

# =========================================
# ENTRADAS
# =========================================

ano = int(input(
    "Informe o ano do Brasileirão: "
).strip())

print("\nEscolha uma opção:")
print("1 - Qual time ficou mais rodadas na lanterna")
print("2 - Quantas rodadas um time ficou entre os rebaixados")
print("3 - Qual time ficou mais rodadas na liderança")
print("4 - Quantas rodadas um time ficou entre XX e YY")
print("5 - Em quais rodadas um time ficou na liderança")
print("6 - Em quais rodadas um time ficou na lanterna")
print("7 - Em quais rodadas um time ficou entre XX e YY")

opcao = input("\nDigite a opção desejada: ").strip()

# =========================================
# CONFIGURAÇÕES
# =========================================

saison_id = ano - 1

base_url = (
    "https://www.transfermarkt.co.uk/"
    "campeonato-brasileiro-serie-a/"
    "spieltagtabelle/"
    "wettbewerb/BRA1"
    "?saison_id={}&spieltag={}"
)

headers = {
    "User-Agent": "Mozilla/5.0"
}

# =========================================
# TOTAL DE RODADAS
# =========================================

def obter_total_rodadas(ano):

    if ano in [2003, 2004]:
        return 46

    elif ano == 2005:
        return 42

    else:
        return 38


# =========================================
# TAMANHO DA ZONA
# =========================================

def obter_tamanho_zona(ano):

    if ano == 2003:
        return 2

    else:
        return 4


total_rodadas = obter_total_rodadas(ano)

# =========================================
# COLETA DOS DADOS
# =========================================

dados_rodadas = []

print("\n====================================")
print("COLETANDO DADOS...")
print("====================================")

for rodada in range(1, total_rodadas + 1):

    url = base_url.format(saison_id, rodada)

    print(f"\nRodada {rodada}")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Erro na rodada {rodada}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    tabela = soup.find("table", class_="items")

    if not tabela:
        print("Tabela não encontrada")
        continue

    linhas = tabela.find("tbody").find_all("tr")

    for linha in linhas:

        cols = linha.find_all("td")

        if len(cols) < 4:
            continue

        try:

            posicao = cols[0].get_text(strip=True)
            posicao = posicao.replace(".", "")
            posicao = int(posicao)

            clube = cols[2].get_text(" ", strip=True)

            dados_rodadas.append({
                "Rodada": rodada,
                "Posicao": posicao,
                "Clube": clube
            })

        except:
            continue

    time.sleep(1)

# =========================================
# DATAFRAME
# =========================================

df = pd.DataFrame(dados_rodadas)

ultima_posicao = df["Posicao"].max()

# =========================================
# OPÇÃO 1
# =========================================

if opcao == "1":

    lanternas = df[
        df["Posicao"] == ultima_posicao
    ]

    ranking = (
        lanternas["Clube"]
        .value_counts()
        .reset_index()
    )

    ranking.columns = ["Clube", "Rodadas"]

    print("\n====================================")
    print("TIME COM MAIS RODADAS NA LANTERNA")
    print("====================================\n")

    for _, row in ranking.iterrows():

        print(
            f"{row['Clube']}: "
            f"{row['Rodadas']} rodadas"
        )

# =========================================
# OPÇÃO 2
# =========================================

elif opcao == "2":

    nome_time = input(
        "\nInforme o nome do time: "
    ).strip().lower()

    tamanho_zona = obter_tamanho_zona(ano)

    zona = df[
        df["Posicao"] >= (
            ultima_posicao
            - tamanho_zona
            + 1
        )
    ]

    resultado = zona[
        zona["Clube"]
        .str.lower()
        .str.contains(nome_time)
    ]

    total = len(resultado)

    print("\n====================================")
    print("TOTAL NA ZONA")
    print("====================================\n")

    print(
        f"{nome_time.title()}: "
        f"{total} rodadas"
    )

# =========================================
# OPÇÃO 3
# =========================================

elif opcao == "3":

    lideres = df[
        df["Posicao"] == 1
    ]

    ranking = (
        lideres["Clube"]
        .value_counts()
        .reset_index()
    )

    ranking.columns = ["Clube", "Rodadas"]

    print("\n====================================")
    print("TIME COM MAIS RODADAS NA LIDERANÇA")
    print("====================================\n")

    for _, row in ranking.iterrows():

        print(
            f"{row['Clube']}: "
            f"{row['Rodadas']} rodadas"
        )

# =========================================
# OPÇÃO 4
# =========================================

elif opcao == "4":

    nome_time = input(
        "\nInforme o nome do time: "
    ).strip().lower()

    intervalo = input(
        "Informe o intervalo de posições (ex: 1-4): "
    ).strip()

    pos_inicio, pos_fim = map(
        int,
        intervalo.split("-")
    )

    resultado = df[
        (
            df["Posicao"] >= pos_inicio
        )
        &
        (
            df["Posicao"] <= pos_fim
        )
        &
        (
            df["Clube"]
            .str.lower()
            .str.contains(nome_time)
        )
    ]

    total = len(resultado)

    print("\n====================================")
    print("TOTAL NO INTERVALO")
    print("====================================\n")

    print(
        f"{nome_time.title()}: "
        f"{total} rodadas "
        f"entre {pos_inicio}º e {pos_fim}º"
    )

# =========================================
# OPÇÃO 5
# =========================================

elif opcao == "5":

    nome_time = input(
        "\nInforme o nome do time: "
    ).strip().lower()

    resultado = df[
        (
            df["Posicao"] == 1
        )
        &
        (
            df["Clube"]
            .str.lower()
            .str.contains(nome_time)
        )
    ]

    rodadas = resultado["Rodada"].tolist()

    print("\n====================================")
    print("RODADAS NA LIDERANÇA")
    print("====================================\n")

    if rodadas:

        print(
            f"{nome_time.title()} "
            f"liderou nas rodadas:"
        )

        print(", ".join(map(str, rodadas)))

    else:

        print("Nenhuma rodada encontrada")

# =========================================
# OPÇÃO 6
# =========================================

elif opcao == "6":

    nome_time = input(
        "\nInforme o nome do time: "
    ).strip().lower()

    resultado = df[
        (
            df["Posicao"] == ultima_posicao
        )
        &
        (
            df["Clube"]
            .str.lower()
            .str.contains(nome_time)
        )
    ]

    rodadas = resultado["Rodada"].tolist()

    print("\n====================================")
    print("RODADAS NA LANTERNA")
    print("====================================\n")

    if rodadas:

        print(
            f"{nome_time.title()} "
            f"foi lanterna nas rodadas:"
        )

        print(", ".join(map(str, rodadas)))

    else:

        print("Nenhuma rodada encontrada")

# =========================================
# OPÇÃO 7
# =========================================

elif opcao == "7":

    nome_time = input(
        "\nInforme o nome do time: "
    ).strip().lower()

    intervalo = input(
        "Informe o intervalo de posições (ex: 5-10): "
    ).strip()

    pos_inicio, pos_fim = map(
        int,
        intervalo.split("-")
    )

    resultado = df[
        (
            df["Posicao"] >= pos_inicio
        )
        &
        (
            df["Posicao"] <= pos_fim
        )
        &
        (
            df["Clube"]
            .str.lower()
            .str.contains(nome_time)
        )
    ]

    rodadas = resultado["Rodada"].tolist()

    print("\n====================================")
    print("RODADAS NO INTERVALO")
    print("====================================\n")

    if rodadas:

        print(
            f"{nome_time.title()} "
            f"ficou entre "
            f"{pos_inicio}º e {pos_fim}º "
            f"nas rodadas:"
        )

        print(", ".join(map(str, rodadas)))

    else:

        print("Nenhuma rodada encontrada")

# =========================================
# EXPORTAÇÃO
# =========================================

arquivo_excel = (
    f"classificacao_completa_{ano}.xlsx"
)

with pd.ExcelWriter(arquivo_excel) as writer:

    df.to_excel(
        writer,
        sheet_name="Classificacao",
        index=False
    )

print("\n====================================")
print("PROCESSAMENTO FINALIZADO")
print("====================================")

print(f"\nArquivo gerado: {arquivo_excel}")
