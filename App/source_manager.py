import json
from pathlib import Path

from App.page_collector import PageCollector
from App.collector import BaseCollector
from App.html_collector import HTMLCollector
from App.rss_collector import RSSCollector


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_PATH = BASE_DIR / "Config" / "sources.json"


class SourceManager:
    """
    Carga las fuentes configuradas y construye
    el colector adecuado para cada una.
    """

    def __init__(
        self,
        sources_path: Path = SOURCES_PATH,
    ) -> None:
        self.sources_path = sources_path

    def load_active_collectors(
        self,
    ) -> list[BaseCollector]:

        sources = self._load_sources()
        collectors: list[BaseCollector] = []

        for source in sources:
            if not source.get("active", False):
                continue

            collector = self._build_collector(source)

            if collector is not None:
                collectors.append(collector)

        return collectors

    def _load_sources(self) -> list[dict]:
        if not self.sources_path.exists():
            raise FileNotFoundError(
                f"No existe el archivo: "
                f"{self.sources_path}"
            )

        with self.sources_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "sources.json debe contener una lista."
            )

        return data

    @staticmethod
    def _build_collector(
        source: dict,
    ) -> BaseCollector | None:

        source_type = source.get(
            "type",
            "",
        ).lower()

        if source_type == "rss":
            return RSSCollector(
                source_id=source["id"],
                source_name=source["name"],
                url=source["url"],
                country=source.get(
                    "country",
                    "INT",
                ),
                category=source.get(
                    "category",
                    "general",
                ),
                default_score=float(
                    source.get(
                        "default_score",
                        50,
                    )
                ),
                default_probability=float(
                    source.get(
                        "default_probability",
                        50,
                    )
                ),
                max_items=int(
                    source.get(
                        "max_items",
                        10,
                    )
                ),
            )
        if source_type == "html":
            selectors = source.get("selectors", {})

            return HTMLCollector(
                source_id=source["id"],
                source_name=source["name"],
                url=source["url"],
                country=source.get("country", "INT"),
                category=source.get(
                    "category",
                    "general",
                ),
                item_selector=selectors["item"],
                title_selector=selectors["title"],
                link_selector=selectors["link"],
                description_selector=selectors.get(
                    "description"
                ),
                source_trust=float(
                    source.get("source_trust", 60)
                ),
                max_items=int(
                    source.get("max_items", 10)
                ),
            )            
        if source_type == "page":
            return PageCollector(
                source_id=source["id"],
                source_name=source["name"],
                url=source["url"],
                country=source.get("country", "INT"),
                category=source.get(
                    "category",
                    "general",
                ),
                source_trust=float(
                    source.get("source_trust", 60)
                ),
                max_items=int(
                    source.get("max_items", 20)
                ),
            )
        print(
            "Tipo de fuente no compatible: "
            f"{source_type}"
        )

        return None