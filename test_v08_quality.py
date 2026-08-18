from App.models import Opportunity
from App.processor import OpportunityProcessor

# Solo comprueba las reglas sin enviar Telegram ni usar DB real.
assert "tarifas y comisiones" in OpportunityProcessor.LOW_QUALITY_TITLES
assert "bases de concursos y promociones" in OpportunityProcessor.LOW_QUALITY_TITLES
assert "previous" in OpportunityProcessor.LOW_QUALITY_TITLES
print("V0.8 QUALITY RULES OK")
