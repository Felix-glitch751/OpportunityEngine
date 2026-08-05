from datetime import datetime
from html import unescape
from typing import Any

import feedparser

from App.analyzer import OpportunityAnalyzer
from App.collector import BaseCollector
from App.models import Opportunity


class RSSCollector(BaseCollector):
    """
    Lee una fuente RSS o Atom y transforma sus publicaciones
    en objetos Opportunity.
    """

    def __init__(
        self,
        source_id: str,
        source_name: str,
        url: str,
        country: str,
        category: str,
        default_score: float = 50.0,
        default_probability: float = 50.0,
        max_items: int = 10,
    ) -> None:
        super().__init__(
            source_id=source_id,
            source_name=source_name,
            url=url,
            country=country,
            category=category,
        )

        self.default_score = default_score
        self.default_probability = default_probability
        self.max_items = max_items
        self.analyzer = OpportunityAnalyzer()

    def collect(self) -> list[Opportunity]:
        feed = feedparser.parse(self.url)

        if feed.bozo and not feed.entries:
            raise RuntimeError(
                f"No fue posible leer la fuente RSS: "
                f"{self.source_name}"
            )

        opportunities: list[Opportunity] = []

        for entry in feed.entries[: self.max_items]:
            title = self._clean_text(
                entry.get("title", "")
            )

            url = entry.get("link", "").strip()

            description = self._clean_text(
                entry.get(
                    "summary",
                    entry.get("description", ""),
                )
            )

            if not title or not url:
                continue

            published_at = self._extract_published_at(entry)

            analysis = self.analyzer.analyze(
                title=title,
                description=description,
                source_trust=self.default_probability,
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
                published_at=published_at,
                raw_data={
                    "collector_type": "rss",
                    "feed_url": self.url,
                    "risk_level": analysis.risk_level,
                },
            )

            opportunities.append(opportunity)

        return opportunities

    @staticmethod
    def _clean_text(value: Any) -> str:
        if not value:
            return ""

        text = str(value)
        text = unescape(text)

        inside_tag = False
        result: list[str] = []

        for character in text:
            if character == "<":
                inside_tag = True
                continue

            if character == ">":
                inside_tag = False
                continue

            if not inside_tag:
                result.append(character)

        return " ".join(
            "".join(result).split()
        )

    @staticmethod
    def _extract_published_at(
        entry: Any,
    ) -> str | None:
        parsed_time = entry.get(
            "published_parsed",
            entry.get("updated_parsed"),
        )

        if not parsed_time:
            return None

        return datetime(
            year=parsed_time.tm_year,
            month=parsed_time.tm_mon,
            day=parsed_time.tm_mday,
            hour=parsed_time.tm_hour,
            minute=parsed_time.tm_min,
            second=parsed_time.tm_sec,
        ).isoformat()