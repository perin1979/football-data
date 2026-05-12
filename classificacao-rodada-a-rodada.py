import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# =========================================
# ENTRADAS DO USUÁRIO
# =========================================

nome_time = input(
    "Informe o nome do time: "
).strip().lower()

ano = int(input(
    "Informe o ano do Brasileirão: "
).strip())

intervalo = input(
    "Informe o intervalo de rodadas (ex: 1-10): "
).strip()

inicio, fim = map(int, intervalo.split("-"))

# =========================================
# CALCULA SAISON_ID
# =========================================

saison_id = ano - 1

print(f"\nAno informado: {ano}")
print(f"saison_id calculado: {saison_id}")

# =========================================
# CONFIGURAÇÕES
# =========================================

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
# RESULTADOS
# =========================================

historico = []

# =========================================
# LOOP DAS RODADAS
# =========================================

for rodada in range(inicio, fim + 1):

    url = base_url.format(saison_id, rodada)

    print(f"\nColetando rodada {rodada}...")
    print(url)

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Erro ao acessar rodada {rodada}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    tabela = soup.find("table", class_="items")

    if not tabela:
        print(f"Tabela não encontrada na rodada {rodada}")
        continue

    linhas = tabela.find("tbody").find_all("tr")

    encontrado = False

    for linha in linhas:

        cols = linha.find_all("td")

        if len(cols) < 4:
            continue

        try:

            posicao = cols[0].get_text(strip=True)
            posicao = posicao.replace(".", "")
            posicao = int(posicao)

            clube = cols[2].get_text(" ", strip=True)

            # comparação sem case sensitive
            if nome_time in clube.lower():

                encontrado = True

                historico.append({
                    "Rodada": rodada,
                    "Posição": posicao,
                    "Clube": clube
                })

                print(
                    f"Rodada {rodada}: "
                    f"{posicao}º colocado"
                )

                break

        except:
            continue

    if not encontrado:

        print(
            f"Time não encontrado na rodada {rodada}"
        )

    time.sleep(1)

# =========================================
# RESULTADO FINAL
# =========================================

print("\n====================================")
print("CLASSIFICAÇÃO POR RODADA")
print("====================================\n")

for item in historico:

    print(
        f"Rodada {item['Rodada']}: "
        f"{item['Posição']}º colocado"
    )

# =========================================
# EXPORTAÇÃO PARA EXCEL
# =========================================

df = pd.DataFrame(historico)

arquivo_excel = (
    f"classificacao_"
    f"{nome_time.replace(' ', '_')}_"
    f"{ano}_"
    f"rodadas_{inicio}_{fim}.xlsx"
)

with pd.ExcelWriter(arquivo_excel) as writer:

    df.to_excel(
        writer,
        sheet_name="Classificação",
        index=False
    )

print("\n====================================")
print("PROCESSAMENTO FINALIZADO")
print("====================================")

print(f"\nArquivo gerado: {arquivo_excel}")