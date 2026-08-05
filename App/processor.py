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
        self.threshold = threshold
        self.database = OpportunityDatabase()
        self.notifier = TelegramNotifier()

    def process(self, opportunity: Opportunity) -> str:
        opportunity.validate()

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