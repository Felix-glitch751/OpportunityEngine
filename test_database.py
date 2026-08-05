from App.database import OpportunityDatabase
from App.models import Opportunity


database = OpportunityDatabase()


high_score_opportunity = Opportunity(
    source_id="test-high",
    source_name="Fuente confiable",
    title="Cashback de $10.000",
    url="https://example.com/high-score",
    country="CL",
    category="cashback",
    reward_amount=10000,
    required_cost=0,
    estimated_minutes=10,
    probability=85,
    score=82,
)


low_score_opportunity = Opportunity(
    source_id="test-low",
    source_name="Fuente experimental",
    title="Recompensa con requisitos poco claros",
    url="https://example.com/low-score",
    country="INT",
    category="reward",
    reward_amount=5000,
    required_cost=2000,
    estimated_minutes=90,
    probability=35,
    score=38,
)


saved_high = database.save(
    high_score_opportunity,
    threshold=50,
)

saved_low = database.save(
    low_score_opportunity,
    threshold=50,
)


print("RESULTADOS DE LA PRUEBA")
print("-----------------------")
print(f"Oportunidad alta guardada: {saved_high}")
print(f"Oportunidad baja guardada: {saved_low}")
print(f"Total almacenado: {database.count_all()}")
print(f"Bandeja principal: {len(database.get_primary_queue())}")
print(f"Bandeja secundaria: {len(database.get_secondary_queue())}")