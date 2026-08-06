from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from App.analyzer import OpportunityAnalyzer
from App.collector import BaseCollector
from App.models import Opportunity


class HTMLCollector(BaseCollector):
    """
    Recolector genérico de páginas HTML públicas.

    Los selectores CSS se configuran desde sources.json,
    permitiendo incorporar páginas nuevas sin modificar este archivo.
    """

    def __init__(
        self,
        source_id: str,
        source_name: str,
        url: str,
        country: str,
        category: str,
        item_selector: str,
        title_selector: str,
        link_selector: str,
        description_selector: str | None = None,
        source_trust: float = 60.0,
        max_items: int = 10,
    ) -> None:
        super().__init__(
            source_id=source_id,
            source_name=source_name,
            url=url,
            country=country,
            category=category,
        )

        self.item_selector = item_selector
        self.title_selector = title_selector
        self.link_selector = link_selector
        self.description_selector = description_selector
        self.source_trust = source_trust
        self.max_items = max_items
        self.analyzer = OpportunityAnalyzer()

    def collect(self) -> list[Opportunity]:
        response = requests.get(
            self.url,
            timeout=25,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 OpportunityEngine/0.6 "
                    "(public promotion monitor)"
                )
            },
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select(self.item_selector)

        opportunities: list[Opportunity] = []

        for item in items[: self.max_items]:
            title_element = item.select_one(self.title_selector)
            link_element = item.select_one(self.link_selector)

            if title_element is None or link_element is None:
                continue

            title = title_element.get_text(
                " ",
                strip=True,
            )

            raw_link = link_element.get("href", "").strip()
            url = urljoin(self.url, raw_link)

            if not title or not raw_link:
                continue

            description = ""

            if self.description_selector:
                description_element = item.select_one(
                    self.description_selector
                )

                if description_element is not None:
                    description = description_element.get_text(
                        " ",
                        strip=True,
                    )

            analysis = self.analyzer.analyze(
                title=title,
                description=description,
                source_trust=self.source_trust,
                country=self.country,
            )

            opportunity = Opportunity(
                source_id=self.source_id,
                source_name=self.source_name,
                title=title,
                url=url,
                country=self.country,
                category=self.category,
                description=description,
                currency=analysis.currency,
                reward_amount=analysis.reward_amount,
                required_cost=analysis.required_cost,
                estimated_minutes=analysis.estimated_minutes,
                probability=analysis.probability,
                score=analysis.score,
                requirements=analysis.requirements,
                tags=analysis.tags,
                raw_data={
                    "collector_type": "html",
                    "source_url": self.url,
                    "risk_level": analysis.risk_level,
                },
            )

            opportunities.append(opportunity)

        return opportunities