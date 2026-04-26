"""CLI entry point for storage analyzer."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from storage_analyzer.scanner import get_largest_files, get_largest_directories
from storage_analyzer.analyzer import analyze_directory, get_path_disk_usage, scan_directory_tree
from storage_analyzer.suggestions import get_all_suggestions, format_suggestions
from storage_analyzer.utils import format_size, get_home_directory

console = Console()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Storage Analyzer - Analyze storage space on Linux and get cleanup suggestions."""
    pass


@cli.command()
@click.argument('paths', nargs=-1, default=['.'])
@click.option('--depth', default=2, help='Directory depth to scan')
def scan(paths, depth):
    """Scan one or more directories and show size breakdown."""
    for path in paths:
        console.print(f"\n[bold cyan]Scanning:[/bold cyan] {path}")
        console.print(f"[dim]Depth: {depth}[/dim]\n")
        
        try:
            result = analyze_directory(path, max_depth=depth)
            
            console.print(Panel(
                f"[bold]Total Size:[/bold] {format_size(result.total_size)}\n"
                f"[bold]Files:[/bold] {result.file_count}\n"
                f"[bold]Directories:[/bold] {result.dir_count}",
                title="Summary",
                border_style="cyan"
            ))
            
            disk_usage = get_path_disk_usage(path)
            console.print(Panel(
                f"[bold]Total:[/bold] {disk_usage['total_formatted']}\n"
                f"[bold]Used:[/bold] {disk_usage['used_formatted']} ({disk_usage['percent_used']}%)\n"
                f"[bold]Free:[/bold] {disk_usage['free_formatted']}",
                title="Disk Usage",
                border_style="green"
            ))
            
            console.print("\n[bold cyan]Top Directories:[/bold cyan]")
            table = Table(box=box.SIMPLE)
            table.add_column("Path", style="cyan")
            table.add_column("Size", justify="right", style="yellow")
            
            for dir_info in result.largest_dirs[:10]:
                table.add_row(dir_info.path, dir_info.formatted_size)
            
            console.print(table)
            
        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
        except PermissionError as e:
            console.print(f"[bold red]Permission Error:[/bold red] {e}")


@cli.command()
@click.argument('paths', nargs=-1, default=['.'])
@click.option('--top', default=10, help='Number of files to show')
def large_files(paths, top):
    """Find largest files in one or more directories."""
    for path in paths:
        console.print(f"\n[bold cyan]Finding largest files in:[/bold cyan] {path}\n")
        
        try:
            files = get_largest_files(path, top=top)
            
            if not files:
                console.print("[yellow]No files found.[/yellow]")
                continue
            
            table = Table(box=box.SIMPLE)
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Path", style="cyan")
            
            for file_info in files:
                table.add_row(format_size(file_info.size), file_info.path)
            
            console.print(table)
            
        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
        except PermissionError as e:
            console.print(f"[bold red]Permission Error:[/bold red] {e}")


@cli.command()
@click.argument('paths', nargs=-1, default=['.'])
@click.option('--top', default=10, help='Number of directories to show')
def large_dirs(paths, top):
    """Find largest directories in one or more paths."""
    for path in paths:
        console.print(f"\n[bold cyan]Finding largest directories in:[/bold cyan] {path}\n")
        
        try:
            dirs = get_largest_directories(path, top=top)
            
            if not dirs:
                console.print("[yellow]No directories found.[/yellow]")
                continue
            
            table = Table(box=box.SIMPLE)
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Path", style="cyan")
            
            for dir_path, size in dirs:
                table.add_row(format_size(size), dir_path)
            
            console.print(table)
            
        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
        except PermissionError as e:
            console.print(f"[bold red]Permission Error:[/bold red] {e}")


@cli.command()
def clean():
    """List cleanable items (cache, logs, trash)."""
    console.print("\n[bold cyan]Looking for cleanable items...[/bold cyan]\n")
    
    items = get_all_suggestions()
    
    if not items:
        console.print("[green]No cleanable items found![/green]")
        return
    
    table = Table(box=box.SIMPLE)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Item", style="cyan")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Path", style="dim")
    
    for i, item in enumerate(items, 1):
        table.add_row(str(i), item.name, item.formatted_size, item.path)
    
    console.print(table)
    
    total = sum(item.size for item in items)
    console.print(f"\n[bold]Total cleanable:[/bold] {format_size(total)}")


@cli.command()
def suggest():
    """Get actionable cleanup suggestions."""
    console.print("\n[bold cyan]Analyzing storage for cleanup suggestions...[/bold cyan]\n")
    
    items = get_all_suggestions()
    
    if not items:
        console.print("[green]No cleanup suggestions found. Your storage is clean![/green]")
        return
    
    for i, item in enumerate(items, 1):
        panel = Panel(
            f"[bold]Path:[/bold] {item.path}\n\n"
            f"[bold green]Command to run:[/bold green]\n"
            f"[code]{item.command}[/code]",
            title=f"{i}. {item.name} ({item.formatted_size})",
            border_style="cyan"
        )
        console.print(panel)
    
    total = sum(item.size for item in items)
    console.print(Panel(
        f"[bold]Total potential savings:[/bold] {format_size(total)}",
        title="Summary",
        border_style="green"
    ))


@cli.command()
def disk():
    """Show disk usage for the filesystem."""
    console.print("\n[bold cyan]Disk Usage:[/bold cyan]\n")
    
    path = get_home_directory()
    usage = get_path_disk_usage(path)
    
    table = Table(box=box.SIMPLE)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="yellow")
    
    table.add_row("Total", usage['total_formatted'])
    table.add_row("Used", usage['used_formatted'])
    table.add_row("Free", usage['free_formatted'])
    table.add_row("Usage", f"{usage['percent_used']}%")
    
    console.print(table)


if __name__ == '__main__':
    cli()
