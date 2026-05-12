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
# TAMANHO DO Z4
# =========================================

def obter_tamanho_zona(ano):

    if ano == 2003:
        return 2

    else:
        return 4


total_rodadas = obter_total_rodadas(ano)

# =========================================
# COLETA TODAS AS CLASSIFICAÇÕES
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

# =========================================
# OPÇÃO 1
# MAIS RODADAS NA LANTERNA
# =========================================

if opcao == "1":

    ultima_posicao = df["Posicao"].max()

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
# RODADAS ENTRE REBAIXADOS
# =========================================

elif opcao == "2":

    nome_time = input(
        "\nInforme o nome do time: "
    ).strip().lower()

    tamanho_zona = obter_tamanho_zona(ano)

    zona = df[
        df["Posicao"] >= (
            df["Posicao"].max()
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
    print("TOTAL NA ZONA DE REBAIXAMENTO")
    print("====================================\n")

    print(
        f"{nome_time.title()}: "
        f"{total} rodadas"
    )

# =========================================
# OPÇÃO 3
# MAIS RODADAS NA LIDERANÇA
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
# RODADAS ENTRE XX E YY
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
# EXPORTAÇÃO EXCEL
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
