import json
from pathlib import Path

path = Path(__file__).resolve().parent / "Config" / "sources.json"
sources = json.loads(path.read_text(encoding="utf-8"))

assert isinstance(sources, list) and sources, "sources.json debe ser una lista no vacía"
ids = [s["id"] for s in sources]
assert len(ids) == len(set(ids)), "Hay IDs de fuentes duplicados"

required = {
    "id", "name", "type", "url", "country", "active",
    "priority", "source_trust", "check_interval_minutes", "max_items",
}
for source in sources:
    missing = required - set(source)
    assert not missing, f"{source.get('id')}: faltan campos {sorted(missing)}"
    assert source["type"] in {"page", "html", "rss", "controlled_test"}
    assert 0 <= float(source["source_trust"]) <= 100
    assert int(source["check_interval_minutes"]) >= 1
    assert int(source["max_items"]) >= 1

assert not next(s for s in sources if s["id"] == "controlled-cloud-test")["active"]
assert not next(s for s in sources if s["id"] == "santander-beneficios")["active"]

active = [s for s in sources if s.get("active")]
assert len(active) >= 20, f"Se esperaban al menos 20 fuentes activas; hay {len(active)}"

print(f"SOURCES CONFIG OK - {len(active)} fuentes activas")
