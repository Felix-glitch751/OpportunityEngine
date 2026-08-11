from App.collector import BaseCollector
from App.models import Opportunity


class ControlledTestCollector(BaseCollector):
    """
    Fuente temporal para comprobar el recorrido completo
    GitHub Actions -> Opportunity Engine -> Telegram.
    """

    def __init__(
        self,
        source_id: str,
        source_name: str,
        url: str,
        country: str,
        category: str,
    ) -> None:
        super().__init__(
            source_id=source_id,
            source_name=source_name,
            url=url,
            country=country,
            category=category,
        )

    def collect(self) -> list[Opportunity]:
        return [
            Opportunity(
                source_id=self.source_id,
                source_name=self.source_name,
                title="PRUEBA CONTROLADA - Bono gratuito por registro",
                url="https://example.com/opportunity-engine-cloud-test",
                country=self.country,
                category=self.category,
                description=(
                    "Prueba interna. Recompensa gratuita de "
                    "10000 CLP por completar un registro. "
                    "Sin depósito, sin compra y sin inversión."
                ),
                currency="CLP",
                reward_amount=10000,
                required_cost=0,
                estimated_minutes=5,
                probability=100,
                score=100,
                requirements=[
                    "Completar registro gratuito",
                    "Verificar cuenta",
                ],
                tags=[
                    "registration",
                    "free",
                    "reward",
                ],
                raw_data={
                    "collector_type": "controlled_test",
                    "risk_level": 1,
                    "test": True,
                },
            )
        ]