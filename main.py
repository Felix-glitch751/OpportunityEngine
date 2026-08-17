from App.engine import OpportunityEngine, print_report


def main() -> None:
    print("=" * 52)
    print("           OPPORTUNITY ENGINE v0.7")
    print("=" * 52)

    engine = OpportunityEngine(
        threshold=50,
    )

    report = engine.run_once()

    print_report(report)


if __name__ == "__main__":
    main()