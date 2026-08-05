from App.models import Opportunity
from App.notifier import TelegramNotifier


opportunity = Opportunity(
    source_id="telegram-test",
    source_name="Opportunity Engine",
    title="Prueba segura de Telegram",
    url="https://example.com",
    country="CL",
    category="test",
    reward_amount=1000,
    required_cost=0,
    estimated_minutes=1,
    probability=100,
    score=100,
    requirements=["Confirmar que el mensaje llegó correctamente"],
)

notifier = TelegramNotifier()

print("Configurado:", notifier.is_configured())
print("Mensaje enviado:", notifier.send_opportunity(opportunity))