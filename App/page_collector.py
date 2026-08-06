from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from App.analyzer import OpportunityAnalyzer
from App.collector import BaseCollector
from App.models import Opportunity


class PageCollector(BaseCollector):
    """
    Examina los enlaces visibles de una página pública y conserva
    aquellos cuyo texto parece representar una oportunidad económica.
    """

    KEYWORDS = (
        "cashback",
        "devolución",
        "devolucion",
        "descuento",
        "promoción",
        "promocion",
        "beneficio",
        "bono",
        "cupón",
        "cupon",
        "gratis",
        "recompensa",
        "oferta",
        "ahorra",
        "tenpesos",
        "misión",
        "mision",
    )

    def __init__(
        self,
        source_id: str,
        source_name: str,
        url: str,
        country: str,
        category: str,
        source_trust: float = 60.0,
        max_items: int = 20,
    ) -> None:
        super().__init__(
            source_id=source_id,
            source_name=source_name,
            url=url,
            country=country,
            category=category,
        )

        self.source_trust = source_trust
        self.max_items = max_items
        self.analyzer = OpportunityAnalyzer()

    def collect(self) -> list[Opportunity]:
        response = requests.get(
            self.url,
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; OpportunityEngine/0.6)"
                )
            },
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        opportunities: list[Opportunity] = []
        processed_urls: set[str] = set()

        for link_element in soup.select("a[href]"):
            title = link_element.get_text(" ", strip=True)
            raw_link = link_element.get("href", "").strip()

            if not title or not raw_link:
                continue

            parent_text = link_element.parent.get_text(
                " ",
                strip=True,
            )

            searchable_text = (
                f"{title} {parent_text}"
            ).lower()

            if not any(
                keyword in searchable_text
                for keyword in self.KEYWORDS
            ):
                continue

            opportunity_url = urljoin(
                self.url,
                raw_link,
            )

            if opportunity_url in processed_urls:
                continue

            processed_urls.add(opportunity_url)

            analysis = self.analyzer.analyze(
                title=title,
                description=parent_text,
                source_trust=self.source_trust,
                country=self.country,
            )

            opportunities.append(
                Opportunity(
                    source_id=self.source_id,
                    source_name=self.source_name,
                    title=title,
                    url=opportunity_url,
                    country=self.country,
                    category=self.category,
                    description=parent_text,
                    currency=analysis.currency,
                    reward_amount=analysis.reward_amount,
                    required_cost=analysis.required_cost,
                    estimated_minutes=analysis.estimated_minutes,
                    probability=analysis.probability,
                    score=analysis.score,
                    requirements=analysis.requirements,
                    tags=analysis.tags,
                    raw_data={
                        "collector_type": "page",
                        "source_url": self.url,
                        "risk_level": analysis.risk_level,
                    },
                )
            )

            if len(opportunities) >= self.max_items:
                break

        return opportunities