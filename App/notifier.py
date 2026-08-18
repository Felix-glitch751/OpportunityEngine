import os

import requests
from dotenv import load_dotenv

from App.models import Opportunity


load_dotenv()


class TelegramNotifier:
    def __init__(self) -> None:
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_opportunity(self, opportunity: Opportunity) -> bool:
        if not self.is_configured():
            print("Telegram no está configurado.")
            return False

        api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self._build_message(opportunity),
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(api_url, json=payload, timeout=20)
            response.raise_for_status()
            return True
        except requests.RequestException as error:
            status_code = error.response.status_code if error.response is not None else "sin respuesta"
            print(f"Error enviando Telegram. Código HTTP: {status_code}")
            return False

    @staticmethod
    def _build_message(opportunity: Opportunity) -> str:
        advice = opportunity.raw_data.get("advice", {})
        reward_known = bool(opportunity.raw_data.get("reward_known", opportunity.reward_amount > 0))
        cost_known = bool(opportunity.raw_data.get("cost_known", False))
        discount_percent = float(opportunity.raw_data.get("discount_percent", 0) or 0)
        opportunity_type = opportunity.raw_data.get("opportunity_type", opportunity.category)
        storage_result = opportunity.raw_data.get("storage_result", "new")
        evidence_points = int(opportunity.raw_data.get("evidence_points", 0) or 0)

        if reward_known:
            reward = f"{opportunity.reward_amount:,.0f} {opportunity.currency}"
        elif discount_percent > 0:
            reward = f"{discount_percent:.0f}% de descuento/devolución"
        else:
            reward = "No determinado"

        cost = (
            f"{opportunity.required_cost:,.0f} {opportunity.currency}"
            if cost_known
            else "No determinado"
        )

        if reward_known and cost_known:
            net_reward = f"{advice.get('net_reward', 0):,.0f} {opportunity.currency}"
        else:
            net_reward = "No calculable con los datos disponibles"

        action = advice.get("recommended_action", "Revisar las condiciones.")
        expiration = opportunity.expires_at or "No informada"

        conditions_note = ""
        if not cost_known or (not reward_known and discount_percent <= 0):
            conditions_note = "\n⚠️ Verifica monto, tope y condiciones antes de usarla.\n"

        update_label = "🔄 ACTUALIZACIÓN DE OPORTUNIDAD\n" if storage_result == "updated" else ""

        return (
            "🟢 OPPORTUNITY ENGINE\n"
            f"{update_label}\n"
            f"📌 {opportunity.title}\n\n"
            f"🏷 Tipo: {opportunity_type}\n"
            f"⭐ Prioridad: {advice.get('priority', 'No calculada')}\n"
            f"🎯 Score: {opportunity.score:.1f}/100\n"
            f"🔎 Evidencia: {evidence_points}/6\n"
            f"🏢 Fuente: {opportunity.source_name}\n"
            f"🌎 País: {opportunity.country}\n\n"
            f"💰 Beneficio: {reward}\n"
            f"💸 Costo/gasto mínimo: {cost}\n"
            f"💵 Beneficio neto: {net_reward}\n"
            f"📈 ROI: {advice.get('roi_level', 'No determinado')}\n"
            f"⏱ Tiempo requerido: {opportunity.estimated_minutes} min\n"
            f"🧩 Dificultad: {advice.get('difficulty', 'No determinada')}\n"
            f"{conditions_note}\n"
            f"📅 Expira: {expiration}\n"
            f"⏳ Tiempo restante: {advice.get('time_remaining', 'No informado')}\n"
            f"🚨 Urgencia: {advice.get('urgency', 'No informada')}\n\n"
            f"📱 Acción recomendada:\n{action}\n\n"
            f"🔗 {opportunity.url}"
        )
