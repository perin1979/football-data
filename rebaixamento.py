import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd
import time

# =========================================
# INFORMAÇÕES IMPORTANTES
# =========================================

print("\n====================================")
print("INFORMAÇÕES DAS TEMPORADAS")
print("====================================")

print("\nQuantidade de rodadas:")
print("- 2003 e 2004: 46 rodadas")
print("- 2005: 42 rodadas")
print("- 2006 em diante: 38 rodadas")

print("\nZona de rebaixamento:")
print("- 2003: 2 rebaixados")
print("- 2004 em diante: 4 rebaixados")

print("\n====================================")

# =========================================
# ENTRADA DOS ANOS
# =========================================

entrada_anos = input(
    "\nInforme um ano ou intervalo "
    "(ex: 2026 ou 2003-2020): "
).strip()

# Caso seja apenas um ano
if "-" not in entrada_anos:

    ano_inicial = int(entrada_anos)
    ano_final = int(entrada_anos)

# Caso seja intervalo
else:

    ano_inicial, ano_final = map(
        int,
        entrada_anos.split("-")
    )

anos = list(range(ano_inicial, ano_final + 1))

# =========================================
# ENTRADA DAS RODADAS
# =========================================

entrada_rodadas = input(
    "\nInforme uma rodada ou intervalo "
    "(ex: 10 ou 1-20): "
).strip()

# Apenas uma rodada
if "-" not in entrada_rodadas:

    rodada_inicial = int(entrada_rodadas)
    rodada_final = int(entrada_rodadas)

# Intervalo de rodadas
else:

    rodada_inicial, rodada_final = map(
        int,
        entrada_rodadas.split("-")
    )

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
# FUNÇÕES AUXILIARES
# =========================================

def obter_total_rodadas(ano):

    # 2003 e 2004
    if ano in [2003, 2004]:
        return 46

    # 2005
    elif ano == 2005:
        return 42

    # 2006+
    else:
        return 38


def obter_tamanho_zona(ano):

    # Em 2003 caíam apenas 2 clubes
    if ano == 2003:
        return 2

    # Demais anos: 4 clubes
    else:
        return 4


# =========================================
# DATAFRAMES FINAIS
# =========================================

todas_rodadas = []
todos_ranking = []

# =========================================
# LOOP DOS ANOS
# =========================================

for ano in anos:

    print("\n====================================")
    print(f"PROCESSANDO ANO {ano}")
    print("====================================")

    saison_id = ano - 1

    total_rodadas = obter_total_rodadas(ano)

    tamanho_zona = obter_tamanho_zona(ano)

    print(f"saison_id: {saison_id}")
    print(f"Total de rodadas: {total_rodadas}")
    print(f"Tamanho da zona: {tamanho_zona}")

    contagem_zona = defaultdict(int)

    # =========================================
    # AJUSTA LIMITE DE RODADAS
    # =========================================

    rodada_inicio_real = max(1, rodada_inicial)

    rodada_final_real = min(
        rodada_final,
        total_rodadas
    )

    # =========================================
    # LOOP DAS RODADAS
    # =========================================

    for rodada in range(
        rodada_inicio_real,
        rodada_final_real + 1
    ):

        url = base_url.format(
            saison_id,
            rodada
        )

        print(f"\nRodada {rodada}")
        print(url)

        response = requests.get(
            url,
            headers=headers
        )

        if response.status_code != 200:

            print(
                f"Erro ao acessar rodada {rodada}"
            )

            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        tabela = soup.find(
            "table",
            class_="items"
        )

        if not tabela:

            print("Tabela não encontrada")

            continue

        linhas = tabela.find(
            "tbody"
        ).find_all("tr")

        classificacao = []

        for linha in linhas:

            cols = linha.find_all("td")

            if len(cols) < 4:
                continue

            try:

                posicao = cols[0].get_text(
                    strip=True
                )

                posicao = posicao.replace(".", "")

                posicao = int(posicao)

                clube = cols[2].get_text(
                    " ",
                    strip=True
                )

                classificacao.append(
                    (posicao, clube)
                )

            except:
                continue

        classificacao.sort(
            key=lambda x: x[0]
        )

        # Últimos colocados da zona
        zona = classificacao[-tamanho_zona:]

        zona_times = [
            x[1] for x in zona
        ]

        # =========================================
        # SALVA RODADA
        # =========================================

        todas_rodadas.append({
            "Ano": ano,
            "Rodada": rodada,
            "Zona de Rebaixamento":
                ", ".join(zona_times)
        })

        # =========================================
        # SOMA PRESENÇA NA ZONA
        # =========================================

        for clube in zona_times:

            contagem_zona[clube] += 1

        print(f"Zona: {zona_times}")

        time.sleep(1)

    # =========================================
    # RANKING FINAL DO ANO
    # =========================================

    ranking = sorted(
        contagem_zona.items(),
        key=lambda x: x[1],
        reverse=True
    )

    print("\n===== TOTAL NA ZONA =====")

    for clube, total in ranking:

        print(f"{clube}: {total}")

        todos_ranking.append({
            "Ano": ano,
            "Clube": clube,
            "Rodadas na Zona": total
        })

# =========================================
# DATAFRAMES
# =========================================

rodadas_df = pd.DataFrame(
    todas_rodadas
)

ranking_df = pd.DataFrame(
    todos_ranking
)

# =========================================
# TOTAL GERAL
# =========================================

total_geral_df = (
    ranking_df
    .groupby("Clube")["Rodadas na Zona"]
    .sum()
    .reset_index()
)

total_geral_df = total_geral_df.sort_values(
    by="Rodadas na Zona",
    ascending=False
)

# =========================================
# EXPORTAÇÃO PARA EXCEL
# =========================================

arquivo_excel = (
    f"zona_rebaixamento_"
    f"{ano_inicial}_a_{ano_final}_"
    f"rodadas_"
    f"{rodada_inicial}_a_{rodada_final}.xlsx"
)

with pd.ExcelWriter(
    arquivo_excel
) as writer:

    rodadas_df.to_excel(
        writer,
        sheet_name="Zona por Rodada",
        index=False
    )

    ranking_df.to_excel(
        writer,
        sheet_name="Total na Zona",
        index=False
    )

    total_geral_df.to_excel(
        writer,
        sheet_name="Total Geral",
        index=False
    )

print("\n====================================")
print("PROCESSAMENTO FINALIZADO")
print("====================================")

print(f"\nArquivo gerado: {arquivo_excel}")
