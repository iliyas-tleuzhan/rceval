from pathlib import Path

from rceval.datasets import sample_cases
from rceval.planners.unsafe_baseline import UnsafeBaselinePlanner
from rceval.report import render_report


def test_report_contains_expanded_sections(tmp_path: Path):
    cases = sample_cases()
    predictions = [UnsafeBaselinePlanner().predict(case) for case in cases]
    report = render_report(cases, predictions)
    out = tmp_path / "report.md"
    out.write_text(report, encoding="utf-8")
    assert "Worst Cases" in report
    assert "Decision Confusion Matrix" in report
    assert "Safety Issue Distribution" in report
    assert "Planner Recommendations" in report
