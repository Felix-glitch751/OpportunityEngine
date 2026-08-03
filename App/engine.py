import json
from pathlib import Path

SETTINGS = Path("Config/settings.json")
SOURCES = Path("Config/sources.json")

def load_settings():
    with open(SETTINGS, "r", encoding="utf-8") as f:
        return json.load(f)

def load_sources():
    with open(SOURCES, "r", encoding="utf-8") as f:
        return json.load(f)

def run():
    settings = load_settings()
    sources = load_sources()

    print("Opportunity Engine v0.4")
    print(f"Umbral: {settings['notification_threshold']}%")
    print(f"Intervalo: {settings['scan_interval_minutes']} minutos")
    print()
    print("Fuentes activas:")

    for source in sources:
        if source["active"]:
            print(f"- {source['name']}")