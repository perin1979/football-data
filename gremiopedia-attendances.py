import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
import time

BASE_URL = "https://gremiopedia.com"
START_URL = "https://gremiopedia.com/wiki/Jogos_do_Gr%C3%AAmio_em_2025"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def get_internal_links(url):
    """
    Extract internal wiki links from a page
    """
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Only wiki pages
        if href.startswith("/wiki/"):

            # Ignore anchors, files, categories etc
            if any(x in href for x in [
                "Especial:",
                "Arquivo:",
                "Categoria:",
                "#"
            ]):
                continue

            full_url = urljoin(BASE_URL, href)
            links.add(full_url)

    return links


def find_arena_matches(url):
    """
    Search tables recursively and extract
    Ficha Técnica links where sixth column (Local)
    = Arena do Grêmio
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

            if local != "Arena do Grêmio":
                continue

            # Search "Ficha Técnica" link in row
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
    Extract data from each Ficha Técnica page
    """
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n")

    # ---------------- DATE ----------------
    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    date = date_match.group(1) if date_match else ""

    # ---------------- MATCH ----------------
    title = soup.find("h1")
    jogo = ""

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
        r'Campeonato Gaúcho',
        r'Campeonato Brasileiro',
        r'Brasileirão',
        r'Copa do Brasil',
        r'Copa Sul-Americana',
        r'Libertadores',
        r'Recopa',
        r'Recopa Gaúcha'
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

    return {
        "Data": date,
        "Jogo": jogo,
        "Competição": competition,
        "Público Total": publico_total,
        "Público Pagantes": publico_pagante,
        "Renda": renda,
        "URL": url
    }


def crawl_all_pages(start_url):
    """
    Recursively navigate all wiki pages
    and collect Arena do Grêmio matches
    """
    visited = set()
    to_visit = {start_url}

    ficha_links = set()

    while to_visit:
        current_url = to_visit.pop()

        if current_url in visited:
            continue

        visited.add(current_url)

        print(f"Visiting: {current_url}")

        try:
            # Find Arena matches in current page
            matches = find_arena_matches(current_url)

            for m in matches:
                ficha_links.add(m)

            # Get more internal links
            internal_links = get_internal_links(current_url)

            for link in internal_links:
                if link not in visited:
                    to_visit.add(link)

            time.sleep(0.5)

        except Exception as e:
            print(f"Error visiting {current_url}: {e}")

    return sorted(ficha_links)


def main():

    print("Starting recursive crawl...\n")

    ficha_links = crawl_all_pages(START_URL)

    print(f"\nFound {len(ficha_links)} Arena do Grêmio matches\n")

    all_data = []

    for i, link in enumerate(ficha_links, start=1):

        try:
            print(f"[{i}/{len(ficha_links)}] Extracting: {link}")

            data = extract_match_data(link)

            all_data.append(data)

            time.sleep(1)

        except Exception as e:
            print(f"Error extracting {link}: {e}")

    # Create dataframe
    df = pd.DataFrame(all_data)

    # Remove duplicates
    df = df.drop_duplicates()

    # Sort by date if possible
    try:
        df["Data_dt"] = pd.to_datetime(
            df["Data"],
            format="%d/%m/%Y"
        )

        df = df.sort_values("Data_dt")

        df = df.drop(columns=["Data_dt"])

    except:
        pass

    # Save CSV
    df.to_csv(
        "gremio_arena_recursive.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nDONE!")
    print(df)

    print("\nCSV saved as:")
    print("gremio_arena_recursive.csv")


if __name__ == "__main__":
    main()
