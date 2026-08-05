from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Opportunity:
    """
    Formato universal para cualquier oportunidad económica detectada.
    Todas las fuentes deben entregar sus resultados usando esta estructura.
    """

    source_id: str
    source_name: str
    title: str
    url: str
    country: str
    category: str

    description: str = ""
    currency: str = "CLP"

    reward_amount: float = 0.0
    required_cost: float = 0.0
    estimated_minutes: int = 0

    probability: float = 0.0
    score: float = 0.0

    requirements: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    published_at: str | None = None
    expires_at: str | None = None

    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    raw_data: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Comprueba que la oportunidad tenga los datos mínimos."""

        if not self.source_id.strip():
            raise ValueError("source_id no puede estar vacío.")

        if not self.title.strip():
            raise ValueError("title no puede estar vacío.")

        if not self.url.strip():
            raise ValueError("url no puede estar vacía.")

        if not 0 <= self.probability <= 100:
            raise ValueError("probability debe estar entre 0 y 100.")

        if not 0 <= self.score <= 100:
            raise ValueError("score debe estar entre 0 y 100.")

        if self.reward_amount < 0:
            raise ValueError("reward_amount no puede ser negativo.")

        if self.required_cost < 0:
            raise ValueError("required_cost no puede ser negativo.")

        if self.estimated_minutes < 0:
            raise ValueError("estimated_minutes no puede ser negativo.")

    def should_notify(self, threshold: float = 50.0) -> bool:
        """Decide si debe enviarse una notificación."""

        return self.score >= threshold

    def to_dict(self) -> dict[str, Any]:
        """Convierte la oportunidad en un diccionario."""

        return asdict(self)