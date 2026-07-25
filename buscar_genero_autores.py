"""
buscar_genero_autores.py — Script auxiliar para Goodreads Explorer

Busca el género de cada autor único en tu CSV usando la API de Wikidata
(propiedad P21 - sexo o género), y guarda el resultado en
locales/author_genders.json.

Categorías:
  - "H" = Hombre
  - "M" = Mujer
  - "O" = Otros (no-binario, colectivos, entidades, anónimos, etc.)

Uso:
    py buscar_genero_autores.py goodreads_library_export.csv

Requiere conexión a internet.
"""

import sys
import json
import re
import time
import os
import urllib.request
import urllib.parse
import pandas as pd

CACHE_PATH = os.path.join("locales", "author_genders.json")

# Overrides manuales — tienen PRIORIDAD sobre Wikidata
# H = Hombre, M = Mujer, O = Otros
MANUAL_OVERRIDES = {
    # Entidades / colectivos / anónimos → Otros
    "Bethesda Softworks": "O",
    "Anonymous": "O",
    "Various": "O",

    # Seudónimos colectivos masculinos
    "James S.A. Corey": "H",   # Daniel Abraham + Ty Franck

    # Aliases que se normalizan en la app — incluirlos por si acaso
    "Julio Verne": "H",
    "Juan Rousseau": "H",
    "Richard Bachman": "H",    # alias de Stephen King

    # Autores conocidos — evitamos depender de Wikidata
    "Akira Toriyama": "H",
    "Aldous Huxley": "H",
    "Andy Weir": "H",
    "Aristotle": "H",
    "Arthur C. Clarke": "H",
    "C.M. Kosemen": "H",
    "C.S. Lewis": "H",
    "Carlos Salvador Bilardo": "H",
    "Clifford D. Simak": "H",
    "Cormac McCarthy": "H",
    "David Grann": "H",
    "Franz Kafka": "H",
    "Fred Hoyle": "H",
    "Félix Luna": "H",
    "George Orwell": "H",
    "H.G. Wells": "H",
    "H.P. Lovecraft": "H",
    "Hajime Isayama": "H",
    "Herman Melville": "H",
    "Homer": "H",
    "Héctor Germán Oesterheld": "H",
    "Isaac Asimov": "H",
    "J.D. Vance": "H",
    "Jean-Jacques Rousseau": "H",
    "Jeff Vandermeer": "H",
    "Joe Haldeman": "H",
    "John Locke": "H",
    "Jorge Luis Borges": "H",
    "José Hernández": "H",
    "Jules Verne": "H",
    "Julio Cortázar": "H",
    "Junji Ito": "H",
    "Karl Marx": "H",
    "Koyoharu Gotouge": "M",
    "Liu Cixin": "H",
    "Manuel Puig": "H",
    "Mary Wollstonecraft Shelley": "M",
    "Matt Groening": "H",
    "Matthew Black": "H",
    "Miguel Ángel Palermo": "H",
    "Niccolò Machiavelli": "H",
    "Nicolás Schuff": "H",
    "Orson Scott Card": "H",
    "Oscar Wilde": "H",
    "Philip K. Dick": "H",
    "Plato": "H",
    "Ray Bradbury": "H",
    "Richard Bachman": "H",
    "Rifujin na Magonote": "H",
    "Robert A. Dahl": "H",
    "Roberto Arlt": "H",
    "Robin Moore": "H",
    "Roger Zelazny": "H",
    "Samuel P. Huntington": "H",
    "Stephen King": "H",
    "Sun Tzu": "H",
    "Thomas Hobbes": "H",
    "Thomas More": "H",
    "Tsugumi Ohba": "H",
    "Walter M. Miller Jr.": "H",
    "Will Guidara": "H",
    "William Gibson": "H",
    "A.G. Riddle": "H",
    "Tim Bowler": "H",
    "Logan Ryan Smith": "H",
    "Abraham Matthews": "H",
}

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"

# Wikidata Q-codes para géneros
MALE_IDS   = {"Q6581097", "Q2449503", "Q15145778"}   # masculino, transgénero masc., etc.
FEMALE_IDS = {"Q6581072", "Q1052281", "Q15145779"}   # femenino, transgénero fem., etc.

def normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()

def wikidata_gender(author: str) -> str | None:
    """Busca el género en Wikidata vía Wikipedia sitelink."""
    try:
        # 1. Buscar el Q-id del autor en Wikidata
        search_params = urllib.parse.urlencode({
            "action": "wbsearchentities", "search": author,
            "language": "en", "type": "item", "limit": 3, "format": "json",
        })
        with urllib.request.urlopen(f"{WIKIDATA_API}?{search_params}", timeout=8) as resp:
            data = json.load(resp)

        results = data.get("search", [])
        if not results:
            return None

        # Tomar el primer resultado que tenga descripción de persona/escritor
        qid = None
        for r in results:
            desc = r.get("description", "").lower()
            if any(w in desc for w in ["writer", "author", "novelist", "poet", "playwright",
                                        "philosopher", "historian", "journalist", "screenwriter"]):
                qid = r["id"]
                break
        if not qid:
            qid = results[0]["id"]

        # 2. Obtener la propiedad P21 (sexo o género)
        entity_params = urllib.parse.urlencode({
            "action": "wbgetentities", "ids": qid,
            "props": "claims", "format": "json",
        })
        with urllib.request.urlopen(f"{WIKIDATA_API}?{entity_params}", timeout=8) as resp:
            data = json.load(resp)

        claims = data.get("entities", {}).get(qid, {}).get("claims", {})
        p21 = claims.get("P21", [])
        if not p21:
            return None

        gender_qid = p21[0]["mainsnak"]["datavalue"]["value"]["id"]
        if gender_qid in MALE_IDS:
            return "H"
        elif gender_qid in FEMALE_IDS:
            return "M"
        else:
            return "O"

    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print("Uso: py buscar_genero_autores.py <archivo.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Exclusive Shelf"] == "read"]
    df["Author"] = df["Author"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    # Aplicar aliases igual que en la app
    ALIASES = {
        "Julio Verne": "Jules Verne",
        "Juan Rousseau": "Jean-Jacques Rousseau",
        "Richard Bachman": "Stephen King",
    }
    df["Author"] = df["Author"].replace(ALIASES)

    authors = sorted(df["Author"].dropna().unique())

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

        # Buscar en Wikidata
        gender = wikidata_gender(author)
        cache[author] = gender
        status = {"H": "Hombre", "M": "Mujer", "O": "Otros"}.get(gender, "NO ENCONTRADO — completar a mano")
        print(f"[wikidata] {author} -> {status}")
        new_lookups += 1
        time.sleep(0.4)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2, sort_keys=True)

    not_found = [a for a, g in cache.items() if g is None]
    print(f"\n✅ Guardado en {CACHE_PATH}")
    print(f"   {new_lookups} autores nuevos consultados.")
    if not_found:
        print(f"\n⚠️  {len(not_found)} autores sin género asignado:")
        for a in not_found:
            print(f"   - {a}")
        print("\n   Agregalos a MANUAL_OVERRIDES en este script")
        print("   o editá directamente locales/author_genders.json")
        print("   Valores: H = Hombre, M = Mujer, O = Otros")


if __name__ == "__main__":
    main()
