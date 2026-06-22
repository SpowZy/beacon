"""Render the results figure used in the README.

Runs the offline evaluation and a routing sweep, then writes a two panel figure
to docs/results.png. Regenerate with:
  pip install -e ".[viz]"
  python -m beacon.plots
"""
from __future__ import annotations


def main() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from .agents.routing import route
    from .config import load_settings
    from .eval import run_eval
    from .models import Category, RawAlert, Severity, TriageResult
    from .synth import SUBURBS, generate_residents

    accent = "#4f46e5"
    good = "#16a34a"

    metrics = run_eval()

    settings = load_settings()
    residents = generate_residents(n=30, seed=7)
    alert = RawAlert(id="sweep", text="severity sweep", suburb="Palo Alto", location=SUBURBS["Palo Alto"])
    severities = [Severity.CRITICAL, Severity.URGENT, Severity.ADVISORY, Severity.INFO]
    reach = []
    for sev in severities:
        triage = TriageResult(severity=sev, category=Category.FIRE, confidence=1.0, rationale="sweep")
        reach.append(len(route(alert, triage, residents, settings).recipients))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3))

    keys = ["triage_accuracy", "grounded_rate", "delivered_rate", "pii_leak_rate"]
    labels = ["triage\naccuracy", "grounded\nrate", "delivered\nrate", "PII leak\nrate"]
    vals = [metrics[k] for k in keys]
    colors = [accent, accent, accent, good]
    bars = ax1.bar(labels, vals, color=colors)
    ax1.set_ylim(0, 1.08)
    ax1.set_title("Evaluation metrics (gated in CI)")
    for bar, value in zip(bars, vals):
        ax1.text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.2f}", ha="center", fontsize=9)
    for side in ("top", "right"):
        ax1.spines[side].set_visible(False)

    bars2 = ax2.bar([s.value for s in severities], reach, color=accent)
    ax2.set_title("Residents reached by severity (of 30)")
    ax2.set_ylabel("recipients")
    for bar, value in zip(bars2, reach):
        ax2.text(bar.get_x() + bar.get_width() / 2, value + 0.3, str(value), ha="center", fontsize=9)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)

    fig.suptitle("Beacon results", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig("docs/results.png", dpi=150, bbox_inches="tight")
    print("wrote docs/results.png")


if __name__ == "__main__":
    main()
