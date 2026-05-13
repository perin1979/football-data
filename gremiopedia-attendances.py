import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
import time

BASE_URL = "https://gremiopedia.com"
SEASONS_URL = "https://gremiopedia.com/wiki/Temporadas"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# Allowed stadiums
VALID_STADIUMS = [
    "Arena do Grêmio",
    "Estádio Olímpico",
    "Estádio Olímpico Monumental",
    "Estádio da Baixada"
]


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def get_season_page(year):
    """
    Find the season page URL for the informed year
    from:
    https://gremiopedia.com/wiki/Temporadas
    """

    print(f"\nSearching season page for {year}...")

    response = requests.get(SEASONS_URL, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):

        text = clean_text(a.get_text())

        # Match exact year
        if text == str(year):

            href = a["href"]

            if href.startswith("/wiki/"):
                full_url = urljoin(BASE_URL, href)

                print(f"Season page found:")
                print(full_url)

                return full_url

    return None


def find_match_links(url):
    """
    Extract all Ficha Técnica links
    where Local is one of allowed stadiums
    """

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    tables = soup.find_all("table")

    for table in tables:

        rows = table.find_all("tr")

        if len(rows) < 2:
            continue

        for row in rows[1:]:

            cols = row.find_all(["td", "th"])

            # Must have at least 6 columns
            if len(cols) < 6:
                continue

            # Sixth column = Local
            local = clean_text(cols[5].get_text())

            if local not in VALID_STADIUMS:
                continue

            # Search Ficha Técnica link
            ficha_link = None

            for a in row.find_all("a", href=True):

                if "Ficha Técnica" in a.get_text():

                    ficha_link = urljoin(BASE_URL, a["href"])
                    break

            if ficha_link:
                results.append(ficha_link)

    return results


def extract_match_data(url):
    """
    Extract match data from Ficha Técnica page
    """

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n")

    # ---------------- DATE ----------------
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    date = date_match.group(1) if date_match else ""

    # ---------------- MATCH ----------------
    jogo = ""

    title = soup.find("h1")

    if title:

        jogo = title.get_text()

        jogo = jogo.replace("Ficha Técnica:", "")

        jogo = re.sub(
            r'\s*-\s*\d{2}/\d{2}/\d{4}',
            '',
            jogo
        )

        jogo = jogo.replace(" x ", "x").strip()

    # ---------------- COMPETITION ----------------
    competition = ""

    competition_patterns = [
        "Campeonato Gaúcho",
        "Campeonato Brasileiro",
        "Brasileirão",
        "Copa do Brasil",
        "Copa Libertadores",
        "Libertadores",
        "Copa Sul-Americana",
        "Recopa",
        "Recopa Gaúcha"
    ]

    for pattern in competition_patterns:

        if re.search(pattern, text, re.IGNORECASE):

            competition = pattern
            break

    # ---------------- ATTENDANCE ----------------
    publico_total = ""
    publico_pagante = ""
    renda = ""

    total_match = re.search(
        r'Público total[:\s]*([\d\.]+)',
        text,
        re.IGNORECASE
    )

    if total_match:
        publico_total = total_match.group(1)

    pagante_match = re.search(
        r'Público pagante[:\s]*([\d\.]+)',
        text,
        re.IGNORECASE
    )

    if pagante_match:
        publico_pagante = pagante_match.group(1)

    renda_match = re.search(
        r'Renda[:\s]*(R\$\s*[\d\.\,]+)',
        text,
        re.IGNORECASE
    )

    if renda_match:
        renda = renda_match.group(1)

    # ---------------- STADIUM ----------------
    estadio = ""

    for stadium in VALID_STADIUMS:

        if stadium in text:
            estadio = stadium
            break

    return {
        "Data": date,
        "Jogo": jogo,
        "Competição": competition,
        "Estádio": estadio,
        "Público Total": publico_total,
        "Público Pagantes": publico_pagante,
        "Renda": renda,
        "URL": url
    }


def main():

    # ---------------- INPUT YEAR ----------------
    year = input("Enter desired year: ").strip()

    if not year.isdigit():

        print("Invalid year.")
        return

    # ---------------- FIND SEASON PAGE ----------------
    season_url = get_season_page(year)

    if not season_url:

        print(f"Season page for {year} not found.")
        return

    # ---------------- FIND MATCH LINKS ----------------
    print("\nSearching matches...\n")

    ficha_links = find_match_links(season_url)

    ficha_links = list(set(ficha_links))

    print(f"Found {len(ficha_links)} matches.\n")

    # ---------------- EXTRACT DATA ----------------
    all_data = []

    for i, link in enumerate(ficha_links, start=1):

        try:

            print(f"[{i}/{len(ficha_links)}] Extracting:")
            print(link)

            data = extract_match_data(link)

            all_data.append(data)

            time.sleep(1)

        except Exception as e:

            print(f"Error extracting {link}")
            print(e)

    # ---------------- DATAFRAME ----------------
    df = pd.DataFrame(all_data)

    # Sort by date
    try:

        df["Data_dt"] = pd.to_datetime(
            df["Data"],
            format="%d/%m/%Y"
        )

        df = df.sort_values("Data_dt")

        df = df.drop(columns=["Data_dt"])

    except:
        pass

    # ---------------- SAVE CSV ----------------
    output_file = f"gremio_publico_{year}.csv"

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    # ---------------- RESULT ----------------
    print("\nDONE!")
    print(df)

    print(f"\nCSV saved as: {output_file}")


if __name__ == "__main__":
    main()
