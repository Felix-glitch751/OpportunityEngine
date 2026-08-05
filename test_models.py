from App.models import Opportunity


opportunity = Opportunity(
    source_id="test-source",
    source_name="Fuente de prueba",
    title="Recibe $10.000 por registrarte",
    url="https://example.com/promocion",
    country="CL",
    category="signup_bonus",
    description="Promoción utilizada para probar la arquitectura.",
    currency="CLP",
    reward_amount=10000,
    required_cost=0,
    estimated_minutes=10,
    probability=80,
    score=75,
    requirements=[
        "Crear una cuenta",
        "Verificar el correo electrónico",
    ],
)

opportunity.validate()

print("OPORTUNIDAD CREADA CORRECTAMENTE")
print(f"Título: {opportunity.title}")
print(f"Score: {opportunity.score}%")
print(f"Notificar: {opportunity.should_notify(50)}")
print(opportunity.to_dict())