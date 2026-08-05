from uuid import uuid4

from App.models import Opportunity
from App.processor import OpportunityProcessor


processor = OpportunityProcessor(threshold=50)


unique_id = uuid4().hex[:8]


high_score = Opportunity(
    source_id="pipeline-test-high",
    source_name="Fuente confiable de prueba",
    title="Cashback de $12.000",
    url=f"https://example.com/high-{unique_id}",
    country="CL",
    category="cashback",
    description="Prueba completa del sistema.",
    currency="CLP",
    reward_amount=12000,
    required_cost=0,
    estimated_minutes=8,
    probability=90,
    score=86,
    requirements=[
        "Abrir la promoción",
        "Revisar sus condiciones",
        "Completar la acción indicada",
    ],
)


low_score = Opportunity(
    source_id="pipeline-test-low",
    source_name="Fuente experimental de prueba",
    title="Recompensa poco clara",
    url=f"https://example.com/low-{unique_id}",
    country="INT",
    category="reward",
    description="Debe ir a la bandeja secundaria.",
    currency="CLP",
    reward_amount=4000,
    required_cost=2000,
    estimated_minutes=90,
    probability=30,
    score=35,
    requirements=[
        "Revisar condiciones manualmente",
    ],
)


high_result = processor.process(high_score)
low_result = processor.process(low_score)


print("RESULTADO DEL PIPELINE")
print("----------------------")
print(f"Oportunidad alta: {high_result}")
print(f"Oportunidad baja: {low_result}")
print(
    "Bandeja principal:",
    len(processor.database.get_primary_queue()),
)
print(
    "Bandeja secundaria:",
    len(processor.database.get_secondary_queue()),
)