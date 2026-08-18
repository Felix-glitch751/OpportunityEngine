from App.advisor import OpportunityAdvisor
from App.database import OpportunityDatabase
from App.models import Opportunity
from App.notifier import TelegramNotifier
from App.normalizer import canonicalize_url, normalize_text


class OpportunityProcessor:
    """Guarda, clasifica y notifica cada oportunidad."""

    BLOCKED_TERMS = (
        "casino", "apuesta", "rollover", "wagering",
        "depósito obligatorio", "deposito obligatorio",
    )

    LOW_QUALITY_TITLES = {
        "previous", "next", "prev", "anterior", "siguiente", "ver mas",
        "leer mas", "conoce mas", "hazte cliente ahora", "ver beneficio",
        "descarga pdf beneficios", "tarifas y comisiones",
        "bases de concursos y promociones", "comision para el mercado financiero",
        "beneficios", "promociones", "conoce nuestros beneficios",
    }

    LOW_QUALITY_PHRASES = (
        "bases legales", "terminos y condiciones", "términos y condiciones",
        "politica de privacidad", "política de privacidad", "tarifas y comisiones",
        "comision para el mercado financiero", "comisión para el mercado financiero",
        "descarga pdf", "ver beneficio", "conoce mas", "conoce más",
    )

    def __init__(self, threshold: float = 50.0) -> None:
        self.advisor = OpportunityAdvisor()
        self.threshold = threshold
        self.database = OpportunityDatabase()
        self.notifier = TelegramNotifier()

    def process(self, opportunity: Opportunity) -> str:
        opportunity.url = canonicalize_url(opportunity.url)
        opportunity = self.advisor.enrich(opportunity)
        opportunity.validate()

        full_text = f"{opportunity.title} {opportunity.description}".lower()
        normalized_title = normalize_text(opportunity.title)

        if any(term in full_text for term in self.BLOCKED_TERMS):
            opportunity.score = min(opportunity.score, 25)

        if normalized_title in self.LOW_QUALITY_TITLES:
            opportunity.score = min(opportunity.score, 15)

        if any(term in normalized_title for term in self.LOW_QUALITY_PHRASES):
            opportunity.score = min(opportunity.score, 20)

        reward_known = bool(opportunity.raw_data.get("reward_known", opportunity.reward_amount > 0))
        discount_percent = float(opportunity.raw_data.get("discount_percent", 0) or 0)
        strong_free_signal = any(term in full_text for term in (
            "gratis", "gratuito", "sin costo", "sin compra", "bono por registro",
            "gana $", "recibe $", "cashback", "devolucion", "devolución",
        ))

        # Evidencia mínima de una oportunidad real: valor cuantificado, porcentaje
        # o una señal gratuita/recompensa inequívoca.
        evidence_points = 0
        evidence_points += 2 if reward_known else 0
        evidence_points += 2 if discount_percent > 0 else 0
        evidence_points += 1 if strong_free_signal else 0
        evidence_points += 1 if opportunity.expires_at else 0
        opportunity.raw_data["evidence_points"] = evidence_points

        if evidence_points == 0:
            opportunity.score = min(opportunity.score, 39)
        elif evidence_points == 1 and not reward_known and discount_percent <= 0:
            opportunity.score = min(opportunity.score, 49)

        storage_result = self.database.save(opportunity, threshold=self.threshold)
        if storage_result == "duplicate":
            return "duplicate"

        # Si la misma URL cambió materialmente, puede volver a notificarse.
        opportunity.raw_data["storage_result"] = storage_result

        if not opportunity.should_notify(self.threshold):
            return "secondary"

        sent = self.notifier.send_opportunity(opportunity)
        if sent:
            self.database.mark_as_notified(opportunity.url)
            return "notified_updated" if storage_result == "updated" else "notified"
        return "notification_failed"
