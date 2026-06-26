"""
ui.py — Rich-enhanced terminal UI for gh-unfollow v2.0.0

Provides premium terminal UX with:
- FIGlet ASCII banner (cyan)
- Live progress dashboard with animated spinners
- Color-coded log output (green/yellow/red/gray)
- Rate-limit cooldown countdown bar
- Dry-run mode with magenta/purple theme
- Whitelist support (skip users)
- Graceful fallback to basic mode if rich is not installed

Install with: pip install gh-unfollow[ui]
"""

import os
import sys
import time
from typing import Any

# Try to import rich — fail gracefully if not installed
try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    from rich.text import Text
    from rich.layout import Layout
    from rich.spinner import Spinner
    from rich import box

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ─── Color Constants (ANSI fallback) ────────────────────────────────────────

class Colors:
    """ANSI color codes for basic mode fallback."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    BG_MAGENTA = "\033[45m"


# ─── FIGlet Banner ──────────────────────────────────────────────────────────

BANNER_ART = r"""
{cyan}  ██████╗ ██╗  ██╗    ██╗   ██╗███╗   ██╗███████╗ ██████╗ ██╗     ██╗      ██████╗ ██╗    ██╗
 ██╔════╝ ██║  ██║    ██║   ██║████╗  ██║██╔════╝██╔═══██╗██║     ██║     ██╔═══██╗██║    ██║
 ██║  ███╗███████║    ██║   ██║██╔██╗ ██║█████╗  ██║   ██║██║     ██║     ██║   ██║██║ █╗ ██║
 ██║   ██║██╔══██║    ██║   ██║██║╚██╗██║██╔══╝  ██║   ██║██║     ██║     ██║   ██║██║███╗██║
 ╚██████╔╝██║  ██║    ╚██████╔╝██║ ╚████║██║     ╚██████╔╝███████╗███████╗╚██████╔╝╚███╔███╔╝
  ╚═════╝ ╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚══════╝╚══════╝ ╚═════╝  ╚══╝╚══╝ {reset}
{version_line}
""".format(
    cyan=Colors.CYAN if not RICH_AVAILABLE else "",
    reset=Colors.RESET if not RICH_AVAILABLE else "",
    version_line="",
)

DRY_RUN_BANNER = """
╔═════════════════════════════════════════════════════════════════════════╗
║                        {color}DRY RUN MODE ACTIVE{reset}                           ║
║              No actual unfollows will be performed.                    ║
╚═════════════════════════════════════════════════════════════════════════╝
"""


# ─── Spinner Characters ─────────────────────────────────────────────────────

SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_spin_idx = 0


def spinner_char() -> str:
    """Return next spinner character (for basic mode)."""
    global _spin_idx
    c = SPINNER_CHARS[_spin_idx % len(SPINNER_CHARS)]
    _spin_idx += 1
    return c


# ─── UI Controller ──────────────────────────────────────────────────────────


class UI:
    """Terminal UI controller — rich or basic fallback."""

    def __init__(
        self,
        version: str,
        dry_run: bool = False,
        no_color: bool = False,
        whitelist: list[str] | None = None,
    ):
        self.version = version
        self.dry_run = dry_run
        self.no_color = no_color
        self.whitelist = set(whitelist or [])
        self.rich = RICH_AVAILABLE and not no_color
        self._live_ok = sys.stdout.isatty()  # Live display needs TTY

        self._live: Any = None
        self._console: Any = None
        self._progress: Any = None
        self._task_id: Any = None
        self._spinner_idx = 0

        if self.rich:
            self._console = Console(force_terminal=True, color_system="standard")
        else:
            # Disable ANSI codes if piped or --no-color
            if no_color or not sys.stdout.isatty():
                Colors.RESET = ""
                Colors.BOLD = ""
                Colors.DIM = ""
                Colors.CYAN = ""
                Colors.GREEN = ""
                Colors.YELLOW = ""
                Colors.RED = ""
                Colors.MAGENTA = ""
                Colors.GRAY = ""

    # ── Banner ───────────────────────────────────────────────────────────

    def show_banner(self):
        """Display the startup banner."""
        version_str = f"v{self.version}  |  github.com/uthumany/gh-unfollow"

        if self.rich:
            from rich.text import Text
            from rich.panel import Panel

            banner = Text()
            banner.append(
                "  ██████╗ ██╗  ██╗    ██╗   ██╗███╗   ██╗███████╗ ██████╗ ██╗     ██╗      ██████╗ ██╗    ██╗\n",
                style="bold cyan",
            )
            banner.append(
                " ██╔════╝ ██║  ██║    ██║   ██║████╗  ██║██╔════╝██╔═══██╗██║     ██║     ██╔═══██╗██║    ██║\n",
                style="cyan",
            )
            banner.append(
                " ██║  ███╗███████║    ██║   ██║██╔██╗ ██║█████╗  ██║   ██║██║     ██║     ██║   ██║██║ █╗ ██║\n",
                style="cyan",
            )
            banner.append(
                " ██║   ██║██╔══██║    ██║   ██║██║╚██╗██║██╔══╝  ██║   ██║██║     ██║     ██║   ██║██║███╗██║\n",
                style="cyan",
            )
            banner.append(
                " ╚██████╔╝██║  ██║    ╚██████╔╝██║ ╚████║██║     ╚██████╔╝███████╗███████╗╚██████╔╝╚███╔███╔╝\n",
                style="bold cyan",
            )
            banner.append(
                "  ╚═════╝ ╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚══════╝╚══════╝ ╚═════╝  ╚══╝╚══╝ \n",
                style="dim cyan",
            )
            banner.append(f"                {version_str}", style="dim")
            self._console.print(banner)
        else:
            print(BANNER_ART.format(
                cyan=Colors.CYAN, reset=Colors.RESET,
                version_line=f"                {Colors.DIM}{version_str}{Colors.RESET}",
            ))

        # Dry-run warning
        if self.dry_run:
            self._print_dry_run_banner()

    def _print_dry_run_banner(self):
        """Print the dry-run warning banner."""
        if self.rich:
            self._console.print()
            self._console.print(Panel(
                "[bold magenta]DRY RUN MODE ACTIVE[/bold magenta]\n"
                "[dim]No actual unfollows will be performed.[/dim]",
                border_style="magenta",
                box=box.DOUBLE,
            ))
        else:
            print(DRY_RUN_BANNER.format(
                color=Colors.MAGENTA + Colors.BOLD,
                reset=Colors.RESET,
            ))

    # ── Live Dashboard ────────────────────────────────────────────────────

    def start_dashboard(self, target: int):
        """Initialize the live-updating dashboard."""
        if self.rich and self._live_ok:
            self._progress = Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
            )
            self._task_id = self._progress.add_task(
                "[cyan]Unfollowing...", total=target
            )
            self._live = Live(self._progress, console=self._console, refresh_per_second=10)
            self._live.start()

    def update_dashboard(self, completed: int, action: str = ""):
        """Update the live dashboard with current progress."""
        if self.rich and self._live_ok and self._progress and self._task_id is not None:
            self._progress.update(
                self._task_id,
                completed=completed,
                description=f"[cyan]Unfollowing[/cyan] {action}",
            )

    def stop_dashboard(self):
        """Stop and finalize the live dashboard."""
        if self.rich and self._live_ok and self._live:
            self._live.stop()

    # ── Log Lines ─────────────────────────────────────────────────────────

    def log_auth(self, username: str, following: int):
        """Log authentication info."""
        if self.rich:
            self._console.print(f"  {self._icon('info')} Authenticated as: [bold white]{username}[/bold white]")
            self._console.print(f"  {self._icon('info')} Currently following: [bold]{following}[/bold]")
            self._console.print()
        else:
            print(f"  [i] Authenticated as: {username}")
            print(f"  [i] Currently following: {following}")
            print()

    def log_target(self, target: int, delay: float, batch: int, batch_delay: int, eta: str):
        """Log target and timing info."""
        if self.rich:
            t = Table.grid(padding=(0, 2))
            t.add_column(style="dim")
            t.add_column()
            t.add_row("Target:", f"[bold cyan]{target}[/bold cyan] users")
            t.add_row("Delay:", f"{delay}s")
            t.add_row("Batch:", f"{batch} users")
            t.add_row("Cooldown:", f"{batch_delay}s between batches")
            t.add_row("Est. time:", f"[yellow]{eta}[/yellow]")
            self._console.print(t)
            self._console.print()
        else:
            print(f"  Target: {target} users")
            print(f"  Delay: {delay}s | Batch: {batch} | Batch pause: {batch_delay}s")
            print(f"  Estimated time: {eta}")
            print()

    def log_page(self, page: int, count: int, rate_limit: str):
        """Log a page fetch."""
        if self.rich:
            self._console.print(f"  [dim]Page {page}:[/dim] {count} users  [dim](limit: {rate_limit})[/dim]")
        else:
            print(f"  Page {page}: {count} users (limit: {rate_limit})")

    def log_unfollow(self, n: int, total: int, name: str, rate_limit: str):
        """Log a successful unfollow."""
        prefix = "[SIM]" if self.dry_run else "✔"
        if self.rich:
            style = "magenta" if self.dry_run else "green"
            action = "Would unfollow" if self.dry_run else "Unfollowed"
            self._console.print(
                f"  [{style}]{prefix}[/{style}] [{n}/{total}] {action} [bold white]@{name}[/bold white]  "
                f"[dim](limit: {rate_limit})[/dim]"
            )
        else:
            action = "Would unfollow" if self.dry_run else "Unfollowed"
            color = Colors.MAGENTA if self.dry_run else Colors.GREEN
            print(f"  {color}{prefix}{Colors.RESET} [{n}/{total}] {action} @{name}  {Colors.DIM}(limit: {rate_limit}){Colors.RESET}")

    def log_skip(self, name: str, reason: str = "Whitelisted"):
        """Log a skipped user."""
        if self.rich:
            self._console.print(f"  [yellow]⚠[/yellow] Skipped [bold white]@{name}[/bold white] [dim]({reason})[/dim]")
        else:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} Skipped @{name} {Colors.DIM}({reason}){Colors.RESET}")

    def log_rate_limit(self, remaining: int):
        """Log a rate limit pause."""
        if self.rich:
            self._console.print(f"  [yellow]![/yellow] Low rate limit ({remaining}), cooling down...")
        else:
            print(f"  {Colors.YELLOW}!{Colors.RESET} Low rate limit ({remaining}), cooling down...")

    def log_error(self, msg: str):
        """Log an error."""
        if self.rich:
            self._console.print(f"  [red]✗[/red] {msg}")
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {msg}")

    def log_final(self, unfollowed: int, elapsed: str):
        """Log the final summary."""
        if self.rich:
            self._console.print()
            self._console.print(Panel(
                f"[bold green]DONE[/bold green] — "
                f"{'Would have ' if self.dry_run else ''}unfollowed "
                f"[bold]{unfollowed}[/bold] users in [yellow]{elapsed}[/yellow]",
                border_style="green",
                box=box.DOUBLE,
            ))
        else:
            print()
            print(f"{'='*50}")
            if self.dry_run:
                print(f"  DONE: Would have unfollowed {unfollowed} users")
            else:
                print(f"  DONE: Unfollowed {unfollowed} users in {elapsed}")
            print(f"{'='*50}")

    # ── Cooldown Countdown ────────────────────────────────────────────────

    def cooldown(self, seconds: int, reason: str = "Batch limit reached"):
        """Display animated cooldown countdown bar."""
        if self.rich:
            with Progress(
                TextColumn(f"[yellow]⏳ {reason}"),
                BarColumn(bar_width=35),
                TextColumn("[yellow]{task.remaining:.0f}s[/yellow]"),
                console=self._console,
            ) as p:
                task = p.add_task("", total=seconds)
                for _ in range(seconds):
                    time.sleep(1)
                    p.update(task, advance=1)
        else:
            msg = f"  {Colors.YELLOW}!{Colors.RESET} {reason}. Cooling down..."
            print(msg)
            bar_width = 35
            for i in range(seconds, 0, -1):
                filled = int(bar_width * (seconds - i) / seconds)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"\r  [{bar}] {i}s remaining ", end="", flush=True)
                time.sleep(1)
            print()

    # ── Simple Spinner ────────────────────────────────────────────────────

    def spinner_message(self, msg: str) -> str:
        """Return a message with spinner (basic mode)."""
        return f"  [{spinner_char()}] {msg}"

    # ── Helpers ───────────────────────────────────────────────────────────

    def _icon(self, name: str) -> str:
        """Return a unicode icon."""
        icons = {"info": "ℹ", "ok": "✔", "warn": "⚠", "err": "✗", "sim": "◇"}
        return icons.get(name, "•")

    def is_whitelisted(self, name: str) -> bool:
        """Check if a user is whitelisted."""
        return name.lower() in {w.lower() for w in self.whitelist}


def check_rich_available() -> bool:
    """Check if rich library is installed."""
    return RICH_AVAILABLE
