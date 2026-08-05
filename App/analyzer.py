import re
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    reward_amount: float = 0.0
    required_cost: float = 0.0
    estimated_minutes: int = 15

    probability: float = 0.0
    score: float = 0.0

    currency: str = "CLP"
    risk_level: int = 3
    requirements: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class OpportunityAnalyzer:
    """
    Analizador inicial basado en reglas.

    No usa APIs pagadas ni inteligencia artificial externa.
    """

    POSITIVE_KEYWORDS = {
        "cashback": 18,
        "devolución": 18,
        "devolucion": 18,
        "reembolso": 18,
        "bono": 15,
        "recompensa": 15,
        "premio": 12,
        "gratis": 12,
        "gratuito": 10,
        "cupón": 10,
        "cupon": 10,
        "descuento": 8,
        "promoción": 8,
        "promocion": 8,
        "regístrate": 7,
        "registrate": 7,
        "primera compra": 8,
        "referido": 8,
        "puntos": 6,
    }

    NEGATIVE_KEYWORDS = {
        "casino": 25,
        "apuesta": 25,
        "rollover": 25,
        "wagering": 25,
        "depósito obligatorio": 20,
        "deposito obligatorio": 20,
        "suscripción": 10,
        "suscripcion": 10,
        "hasta": 5,
        "sorteo": 10,
        "probabilidad de ganar": 15,
    }

    MONEY_PATTERN = re.compile(
        r"""
        (?:
            \$\s*
            (?P<amount1>\d{1,3}(?:[.\s]\d{3})+|\d+)
            |
            (?P<amount2>\d{1,3}(?:[.\s]\d{3})+|\d+)
            \s*
            (?P<currency>CLP|USD|EUR|pesos?|dólares?|dolares?)
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    PERCENTAGE_PATTERN = re.compile(
        r"(\d{1,3})\s*%",
        re.IGNORECASE,
    )

    def analyze(
        self,
        title: str,
        description: str,
        source_trust: float = 60.0,
        country: str = "INT",
    ) -> AnalysisResult:

        full_text = (
            f"{title} {description}"
        ).lower()

        reward_amount, currency = (
            self._extract_reward(full_text)
        )

        required_cost = self._estimate_cost(
            full_text,
            reward_amount,
        )

        estimated_minutes = self._estimate_time(
            full_text
        )

        requirements = self._extract_requirements(
            full_text
        )

        tags = self._extract_tags(full_text)

        risk_level = self._calculate_risk(
            full_text,
            required_cost,
        )

        probability = self._calculate_probability(
            full_text=full_text,
            source_trust=source_trust,
            reward_amount=reward_amount,
            risk_level=risk_level,
            country=country,
        )

        score = self._calculate_score(
            full_text=full_text,
            reward_amount=reward_amount,
            required_cost=required_cost,
            estimated_minutes=estimated_minutes,
            probability=probability,
            risk_level=risk_level,
        )

        return AnalysisResult(
            reward_amount=reward_amount,
            required_cost=required_cost,
            estimated_minutes=estimated_minutes,
            probability=probability,
            score=score,
            currency=currency,
            risk_level=risk_level,
            requirements=requirements,
            tags=tags,
        )

    def _extract_reward(
        self,
        text: str,
    ) -> tuple[float, str]:

        values: list[float] = []
        currency = "CLP"

        for match in self.MONEY_PATTERN.finditer(text):
            raw_amount = (
                match.group("amount1")
                or match.group("amount2")
            )

            if not raw_amount:
                continue

            normalized = (
                raw_amount
                .replace(".", "")
                .replace(" ", "")
            )

            try:
                values.append(float(normalized))
            except ValueError:
                continue

            detected_currency = (
                match.group("currency") or ""
            ).lower()

            if (
                "usd" in detected_currency
                or "dólar" in detected_currency
                or "dolar" in detected_currency
            ):
                currency = "USD"

            elif "eur" in detected_currency:
                currency = "EUR"

        reward_amount = max(values) if values else 0.0

        return reward_amount, currency

    def _estimate_cost(
        self,
        text: str,
        reward_amount: float,
    ) -> float:

        if any(term in text for term in [
            "sin depósito",
            "sin deposito",
            "sin costo",
            "gratis",
            "gratuito",
        ]):
            return 0.0

        if any(term in text for term in [
            "deposita",
            "depositar",
            "depósito",
            "deposito",
            "compra mínima",
            "compra minima",
        ]):
            return max(
                reward_amount * 0.5,
                1.0,
            )

        return 0.0

    @staticmethod
    def _estimate_time(text: str) -> int:
        if any(term in text for term in [
            "descarga",
            "registro",
            "regístrate",
            "registrate",
            "activar promoción",
            "activar promocion",
        ]):
            return 10

        if any(term in text for term in [
            "completa el nivel",
            "alcanza el nivel",
            "varias tareas",
            "30 días",
            "30 dias",
        ]):
            return 120

        if any(term in text for term in [
            "primera compra",
            "pagar con",
            "comprar",
        ]):
            return 15

        return 20

    @staticmethod
    def _extract_requirements(
        text: str,
    ) -> list[str]:

        requirements: list[str] = []

        rules = {
            "registr": "Crear o verificar una cuenta",
            "descarga": "Descargar la aplicación",
            "primera compra": "Realizar la primera compra",
            "pagar con": "Usar el medio de pago indicado",
            "referido": "Usar o compartir un código de referido",
            "deposit": "Realizar un depósito",
            "nivel": "Completar el nivel solicitado",
            "activar": "Activar previamente la promoción",
        }

        for keyword, requirement in rules.items():
            if keyword in text:
                requirements.append(requirement)

        if not requirements:
            requirements.append(
                "Revisar las condiciones completas"
            )

        return requirements

    def _extract_tags(
        self,
        text: str,
    ) -> list[str]:

        tags: list[str] = []

        tag_rules = {
            "cashback": "cashback",
            "devolución": "cashback",
            "devolucion": "cashback",
            "bono": "bonus",
            "cupón": "coupon",
            "cupon": "coupon",
            "referido": "referral",
            "gratis": "free",
            "banco": "banking",
            "tarjeta": "card",
            "puntos": "loyalty",
            "casino": "gambling",
        }

        for keyword, tag in tag_rules.items():
            if keyword in text and tag not in tags:
                tags.append(tag)

        return tags

    @staticmethod
    def _calculate_risk(
        text: str,
        required_cost: float,
    ) -> int:

        if any(term in text for term in [
            "casino",
            "apuesta",
            "rollover",
            "wagering",
        ]):
            return 5

        if required_cost > 0:
            return 4

        if any(term in text for term in [
            "sorteo",
            "hasta",
            "podrías ganar",
            "podrias ganar",
        ]):
            return 3

        return 1

    def _calculate_probability(
        self,
        full_text: str,
        source_trust: float,
        reward_amount: float,
        risk_level: int,
        country: str,
    ) -> float:

        probability = source_trust

        for keyword, weight in (
            self.POSITIVE_KEYWORDS.items()
        ):
            if keyword in full_text:
                probability += weight * 0.35

        for keyword, penalty in (
            self.NEGATIVE_KEYWORDS.items()
        ):
            if keyword in full_text:
                probability -= penalty * 0.45

        if reward_amount > 0:
            probability += 8
        else:
            probability -= 12

        if risk_level >= 4:
            probability -= 20

        if country.upper() == "CL":
            probability += 5

        return self._clamp(probability)

    def _calculate_score(
        self,
        full_text: str,
        reward_amount: float,
        required_cost: float,
        estimated_minutes: int,
        probability: float,
        risk_level: int,
    ) -> float:

        keyword_score = 0.0

        for keyword, weight in (
            self.POSITIVE_KEYWORDS.items()
        ):
            if keyword in full_text:
                keyword_score += weight

        for keyword, penalty in (
            self.NEGATIVE_KEYWORDS.items()
        ):
            if keyword in full_text:
                keyword_score -= penalty

        economic_score = min(
            reward_amount / 250,
            25,
        )

        if reward_amount <= 0:
            economic_score = 0

        cost_ratio = (
            required_cost / reward_amount
            if reward_amount > 0
            else 1
        )

        cost_score = max(
            0,
            15 - (cost_ratio * 20),
        )

        time_score = max(
            0,
            15 - (estimated_minutes / 10),
        )

        risk_score = max(
            0,
            15 - ((risk_level - 1) * 4),
        )

        final_score = (
            probability * 0.40
            + economic_score
            + cost_score
            + time_score
            + risk_score
            + keyword_score * 0.20
        )

        if reward_amount <= 0:
            final_score = min(
                final_score,
                45,
            )

        if risk_level == 5:
            final_score = min(
                final_score,
                25,
            )

        return round(
            self._clamp(final_score),
            2,
        )

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> float:
        return max(
            minimum,
            min(maximum, value),
        )