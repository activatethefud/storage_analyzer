"""CLI entry point for storage analyzer."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from storage_analyzer.scanner import get_largest_files, get_largest_directories
from storage_analyzer.analyzer import analyze_directory, get_path_disk_usage, scan_directory_tree
from storage_analyzer.suggestions import get_all_suggestions, format_suggestions
from storage_analyzer.utils import format_size, get_home_directory, get_all_devices, validate_device, get_mount_point_for_device, get_device_info

console = Console()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Storage Analyzer - Analyze storage space on Linux and get cleanup suggestions."""
    pass


def create_progress():
    """Create a progress bar instance."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    )


@cli.command()
@click.argument('paths', nargs=-1, default=['.'])
@click.option('--depth', default=2, help='Directory depth to scan')
def scan(paths, depth):
    """Scan one or more directories and show size breakdown."""
    for path in paths:
        console.print(f"\n[bold cyan]Scanning:[/bold cyan] {path}")
        console.print(f"[dim]Depth: {depth}[/dim]\n")
        
        try:
            file_count = [0]
            
            def progress_callback(count):
                file_count[0] = count
            
            with create_progress() as progress:
                task = progress.add_task("[cyan]Scanning files...", total=None, start=False)
                result = analyze_directory(path, max_depth=depth, progress_callback=progress_callback)
                progress.update(task, completed=True, description=f"[green]Scanned {result.file_count} files, {result.dir_count} directories")
            
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
            file_count = [0]
            
            def progress_callback(count):
                file_count[0] = count
            
            with create_progress() as progress:
                task = progress.add_task("[cyan]Scanning for large files...", total=None, start=False)
                files = get_largest_files(path, top=top)
                progress.update(task, completed=True, description=f"[green]Found {len(files)} large files (scanned {file_count[0]} files)")
            
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
            file_count = [0]
            
            def progress_callback(count):
                file_count[0] = count
            
            with create_progress() as progress:
                task = progress.add_task("[cyan]Scanning for large directories...", total=None, start=False)
                dirs = get_largest_directories(path, top=top)
                progress.update(task, completed=True, description=f"[green]Found {len(dirs)} large directories (scanned {file_count[0]} items)")
            
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
@click.option('--device', help='Filter by device (e.g., /dev/sda2, /dev/sda4)')
def clean(device):
    """List cleanable items (cache, logs, trash).
    
    Use --device to filter suggestions to a specific partition.
    Use 'storage-analyzer drives' to see available devices.
    """
    if device:
        is_valid, error = validate_device(device)
        if not is_valid:
            console.print(f"[bold red]Error:[/bold red] {error}")
            return
        mountpoint = get_mount_point_for_device(device)
        console.print(f"\n[bold cyan]Looking for cleanable items on:[/bold cyan] {device} (mounted at {mountpoint})\n")
    else:
        console.print("\n[bold cyan]Looking for cleanable items...[/bold cyan]\n")
    
    with create_progress() as progress:
        task = progress.add_task("[cyan]Scanning for cleanable items...", total=None, start=False)
        items = get_all_suggestions(device=device)
        progress.update(task, completed=True, description=f"[green]Found {len(items)} cleanable items")
    
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
@click.option('--device', help='Filter by device (e.g., /dev/sda2, /dev/sda4)')
def suggest(device):
    """Get actionable cleanup suggestions.
    
    Use --device to get suggestions for a specific partition.
    Use 'storage-analyzer drives' to see available devices.
    """
    if device:
        is_valid, error = validate_device(device)
        if not is_valid:
            console.print(f"[bold red]Error:[/bold red] {error}")
            return
        mountpoint = get_mount_point_for_device(device)
        console.print(f"\n[bold cyan]Analyzing storage for cleanup suggestions on:[/bold cyan] {device} (mounted at {mountpoint})\n")
    else:
        console.print("\n[bold cyan]Analyzing storage for cleanup suggestions...[/bold cyan]\n")
    
    with create_progress() as progress:
        task = progress.add_task("[cyan]Scanning for cleanup suggestions...", total=None, start=False)
        items = get_all_suggestions(device=device)
        progress.update(task, completed=True, description=f"[green]Found {len(items)} suggestions")
    
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


@cli.command()
def drives():
    """List all block devices (disks and partitions).
    
    Shows all available drives and their mount points.
    Use this to find the device path for --device option.
    """
    console.print("\n[bold cyan]Available Block Devices:[/bold cyan]\n")
    
    with create_progress() as progress:
        task = progress.add_task("[cyan]Scanning block devices...", total=None, start=False)
        devices = get_all_devices()
        progress.update(task, completed=True, description=f"[green]Found {len(devices)} devices")
    
    if not devices:
        console.print("[yellow]No block devices found. Is lsblk available?[/yellow]")
        return
    
    for disk in devices:
        if disk.is_disk:
            console.print(f"[bold cyan]Disk:[/bold cyan] {disk.device} ({disk.size})")
            
            if disk.children:
                for part in disk.children:
                    mount = part.mountpoint if part.mountpoint else "[bold red]not mounted[/bold red]"
                    console.print(f"  └── {part.device}  {part.size}  {mount}")
            else:
                console.print(f"  [dim]No partitions[/dim]")
            console.print()


if __name__ == '__main__':
    cli()
