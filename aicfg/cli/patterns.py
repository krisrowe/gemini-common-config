"""CLI commands for pattern testing."""
import json

import click
from rich.console import Console

from aicfg.sdk import patterns


@click.group(name="patterns")
def patterns_group():
    """Test secret detection patterns."""
    pass


@patterns_group.command("list")
@click.option("--seed", type=int, default=None, help="Random seed (default: from YAML)")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--test", "test_values", multiple=True, help="Additional values to test (can repeat)")
def list_patterns(seed, output_format, test_values):
    """Generate examples from patterns and test detection."""
    result = patterns.test_patterns(seed=seed)

    # Add user-provided test values at the top
    user_tests = []
    for val in test_values:
        check = patterns.check_secret(val)
        user_tests.append({
            "id": "user-test",
            "type": "User Test",
            "pattern": "-",
            "example": val,
            "description": "USER TEST",
            "expect": "flag" if check["flagged"] else "pass",
            "flagged": check["flagged"],
            "correct": True,  # User tests are always "correct" (no expectation)
            "entropy": check["entropy"],
            "exception": check["exception"],
            "reason": check["reason"],
        })
    if user_tests:
        result["results"] = user_tests + result["results"]

    if output_format == "json":
        click.echo(json.dumps(result, indent=2))
        return

    # Table output - no wrap
    con = Console(width=130, soft_wrap=False)
    con.print(f"[bold]Pattern Detection Test (seed={result['seed']})[/bold]\n")
    con.print(f"{'':5} {'Type':<22} {'Example':<48} {'Ent':>5} {'Exception':<12} {'Description'}")
    con.print("─" * 108)

    prev_flagged = None
    for r in result["results"]:
        if prev_flagged is not None and r["flagged"] != prev_flagged:
            con.print("─" * 108)

        # Icon: [alert] [outcome]
        # Outcome: ✗ = flagged, ✓ = pass
        outcome = "✗" if r["flagged"] else "✓"
        # Alert: 🚨 if wrong, 👀 for user tests, space if correct
        if r["id"] == "user-test":
            alert = "👀"
        elif not r["correct"]:
            alert = "🚨"
        else:
            alert = "  "
        icon = f"{alert} {outcome}"
        exc = r["exception"] or "-"
        example = r["example"][:46] + ".." if len(r["example"]) > 48 else r["example"]
        desc = r["description"][:30] + ".." if len(r["description"]) > 32 else r["description"]

        con.print(f"{icon} [cyan]{r['type']:<22}[/cyan] [dim]{example:<48}[/dim] {r['entropy']:>5.2f} {exc:<12} {desc}")
        prev_flagged = r["flagged"]

    con.print("─" * 108)

    # Summary
    s = result["summary"]
    n_user = len(user_tests)
    n_pattern = s["total"] - n_user
    n_correct = s["correct"] - n_user  # user tests are always "correct"
    con.print()
    user_suffix = f" + {n_user} user-provided" if n_user else ""
    con.print(f"[bold]Results:[/bold] {n_correct}/{n_pattern} as expected{user_suffix}")
    con.print(
        f"  True Positives: {s['true_positives']}  |  "
        f"False Positives: {s['false_positives']}  |  "
        f"True Negatives: {s['true_negatives']}  |  "
        f"False Negatives: {s['false_negatives']}"
    )
    con.print(f"  Precision: {s['precision']*100:.0f}%  |  Recall: {s['recall']*100:.0f}%")


@patterns_group.command("show")
@click.argument("pattern_id")
@click.option("--seed", type=int, default=None)
def show_pattern(pattern_id, seed):
    """Show details for a specific pattern."""
    con = Console()
    result = patterns.test_patterns(seed=seed)

    for r in result["results"]:
        if r["id"] == pattern_id:
            con.print(f"[bold]ID:[/bold] {r['id']}")
            con.print(f"[bold]Type:[/bold] {r['type']}")
            con.print(f"[bold]Pattern:[/bold] {r['pattern']}")
            con.print(f"[bold]Example:[/bold] {r['example']}")
            con.print(f"[bold]Description:[/bold] {r['description']}")
            con.print()
            con.print(f"[bold]Expected:[/bold] {r['expect']}")
            con.print(f"[bold]Flagged:[/bold] {r['flagged']}")
            con.print(f"[bold]Correct:[/bold] {'✓' if r['correct'] else '❌'}")
            con.print(f"[bold]Entropy:[/bold] {r['entropy']:.3f}")
            con.print(f"[bold]Exception:[/bold] {r['exception'] or 'None'}")
            con.print(f"[bold]Reason:[/bold] {r['reason']}")
            return

    con.print(f"[red]Pattern '{pattern_id}' not found[/red]")


@patterns_group.command("test")
@click.argument("value")
def test_value(value):
    """Test if a value would be flagged as a secret."""
    con = Console()
    result = patterns.check_secret(value)

    if result["flagged"]:
        con.print("[bold red]🚨 FLAGGED[/bold red]")
    else:
        con.print("[bold green]✓ PASS[/bold green]")

    con.print(f"  Value:     {value}")
    con.print(f"  Length:    {len(value)}")
    con.print(f"  Entropy:   {result['entropy']:.3f}")
    con.print(f"  Exception: {result['exception'] or 'None'}")
    con.print(f"  Reason:    {result['reason']}")
