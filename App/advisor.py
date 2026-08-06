from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re

from App.models import Opportunity


@dataclass
class AdviceResult:
    final_score: float
    priority: str
    urgency: str
    difficulty: str
    roi_level: str
    net_reward: float
    value_per_hour: float
    time_remaining: str
    recommended_action: str
    expired: bool
    safe_to_notify: bool


class OpportunityAdvisor:
    """
    Convierte una oportunidad analizada en una recomendación accionable.
    """

    DATE_PATTERNS = (
        re.compile(
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"
        ),
        re.compile(
            r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"
        ),
    )

    def enrich(self, opportunity: Opportunity) -> Opportunity:
        if not opportunity.expires_at:
            opportunity.expires_at = self._extract_expiration(
                f"{opportunity.title} {opportunity.description}"
            )

        advice = self.evaluate(opportunity)

        opportunity.score = advice.final_score

        opportunity.raw_data = {
            **opportunity.raw_data,
            "advice": asdict(advice),
        }

        return opportunity

    def evaluate(
        self,
        opportunity: Opportunity,
    ) -> AdviceResult:
        now = datetime.now(timezone.utc)

        expiration = self._parse_datetime(
            opportunity.expires_at
        )

        expired = bool(
            expiration is not None and expiration <= now
        )

        remaining_hours = None

        if expiration is not None:
            remaining_hours = max(
                0,
                (expiration - now).total_seconds() / 3600,
            )

        net_reward = max(
            0,
            opportunity.reward_amount
            - opportunity.required_cost,
        )

        minutes = max(
            opportunity.estimated_minutes,
            1,
        )

        value_per_hour = (
            net_reward / minutes
        ) * 60

        urgency_score, urgency = self._urgency(
            remaining_hours
        )

        roi_score, roi_level = self._roi(
            value_per_hour=value_per_hour,
            net_reward=net_reward,
        )

        difficulty_score, difficulty = (
            self._difficulty(opportunity)
        )

        risk_level = int(
            opportunity.raw_data.get(
                "risk_level",
                3,
            )
        )

        final_score = (
            opportunity.score * 0.55
            + opportunity.probability * 0.10
            + urgency_score * 0.15
            + roi_score * 0.15
            + difficulty_score * 0.05
        )

        if risk_level >= 4:
            final_score -= 15

        if risk_level >= 5:
            final_score = min(
                final_score,
                25,
            )

        if expired:
            final_score = 0

        final_score = round(
            max(0, min(100, final_score)),
            2,
        )

        priority = self._priority(final_score)

        safe_to_notify = (
            final_score >= 50
            and not expired
            and risk_level < 5
        )

        return AdviceResult(
            final_score=final_score,
            priority=priority,
            urgency=urgency,
            difficulty=difficulty,
            roi_level=roi_level,
            net_reward=round(net_reward, 2),
            value_per_hour=round(value_per_hour, 2),
            time_remaining=self._format_remaining(
                remaining_hours
            ),
            recommended_action=(
                self._recommended_action(opportunity)
            ),
            expired=expired,
            safe_to_notify=safe_to_notify,
        )

    @staticmethod
    def _urgency(
        remaining_hours: float | None,
    ) -> tuple[float, str]:
        if remaining_hours is None:
            return 45, "Fecha no informada"

        if remaining_hours <= 2:
            return 100, "Crítica: menos de 2 horas"

        if remaining_hours <= 24:
            return 90, "Muy alta: menos de 24 horas"

        if remaining_hours <= 72:
            return 75, "Alta: menos de 3 días"

        if remaining_hours <= 168:
            return 60, "Media: menos de 7 días"

        return 40, "Baja"

    @staticmethod
    def _roi(
        value_per_hour: float,
        net_reward: float,
    ) -> tuple[float, str]:
        if net_reward <= 0:
            return 20, "No determinado"

        if value_per_hour >= 50000:
            return 100, "Excelente"

        if value_per_hour >= 20000:
            return 85, "Muy alto"

        if value_per_hour >= 10000:
            return 70, "Alto"

        if value_per_hour >= 5000:
            return 55, "Medio"

        return 35, "Bajo"

    @staticmethod
    def _difficulty(
        opportunity: Opportunity,
    ) -> tuple[float, str]:
        points = 100

        points -= min(
            opportunity.estimated_minutes / 2,
            35,
        )

        points -= min(
            len(opportunity.requirements) * 5,
            25,
        )

        if opportunity.required_cost > 0:
            points -= 20

        if points >= 80:
            return points, "Muy baja"

        if points >= 65:
            return points, "Baja"

        if points >= 45:
            return points, "Media"

        return max(points, 0), "Alta"

    @staticmethod
    def _priority(score: float) -> str:
        if score >= 85:
            return "🔴 Muy alta"

        if score >= 70:
            return "🟠 Alta"

        if score >= 50:
            return "🟡 Media"

        return "⚪ Secundaria"

    @staticmethod
    def _recommended_action(
        opportunity: Opportunity,
    ) -> str:
        if opportunity.requirements:
            return " → ".join(
                opportunity.requirements
            )

        return (
            "Abrir el enlace y verificar "
            "las condiciones completas."
        )

    @staticmethod
    def _format_remaining(
        remaining_hours: float | None,
    ) -> str:
        if remaining_hours is None:
            return "No informado"

        if remaining_hours <= 0:
            return "Expirada"

        days = int(remaining_hours // 24)
        hours = int(remaining_hours % 24)

        if days > 0:
            return f"{days} días y {hours} horas"

        return f"{hours} horas"

    def _extract_expiration(
        self,
        text: str,
    ) -> str | None:
        for index, pattern in enumerate(
            self.DATE_PATTERNS
        ):
            match = pattern.search(text)

            if not match:
                continue

            try:
                if index == 0:
                    day, month, year = map(
                        int,
                        match.groups(),
                    )
                else:
                    year, month, day = map(
                        int,
                        match.groups(),
                    )

                expiration = datetime(
                    year,
                    month,
                    day,
                    23,
                    59,
                    59,
                    tzinfo=timezone.utc,
                )

                return expiration.isoformat()

            except ValueError:
                continue

        return None

    @staticmethod
    def _parse_datetime(
        value: str | None,
    ) -> datetime | None:
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed

        except ValueError:
            return None