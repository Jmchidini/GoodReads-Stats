"""
buscar_paises_autores.py — Script auxiliar para Goodreads Explorer

Busca el país de nacimiento de cada autor único en tu CSV usando la API
de Wikipedia, y guarda el resultado en locales/author_countries.json.

Este archivo se usa después en goodreads_explorer.py para el mapa mundial
de autores. Corré este script UNA VEZ después de exportar un CSV nuevo,
o cuando tengas autores nuevos que no estén en el cache todavía.

Uso:
    python buscar_paises_autores.py goodreads_library_export.csv

Requiere conexión a internet (no funciona en sandboxes sin acceso a la web).
"""

import sys
import json
import re
import time
import os
import unicodedata
import urllib.request
import urllib.parse
import pandas as pd

CACHE_PATH = os.path.join("locales", "author_countries.json")

# Entidades que NO son personas — se excluyen automáticamente de la búsqueda
NOT_A_PERSON = {
    "anonymous", "various", "bethesda softworks",
}

# Diccionario de overrides manuales — tiene PRIORIDAD sobre lo que devuelva Wikipedia.
# Usalo para corregir errores de matching o completar autores que la API no encuentra.
# Formato: "Nombre exacto del autor": "Nombre del país"
MANUAL_OVERRIDES = {
    "Bethesda Softworks": None,          # estudio, no autor — sin país
    "Anonymous": None,
    "Various": None,
    "Jean-Jacques Rousseau": "Suiza",    # alias de Juan Rousseau
    "Julio Verne": "Francia",            # alias de Jules Verne
    "Jules Verne": "Francia",
    "Stephen King": "Estados Unidos",    # nombres con espacios dobles en el CSV original
    "Richard Bachman": "Estados Unidos",
    "Robin Moore": "Estados Unidos",
    "Matthew Black": "Estados Unidos",
    "Rifujin na Magonote": "Japón",
    "Tsugumi Ohba": "Japón",
    "Akira Toriyama": "Japón",
    "Koyoharu Gotouge": "Japón",
    "Hajime Isayama": "Japón",
    "Junji Ito": "Japón",
    "Carlos Salvador Bilardo": "Argentina",
    "Héctor Germán Oesterheld": "Argentina",
    "José Hernández": "Argentina",
    "Roberto Arlt": "Argentina",
    "Jorge Luis Borges": "Argentina",
    "Julio Cortázar": "Argentina",
    "Manuel Puig": "Argentina",
    "Félix Luna": "Argentina",
    "Miguel Ángel Palermo": "Argentina",
    "Nicolás Schuff": "Argentina",

    # Autores conocidos — evitamos depender de la heurística de Wikipedia
    "Aldous Huxley": "Reino Unido",
    "Andy Weir": "Estados Unidos",
    "Aristotle": "Grecia",
    "Arthur C. Clarke": "Reino Unido",
    "C.S. Lewis": "Reino Unido",
    "Clifford D. Simak": "Estados Unidos",
    "Cormac McCarthy": "Estados Unidos",
    "Franz Kafka": "República Checa",
    "Fred Hoyle": "Reino Unido",
    "George Orwell": "Reino Unido",
    "H.G. Wells": "Reino Unido",
    "H.P. Lovecraft": "Estados Unidos",
    "Herman Melville": "Estados Unidos",
    "Homer": "Grecia",
    "Isaac Asimov": "Estados Unidos",
    "Joe Haldeman": "Estados Unidos",
    "John Locke": "Reino Unido",
    "Karl Marx": "Alemania",
    "Liu Cixin": "China",
    "Mary Wollstonecraft Shelley": "Reino Unido",
    "Niccolò Machiavelli": "Italia",
    "Orson Scott Card": "Estados Unidos",
    "Philip K. Dick": "Estados Unidos",
    "Plato": "Grecia",
    "Ray Bradbury": "Estados Unidos",
    "Robert A. Dahl": "Estados Unidos",
    "Roger Zelazny": "Estados Unidos",
    "Samuel P. Huntington": "Estados Unidos",
    "Sun Tzu": "China",
    "Thomas Hobbes": "Reino Unido",
    "Thomas More": "Reino Unido",
    "Walter M. Miller Jr.": "Estados Unidos",
    "William Gibson": "Estados Unidos",
    "James S.A. Corey": "Estados Unidos",  # seudónimo (Abraham + Franck)
    "David Grann": "Estados Unidos",
    "J.D. Vance": "Estados Unidos",
    "Matt Groening": "Estados Unidos",
    "Adolfo Bioy Casares": "Argentina",
    "Horacio Quiroga": "Uruguay",
    "Casona A.": "España",       # Alejandro Casona
    "Gonzalez": "Argentina",
    "MARRADI": "Argentina",
    "Jeff Vandermeer": "Estados Unidos",
}

WIKI_API = "https://es.wikipedia.org/w/api.php"
WIKI_API_EN = "https://en.wikipedia.org/w/api.php"

# Frases típicas en el resumen de Wikipedia que preceden la nacionalidad
COUNTRY_PATTERNS = [
    r"escritor[a]?\s+([a-záéíóúñ]+)",
    r"naci[oó]\s+en\s+[\wÁÉÍÓÚáéíóúñÑ\s]+,\s*([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚáéíóúñÑ\s]+?)[\.\,]",
    r"\(([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚáéíóúñÑ\s]+?),\s*\d{3,4}",
]

def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()

def fetch_wikipedia_summary(author: str, lang_api: str) -> str | None:
    """Busca el artículo de Wikipedia para el autor y devuelve el extracto."""
    try:
        search_params = urllib.parse.urlencode({
            "action": "query", "list": "search", "srsearch": author,
            "format": "json", "srlimit": 1,
        })
        with urllib.request.urlopen(f"{lang_api}?{search_params}", timeout=8) as resp:
            data = json.load(resp)
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        page_title = results[0]["title"]

        extract_params = urllib.parse.urlencode({
            "action": "query", "prop": "extracts", "exintro": True,
            "explaintext": True, "titles": page_title, "format": "json",
        })
        with urllib.request.urlopen(f"{lang_api}?{extract_params}", timeout=8) as resp:
            data = json.load(resp)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            return page.get("extract", "")
    except Exception:
        return None
    return None


def guess_country(extract: str) -> str | None:
    """Heurística simple para extraer el país desde el texto del resumen."""
    if not extract:
        return None
    # Nacionalidades comunes -> país (extensible)
    NATIONALITY_MAP = {
        "estadounidense": "Estados Unidos", "american": "Estados Unidos",
        "británico": "Reino Unido", "británica": "Reino Unido", "british": "Reino Unido",
        "inglés": "Reino Unido", "inglesa": "Reino Unido", "english": "Reino Unido",
        "francés": "Francia", "francesa": "Francia", "french": "Francia",
        "japonés": "Japón", "japonesa": "Japón", "japanese": "Japón",
        "alemán": "Alemania", "alemana": "Alemania", "german": "Alemania",
        "ruso": "Rusia", "rusa": "Rusia", "russian": "Rusia",
        "chino": "China", "china": "China", "chinese": "China",
        "argentino": "Argentina", "argentina": "Argentina",
        "español": "España", "española": "España", "spanish": "España",
        "italiano": "Italia", "italiana": "Italia", "italian": "Italia",
        "griego": "Grecia", "griega": "Grecia", "greek": "Grecia",
        "canadiense": "Canadá", "canadian": "Canadá",
        "checo": "República Checa", "czech": "República Checa",
        "irlandés": "Irlanda", "irish": "Irlanda",
        "polaco": "Polonia", "polish": "Polonia",
    }
    lower = extract.lower()
    for word, country in NATIONALITY_MAP.items():
        if re.search(rf"\b{word}\b", lower):
            return country
    return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python buscar_paises_autores.py <archivo.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Exclusive Shelf"] == "read"]
    authors = sorted(set(normalize(a) for a in df["Author"].dropna().unique()))

    os.makedirs("locales", exist_ok=True)
    cache = {}
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            cache = json.load(f)

    print(f"Total autores únicos: {len(authors)}")
    new_lookups = 0

    for author in authors:
        # Overrides manuales tienen SIEMPRE prioridad, incluso sobre valores null en cache
        if author in MANUAL_OVERRIDES:
            if cache.get(author) != MANUAL_OVERRIDES[author]:
                cache[author] = MANUAL_OVERRIDES[author]
                print(f"[override] {author} -> {MANUAL_OVERRIDES[author]}")
            continue

        if author in cache and cache[author] is not None:
            continue  # ya tiene un valor válido en cache, no tocar

        # 2. Excluir entidades que no son personas
        if author.lower() in NOT_A_PERSON:
            cache[author] = None
            continue

        # 3. Buscar en Wikipedia (español primero, luego inglés)
        extract = fetch_wikipedia_summary(author, WIKI_API)
        country = guess_country(extract) if extract else None

        if country is None:
            extract = fetch_wikipedia_summary(author, WIKI_API_EN)
            country = guess_country(extract) if extract else None

        cache[author] = country
        status = country if country else "NO ENCONTRADO — completar a mano"
        print(f"[wiki] {author} -> {status}")
        new_lookups += 1
        time.sleep(0.3)  # no saturar la API

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2, sort_keys=True)

    not_found = [a for a, c in cache.items() if c is None and a not in MANUAL_OVERRIDES]
    print(f"\n✅ Guardado en {CACHE_PATH}")
    print(f"   {new_lookups} autores nuevos consultados.")
    if not_found:
        print(f"\n⚠️  {len(not_found)} autores sin país asignado:")
        for a in not_found:
            print(f"   - {a}")
        print("\n   Agregalos a MANUAL_OVERRIDES en este script y volvé a correrlo,")
        print("   o editá directamente el archivo locales/author_countries.json")


if __name__ == "__main__":
    main()
