"""Run the whole pipeline on the synthetic scenario and print the trace.

No API key, no model download, no network. This is the short screen recording:
a synthetic alert that carries personal details goes in, gets triaged, scrubbed
to P2, routed by geography, and verified before delivery.
"""
from __future__ import annotations

from .config import load_settings
from .graph import run_pipeline
from .models import PipelineResult
from .synth import generate_residents, scenario_alerts


def _print_result(res: PipelineResult) -> None:
    print(f"\n=== alert {res.alert_id} ===")
    for line in res.trace:
        print(f"  {line}")
    print(f"  final status: {res.status.upper()}")
    print(f"  message to residents: {res.message}")


def main() -> None:
    settings = load_settings()
    residents = generate_residents(n=30, seed=7)
    print(f"Beacon demo. backend={settings.llm_backend}. residents={len(residents)}.")
    for alert in scenario_alerts():
        res = run_pipeline(alert, residents, settings)
        _print_result(res)
    print("\nDone. No API key or downloaded model was required for this run.")


if __name__ == "__main__":
    main()
