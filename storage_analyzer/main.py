import click
from rich.console import Console

console = Console()


@click.group()
def cli():
    """Storage Analyzer - Analyze storage space on Linux."""
    pass


@cli.command()
@click.argument('path', default='.')
@click.option('--depth', default=2, help='Directory depth to scan')
def scan(path, depth):
    """Scan directory and show size breakdown."""
    console.print(f"[bold]Scanning:[/bold] {path}")
    console.print(f"[dim]Depth: {depth}[/dim]")


@cli.command()
@click.argument('path', default='.')
@click.option('--top', default=10, help='Number of files to show')
def large_files(path, top):
    """Find largest files."""
    console.print(f"[bold]Finding largest files in:[/bold] {path}")


@cli.command()
@click.argument('path', default='.')
@click.option('--top', default=10, help='Number of directories to show')
def large_dirs(path, top):
    """Find largest directories."""
    console.print(f"[bold]Finding largest directories in:[/bold] {path}")


@cli.command()
def clean():
    """List cleanable items (cache, logs, trash)."""
    console.print("[bold]Looking for cleanable items...[/bold]")


@cli.command()
def suggest():
    """Get actionable cleanup suggestions."""
    console.print("[bold]Analyzing storage...[/bold]")


if __name__ == '__main__':
    cli()
