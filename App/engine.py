from dataclasses import dataclass, field

from App.processor import OpportunityProcessor
from App.source_manager import SourceManager


@dataclass
class EngineReport:
    sources_loaded: int = 0
    sources_completed: int = 0
    sources_failed: int = 0

    opportunities_collected: int = 0
    opportunities_notified: int = 0
    opportunities_secondary: int = 0
    opportunities_duplicated: int = 0
    notification_failures: int = 0

    errors: list[str] = field(default_factory=list)


class OpportunityEngine:
    """
    Coordina todo el flujo:

    fuentes -> colectores -> oportunidades ->
    base de datos -> clasificación -> Telegram
    """

    def __init__(self, threshold: float = 50.0) -> None:
        self.threshold = threshold
        self.source_manager = SourceManager()
        self.processor = OpportunityProcessor(
            threshold=self.threshold,
        )

    def run_once(self) -> EngineReport:
        report = EngineReport()

        collectors = (
            self.source_manager.load_active_collectors()
        )

        report.sources_loaded = len(collectors)

        for collector in collectors:
            print(
                f"\nConsultando fuente: "
                f"{collector.source_name}"
            )

            try:
                opportunities = collector.collect()

                report.sources_completed += 1
                report.opportunities_collected += len(
                    opportunities
                )

                print(
                    "Publicaciones obtenidas: "
                    f"{len(opportunities)}"
                )

            except Exception as error:
                report.sources_failed += 1

                error_message = (
                    f"{collector.source_name}: "
                    f"{type(error).__name__}: {error}"
                )

                report.errors.append(error_message)

                print(
                    "Error consultando la fuente: "
                    f"{error_message}"
                )

                continue

            for opportunity in opportunities:
                try:
                    result = self.processor.process(
                        opportunity
                    )

                    self._register_result(
                        report,
                        result,
                    )

                    print(
                        f"- {result}: "
                        f"{opportunity.title}"
                    )

                except Exception as error:
                    report.errors.append(
                        f"{collector.source_name} / "
                        f"{opportunity.title}: "
                        f"{type(error).__name__}: {error}"
                    )

                    print(
                        "Error procesando oportunidad: "
                        f"{error}"
                    )

        return report

    @staticmethod
    def _register_result(
        report: EngineReport,
        result: str,
    ) -> None:

        if result == "notified":
            report.opportunities_notified += 1

        elif result == "secondary":
            report.opportunities_secondary += 1

        elif result == "duplicate":
            report.opportunities_duplicated += 1

        elif result == "notification_failed":
            report.notification_failures += 1


def print_report(report: EngineReport) -> None:
    print("\n" + "=" * 52)
    print("          OPPORTUNITY ENGINE - REPORTE")
    print("=" * 52)

    print(
        f"Fuentes activas............... "
        f"{report.sources_loaded}"
    )

    print(
        f"Fuentes completadas........... "
        f"{report.sources_completed}"
    )

    print(
        f"Fuentes con error............. "
        f"{report.sources_failed}"
    )

    print(
        f"Oportunidades recopiladas..... "
        f"{report.opportunities_collected}"
    )

    print(
        f"Notificaciones enviadas....... "
        f"{report.opportunities_notified}"
    )

    print(
        f"Bandeja secundaria............ "
        f"{report.opportunities_secondary}"
    )

    print(
        f"Duplicadas ignoradas.......... "
        f"{report.opportunities_duplicated}"
    )

    print(
        f"Fallos de notificación........ "
        f"{report.notification_failures}"
    )

    if report.errors:
        print("\nErrores registrados:")

        for error in report.errors:
            print(f"- {error}")

    print("=" * 52)