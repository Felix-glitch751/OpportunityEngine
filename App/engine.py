from dataclasses import dataclass, field
from datetime import datetime, timezone

from App.processor import OpportunityProcessor
from App.source_manager import SourceManager


@dataclass
class EngineReport:
    sources_loaded: int = 0
    sources_completed: int = 0
    sources_failed: int = 0
    sources_skipped: int = 0

    opportunities_collected: int = 0
    opportunities_notified: int = 0
    opportunities_secondary: int = 0
    opportunities_duplicated: int = 0
    notification_failures: int = 0

    errors: list[str] = field(default_factory=list)


class OpportunityEngine:

    def __init__(
        self,
        threshold: float = 50.0,
    ) -> None:

        self.threshold = threshold

        self.source_manager = SourceManager()

        self.processor = OpportunityProcessor(
            threshold=self.threshold,
        )

    def _should_check_source(
        self,
        collector,
    ) -> bool:

        state = self.processor.database.get_source_state(
            collector.source_id
        )

        if state is None:
            return True

        last_checked_at = state.get(
            "last_checked_at"
        )

        if not last_checked_at:
            return True

        try:
            last_checked = datetime.fromisoformat(
                last_checked_at.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:
            return True

        if last_checked.tzinfo is None:
            last_checked = last_checked.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        elapsed_minutes = (
            now - last_checked
        ).total_seconds() / 60

        interval = getattr(
            collector,
            "check_interval_minutes",
            60,
        )

        return elapsed_minutes >= interval

    def run_once(self) -> EngineReport:

        report = EngineReport()

        collectors = (
            self.source_manager.load_active_collectors()
        )

        report.sources_loaded = len(collectors)

        for collector in collectors:

            if not self._should_check_source(
                collector
            ):
                report.sources_skipped += 1

                print(
                    f"\nSaltando fuente: "
                    f"{collector.source_name} "
                    f"(todavía no corresponde revisar)"
                )

                continue

            print(
                f"\nConsultando fuente: "
                f"{collector.source_name}"
            )

            try:
                opportunities = collector.collect()

                self.processor.database.update_source_state(
                    source_id=collector.source_id,
                    checked_at=datetime.now(
                        timezone.utc
                    ).isoformat(),
                    status="ok",
                )

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
                    f"{type(error).__name__}: "
                    f"{error}"
                )

                report.errors.append(
                    error_message
                )

                print(
                    "Error consultando la fuente: "
                    f"{error_message}"
                )

                self.processor.database.update_source_state(
                    source_id=collector.source_id,
                    checked_at=datetime.now(
                        timezone.utc
                    ).isoformat(),
                    status="error",
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

                    error_message = (
                        f"{collector.source_name} / "
                        f"{opportunity.title}: "
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

                    report.errors.append(
                        error_message
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


def print_report(
    report: EngineReport,
) -> None:

    print("\n" + "=" * 52)
    print("          OPPORTUNITY ENGINE - REPORTE")
    print("=" * 52)

    print(
        f"Fuentes activas............... "
        f"{report.sources_loaded}"
    )

    print(
        f"Fuentes revisadas............. "
        f"{report.sources_completed}"
    )

    print(
        f"Fuentes omitidas.............. "
        f"{report.sources_skipped}"
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