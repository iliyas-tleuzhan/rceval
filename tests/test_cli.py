from pathlib import Path

from typer.testing import CliRunner

from rceval.cli import app

runner = CliRunner()


def test_cli_commands_work(tmp_path: Path):
    cases = tmp_path / "cases.jsonl"
    preds = tmp_path / "preds.jsonl"
    scores = tmp_path / "scores.json"
    report = tmp_path / "report.md"
    result = runner.invoke(app, ["create-sample", "--out", str(cases)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["validate", str(cases)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["run", str(cases), "--planner", "oracle", "--out", str(preds)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["score", str(cases), str(preds), "--out", str(scores)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["report", str(cases), str(preds), "--out", str(report)])
    assert result.exit_code == 0, result.output
    assert report.exists()

