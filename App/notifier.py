import os

import requests
from dotenv import load_dotenv

from App.models import Opportunity


load_dotenv()


class TelegramNotifier:
    """Envía oportunidades calificadas al chat configurado."""

    def __init__(self) -> None:
        self.bot_token = os.getenv(
            "TELEGRAM_BOT_TOKEN",
            "",
        ).strip()

        self.chat_id = os.getenv(
            "TELEGRAM_CHAT_ID",
            "",
        ).strip()

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_opportunity(
        self,
        opportunity: Opportunity,
    ) -> bool:

        if not self.is_configured():
            print(
                "Telegram no está configurado. "
                "Revisa el archivo .env."
            )
            return False

        api_url = (
            "https://api.telegram.org/"
            f"bot{self.bot_token}/sendMessage"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": self._build_message(opportunity),
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(
                api_url,
                json=payload,
                timeout=20,
            )

            response.raise_for_status()
            return True

        except requests.RequestException as error:
            status_code = (
                error.response.status_code
                if error.response is not None
                else "sin respuesta"
            )

            print(
                "Error enviando Telegram. "
                f"Código HTTP: {status_code}"
            )

            return False

    @staticmethod
    def _build_message(
        opportunity: Opportunity,
    ) -> str:

        reward = (
            f"{opportunity.reward_amount:,.0f} "
            f"{opportunity.currency}"
        )

        cost = (
            f"{opportunity.required_cost:,.0f} "
            f"{opportunity.currency}"
        )

        requirements = "\n".join(
            f"• {requirement}"
            for requirement in opportunity.requirements
        )

        if not requirements:
            requirements = (
                "• Revisar condiciones en el enlace."
            )

        return (
            "🟢 OPPORTUNITY ENGINE\n\n"
            f"📌 {opportunity.title}\n\n"
            f"🏢 Fuente: {opportunity.source_name}\n"
            f"🌎 País: {opportunity.country}\n"
            f"🏷 Categoría: {opportunity.category}\n"
            f"💰 Beneficio estimado: {reward}\n"
            f"💸 Costo requerido: {cost}\n"
            f"⏱ Tiempo estimado: "
            f"{opportunity.estimated_minutes} min\n"
            f"🎯 Factibilidad: "
            f"{opportunity.score:.1f}%\n\n"
            f"Objetivo:\n"
            f"{requirements}\n\n"
            f"🔗 {opportunity.url}"
        )