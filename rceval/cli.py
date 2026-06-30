from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from rceval.datasets import sample_cases
from rceval.importers.rgen import convert_rgen_records
from rceval.io import read_cases, read_predictions, read_records, write_json, write_records
from rceval.planners import PLANNERS
from rceval.report import render_comparison, render_report
from rceval.safety_judge import RuleBasedSafetyJudge
from rceval.scoring import score_predictions

app = typer.Typer(help="RCEval robot instruction benchmark CLI.")
console = Console()


@app.command("create-sample")
def create_sample(out: Path = typer.Option(..., "--out", help="Output JSONL/YAML/JSON path.")) -> None:
    cases = sample_cases()
    write_records(out, cases)
    console.print(f"[green]Wrote {len(cases)} sample cases to {out}[/green]")


@app.command()
def validate(path: Path) -> None:
    cases = read_cases(path)
    table = Table(title="Benchmark Validation")
    table.add_column("File")
    table.add_column("Cases", justify="right")
    table.add_column("Status")
    table.add_row(str(path), str(len(cases)), "valid")
    console.print(table)


@app.command()
def run(
    cases_path: Path,
    planner: str = typer.Option("safe_baseline", "--planner", help="oracle|safe_baseline|unsafe_baseline"),
    out: Path = typer.Option(..., "--out", help="Output predictions path."),
) -> None:
    if planner not in PLANNERS:
        raise typer.BadParameter(f"Unknown planner '{planner}'. Available: {', '.join(PLANNERS)}")
    cases = read_cases(cases_path)
    planner_instance = PLANNERS[planner]()
    predictions = [planner_instance.predict(case) for case in cases]
    write_records(out, predictions)
    console.print(f"[green]Wrote {len(predictions)} {planner} predictions to {out}[/green]")


@app.command()
def score(cases_path: Path, predictions_path: Path, out: Path | None = typer.Option(None, "--out")) -> None:
    cases = read_cases(cases_path)
    predictions = read_predictions(predictions_path)
    report = score_predictions(cases, predictions)
    _print_score_table(report)
    if out:
        write_json(out, report)
        console.print(f"[green]Wrote score JSON to {out}[/green]")


@app.command()
def judge(cases_path: Path, predictions_path: Path, out: Path = typer.Option(..., "--out")) -> None:
    cases = read_cases(cases_path)
    predictions = {prediction.case_id: prediction for prediction in read_predictions(predictions_path)}
    judge_instance = RuleBasedSafetyJudge()
    judgements = [judge_instance.judge(case, predictions[case.id]) for case in cases if case.id in predictions]
    write_records(out, judgements)
    console.print(f"[green]Wrote {len(judgements)} safety judgements to {out}[/green]")


@app.command()
def report(cases_path: Path, predictions_path: Path, out: Path = typer.Option(..., "--out")) -> None:
    markdown = render_report(read_cases(cases_path), read_predictions(predictions_path))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    console.print(f"[green]Wrote Markdown report to {out}[/green]")


@app.command()
def compare(
    cases_path: Path,
    prediction_paths: list[Path] = typer.Argument(...),
    out: Path = typer.Option(..., "--out"),
) -> None:
    cases = read_cases(cases_path)
    reports = {
        str(path): score_predictions(cases, read_predictions(path))
        for path in prediction_paths
    }
    markdown = render_comparison(reports)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    console.print(f"[green]Wrote comparison report to {out}[/green]")


@app.command("import-rgen")
def import_rgen(path: Path, out: Path = typer.Option(..., "--out")) -> None:
    cases = convert_rgen_records(read_records(path))
    write_records(out, cases)
    console.print(f"[green]Imported {len(cases)} RGen records to {out}[/green]")


def _print_score_table(report) -> None:
    table = Table(title="RCEval Scores")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    aggregate = report.aggregate
    table.add_row("total_cases", str(aggregate.total_cases))
    table.add_row("passed_cases", str(aggregate.passed_cases))
    table.add_row("mean_overall_score", f"{aggregate.mean_overall_score:.3f}")
    table.add_row("mean_safety_score", f"{aggregate.mean_safety_score:.3f}")
    table.add_row("decision_accuracy", f"{aggregate.decision_accuracy:.3f}")
    table.add_row("hallucination_rate", f"{aggregate.hallucination_rate:.3f}")
    console.print(table)


if __name__ == "__main__":
    app()

