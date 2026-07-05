"""
sincronizar_locales.py — Script auxiliar para Goodreads Explorer

Toma es.json como fuente de verdad y sincroniza todos los demás archivos
de idioma en la carpeta locales/, agregando las claves faltantes con un
placeholder "[TRADUCIR]: valor en español" para que sean fáciles de encontrar.

También detecta claves que existen en otros idiomas pero ya no están en es.json
y las reporta como obsoletas (no las borra automáticamente por seguridad).

Uso:
    python sincronizar_locales.py
"""

import json
import os
import sys

LOCALES_DIR = os.path.join(os.getcwd(), "locales")
if not os.path.exists(LOCALES_DIR):
    # Fallback: buscar relativo al script
    LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
SOURCE_LANG = "es"
PLACEHOLDER_PREFIX = "[TRADUCIR]"

def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Guardado: {os.path.basename(path)}")

def sync():
    source_path = os.path.join(LOCALES_DIR, f"{SOURCE_LANG}.json")
    if not os.path.exists(source_path):
        print(f"❌ No se encontró el archivo fuente: {source_path}")
        sys.exit(1)

    source = load_json(source_path)
    source_keys = set(source.keys())

    # Buscar todos los demás archivos .json en locales/ (excepto el source y author_countries)
    targets = [
        f for f in os.listdir(LOCALES_DIR)
        if f.endswith(".json")
        and f != f"{SOURCE_LANG}.json"
        and f != "author_countries.json"
    ]

    if not targets:
        print("No se encontraron otros archivos de idioma para sincronizar.")
        return

    for filename in sorted(targets):
        lang = filename.replace(".json", "")
        path = os.path.join(LOCALES_DIR, filename)
        target = load_json(path)
        target_keys = set(target.keys())

        missing = source_keys - target_keys
        obsolete = target_keys - source_keys

        print(f"\n🌐 {filename}:")

        if not missing and not obsolete:
            print("  ✓ Sincronizado, no hay diferencias.")
            continue

        # Agregar claves faltantes con placeholder
        if missing:
            print(f"  ➕ {len(missing)} clave(s) faltante(s) — agregadas con placeholder:")
            for key in sorted(missing):
                value = source[key]
                if isinstance(value, list):
                    target[key] = [f"{PLACEHOLDER_PREFIX}: {v}" for v in value]
                else:
                    target[key] = f"{PLACEHOLDER_PREFIX}: {value}"
                print(f"     - {key}")

        # Reportar claves obsoletas (sin borrar)
        if obsolete:
            print(f"  ⚠️  {len(obsolete)} clave(s) obsoleta(s) (están en {filename} pero no en {SOURCE_LANG}.json):")
            for key in sorted(obsolete):
                print(f"     - {key}  (valor actual: {repr(target[key])})")
            print(f"     → Revisalas y borralas a mano si ya no se usan.")

        # Guardar manteniendo el orden del source para consistencia
        ordered = {k: target[k] for k in source_keys if k in target}
        # Agregar las obsoletas al final para no perderlas
        for k in sorted(obsolete):
            ordered[k] = target[k]

        save_json(path, ordered)

    print("\n✅ Sincronización completada.")
    print("   Buscá las claves marcadas con '[TRADUCIR]' en los archivos de idioma y completalas.")

if __name__ == "__main__":
    sync()
