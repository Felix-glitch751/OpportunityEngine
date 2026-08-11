from App.advisor import OpportunityAdvisor
from App.database import OpportunityDatabase
from App.models import Opportunity
from App.notifier import TelegramNotifier


class OpportunityProcessor:
    """
    Guarda, clasifica y notifica cada oportunidad.
    """

    def __init__(
        self,
        threshold: float = 50.0,
    ) -> None:
        self.advisor = OpportunityAdvisor()
        self.threshold = threshold
        self.database = OpportunityDatabase()
        self.notifier = TelegramNotifier()

    def process(self, opportunity: Opportunity) -> str:
        opportunity = self.advisor.enrich(opportunity)
        opportunity.validate()

        blocked_terms = [
    "casino",
    "apuesta",
    "rollover",
    "wagering",
    "depósito obligatorio",
    "deposito obligatorio",
]

        full_text = (
            f"{opportunity.title} "
            f"{opportunity.description}"
        ).lower()

        requires_forced_payment = (
            opportunity.required_cost > 0
            and not any(
                term in full_text
                for term in [
                    "cashback",
                    "devolución",
                    "devolucion",
                    "reembolso",
                ]
            )
        )

        blocked = any(
            term in full_text
            for term in blocked_terms
        )

        if blocked or requires_forced_payment:
            opportunity.score = min(
                opportunity.score,
                49,
            )
            
        was_saved = self.database.save(
            opportunity,
            threshold=self.threshold,
        )

        if not was_saved:
            return "duplicate"

        if not opportunity.should_notify(self.threshold):
            return "secondary"

        sent = self.notifier.send_opportunity(opportunity)

        if sent:
            self.database.mark_as_notified(opportunity.url)
            return "notified"

        return "notification_failed"