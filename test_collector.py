from App.source_manager import SourceManager


manager = SourceManager()

collectors = manager.load_active_collectors()

print("PRUEBA DEL COLLECTOR FRAMEWORK")
print("-----------------------------")
print(f"Colectores activos: {len(collectors)}")


for collector in collectors:
    print(
        f"\nConsultando: "
        f"{collector.source_name}"
    )

    opportunities = collector.collect()

    print(
        f"Oportunidades obtenidas: "
        f"{len(opportunities)}"
    )

    for opportunity in opportunities:
        opportunity.validate()

        print(
            f"- {opportunity.title}"
        )

        print(
            f"  URL: {opportunity.url}"
        )

        print(
            f"  Score inicial: "
            f"{opportunity.score}%"
        )