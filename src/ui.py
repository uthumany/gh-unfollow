"""
ui.py — Premium terminal UI for gh-unfollow v2.1.0

Full multi-panel dashboard as specified in the UI/UX design:
  - FIGlet ASCII banner (cyan)
  - Operation Status panel: progress bar, counts, rate limit, elapsed/ETA
  - Current Action panel: spinner + username being processed
  - Recent Logs: last 5 actions with timestamps and icons
  - Animated cooldown countdown bar
  - Dry-run mode with magenta theme
  - Color-coded: green=success, yellow=warning, red=error, cyan=banner
  - Graceful fallback to basic ANSI/ASCII mode if rich is not installed

Install with: pip install gh-unfollow[ui]
"""

import os
import sys
import time
from collections import deque
from typing import Any

# ─── Try to import rich (optional) ────────────────────────────────────────

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.align import Align
    from rich.spinner import Spinner

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ─── ANSI Color Constants (basic fallback) ─────────────────────────────────

class Colors:
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

# ─── Spinner Characters ────────────────────────────────────────────────────

SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_spin_idx = 0


def spinner_char() -> str:
    global _spin_idx
    c = SPINNER_CHARS[_spin_idx % len(SPINNER_CHARS)]
    _spin_idx += 1
    return c


# ─── FIGlet Banner Art ─────────────────────────────────────────────────────

BANNER_LINES = [
    "  ██████╗ ██╗  ██╗    ██╗   ██╗███╗   ██╗███████╗ ██████╗ ██╗     ██╗      ██████╗ ██╗    ██╗",
    " ██╔════╝ ██║  ██║    ██║   ██║████╗  ██║██╔════╝██╔═══██╗██║     ██║     ██╔═══██╗██║    ██║",
    " ██║  ███╗███████║    ██║   ██║██╔██╗ ██║█████╗  ██║   ██║██║     ██║     ██║   ██║██║ █╗ ██║",
    " ██║   ██║██╔══██║    ██║   ██║██║╚██╗██║██╔══╝  ██║   ██║██║     ██║     ██║   ██║██║███╗██║",
    " ╚██████╔╝██║  ██║    ╚██████╔╝██║ ╚████║██║     ╚██████╔╝███████╗███████╗╚██████╔╝╚███╔███╔╝",
    "  ╚═════╝ ╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚══════╝╚══════╝ ╚═════╝  ╚══╝╚══╝ ",
]

DRY_RUN_BANNER_TOP = "╔═════════════════════════════════════════════════════════════════════════╗"
DRY_RUN_BANNER_MID = "║                        DRY RUN MODE ACTIVE                           ║"
DRY_RUN_BANNER_BOT = "║              No actual unfollows will be performed.                    ║"
DRY_RUN_BANNER_END = "╚═════════════════════════════════════════════════════════════════════════╝"


# ─── Progress Bar Helper ───────────────────────────────────────────────────

def _make_bar(percent: float, width: int = 38) -> str:
    """Build a text progress bar: ████░░░░"""
    filled = max(0, int(width * percent / 100))
    empty = width - filled
    return "█" * filled + "░" * empty


# ─── Time Formatting ───────────────────────────────────────────────────────

def _fmt_seconds(s: float) -> str:
    """Format seconds as mm:ss or hh:mm:ss."""
    s = int(s)
    if s < 3600:
        return f"{s // 60:02d}m {s % 60:02d}s"
    return f"{s // 3600:d}h {(s % 3600) // 60:02d}m"


# ── UI Controller ──────────────────────────────────────────────────────────

class UI:
    """Terminal UI controller — rich or basic ANSI fallback."""

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
        self.tty = sys.stdout.isatty()

        # Dashboard state
        self._target = 0
        self._completed = 0
        self._rate_limit = "?"
        self._current_action = ""
        self._recent_logs: deque[str] = deque(maxlen=5)
        self._start_time = 0.0
        self._last_frame_lines = 0

        # Rich handles
        self._console: Any = None
        self._live: Any = None
        self._dashboard_task: Any = None

        if self.rich:
            self._console = Console(force_terminal=True, color_system="standard")
        elif no_color:
            # Kill ANSI escape codes
            for attr in dir(Colors):
                if not attr.startswith("_") and isinstance(getattr(Colors, attr), str):
                    setattr(Colors, attr, "")

    # ═══════════════════════════════════════════════════════════════════════
    #  BANNER
    # ═══════════════════════════════════════════════════════════════════════

    def show_banner(self) -> None:
        """Display the FIGlet startup banner."""
        version_str = f"v{self.version}  |  github.com/uthumany/gh-unfollow"

        if self.rich:
            banner = Text()
            styles = ["bold cyan", "cyan", "cyan", "cyan", "bold cyan", "dim cyan"]
            for i, line in enumerate(BANNER_LINES):
                banner.append(line + "\n", style=styles[i])
            banner.append(f"                {version_str}", style="dim")
            self._console.print(banner)
        else:
            lines = BANNER_LINES[:]
            for i in range(len(lines)):
                style = Colors.CYAN + (Colors.BOLD if i in (0, 4) else "")
                lines[i] = f"{style}{lines[i]}{Colors.RESET}"
            lines.append(f"                {Colors.DIM}{version_str}{Colors.RESET}")
            print("\n".join(lines), flush=True)

        if self.dry_run:
            self._print_dry_run_banner()

    def _print_dry_run_banner(self) -> None:
        if self.rich:
            self._console.print()
            self._console.print(Panel(
                "[bold magenta]DRY RUN MODE ACTIVE[/bold magenta]\n"
                "[dim]No actual unfollows will be performed.[/dim]",
                border_style="magenta", box=box.DOUBLE,
            ))
        else:
            mc, rs = Colors.MAGENTA + Colors.BOLD, Colors.RESET
            print(f"\n{mc}{DRY_RUN_BANNER_TOP}{rs}")
            print(f"{mc}{DRY_RUN_BANNER_MID}{rs}")
            print(f"{mc}{DRY_RUN_BANNER_BOT}{rs}")
            print(f"{mc}{DRY_RUN_BANNER_END}{rs}\n", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  MULTI-PANEL DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════

    def start_dashboard(self, target: int, rate_limit: str = "?") -> None:
        """Initialize the dashboard with target count."""
        self._target = target
        self._completed = 0
        self._rate_limit = rate_limit
        self._current_action = ""
        self._recent_logs.clear()
        self._start_time = time.time()

        if self.rich:
            self._start_rich_dashboard()
        else:
            self._print_basic_dashboard_frame()

    def _start_rich_dashboard(self) -> None:
        """Create the rich Live dashboard layout."""
        if not self.tty:
            # Non-TTY: don't use Live, just print compact frames
            self._live = None
            self._print_basic_dashboard_frame()
            return

        self._render_rich_frame()

        def render():
            return self._build_rich_dashboard()

        self._live = Live(
            render(),
            console=self._console,
            refresh_per_second=8,
            transient=False,
        )
        self._live.start()

    def _build_rich_dashboard(self) -> Any:
        """Build the rich dashboard renderable."""
        elapsed = time.time() - self._start_time
        progress = (self._completed / self._target * 100) if self._target else 0
        eta = (
            _fmt_seconds((elapsed / self._completed) * (self._target - self._completed))
            if self._completed > 0
            else "--"
        )
        bar = _make_bar(progress)
        percent_str = f"{progress:.0f}%"

        # Current action spinner
        spin = SPINNER_CHARS[int(time.time() * 10) % len(SPINNER_CHARS)]
        action_text = self._current_action or "Fetching..."
        action = Text(f"  {spin} {action_text}", style="cyan")

        # Operation status table
        status = Table.grid(padding=(0, 4))
        status.add_column(style="dim", width=14)
        status.add_column()
        status.add_column(style="dim", width=14)
        status.add_column()
        status.add_row("Progress:", f"[bold cyan]{bar}[/bold cyan]  [bold]{percent_str}[/bold]")
        status.add_row(
            "Unfollowed:", f"[bold green]{self._completed}[/bold green] / {self._target}",
            "Rate Limit:", f"[yellow]{self._rate_limit}[/yellow] remaining",
        )
        status.add_row(
            "Elapsed:", _fmt_seconds(elapsed),
            "ETA:", f"[yellow]{eta}[/yellow]",
        )

        # Recent logs
        log_lines = Text()
        log_lines.append("Recent:\n", style="bold dim")
        for entry in self._recent_logs:
            log_lines.append(f"  {entry}\n", style="dim")

        # Assemble layout
        layout = Layout()
        layout.split(
            Layout(name="status", size=5),
            Layout(name="action", size=2),
            Layout(name="logs", size=7),
        )
        layout["status"].update(Panel(status, title="Operation Status", border_style="cyan", padding=(1, 2)))
        layout["action"].update(Panel(action, title="Current Action", border_style="cyan", padding=(0, 2)))
        layout["logs"].update(Panel(log_lines, title="Recent Logs", border_style="dim cyan", padding=(0, 2)))

        return layout

    def _render_rich_frame(self) -> None:
        """Trigger a manual frame render (for non-live contexts)."""
        if self._console:
            self._console.print(self._build_rich_dashboard())

    def _print_basic_dashboard_frame(self) -> None:
        """Print one compact dashboard frame (basic ANSI mode)."""
        elapsed = time.time() - self._start_time
        progress = (self._completed / self._target * 100) if self._target else 0
        eta = (
            _fmt_seconds((elapsed / self._completed) * (self._target - self._completed))
            if self._completed > 0
            else "--"
        )
        bar = _make_bar(progress, 30)
        percent_str = f"{progress:.0f}%"

        cy, rs, bo, di, gr, ye = Colors.CYAN, Colors.RESET, Colors.BOLD, Colors.DIM, Colors.GREEN, Colors.YELLOW
        spin = spinner_char()
        action_text = self._current_action or "Fetching..."
        limit_str = f"{self._rate_limit}"

        frame = []
        frame.append(f"  {cy}┌── Status ──────────────────────────────────────────┐{rs}")
        frame.append(f"  {cy}│{rs}  {bo}{bar}{rs}  {percent_str}    "
                     f"Unfollowed: {gr}{self._completed}{rs}/{self._target}    "
                     f"Limit: {ye}{limit_str}{rs}  {cy}│{rs}")
        frame.append(f"  {cy}│{rs}  {spin} {action_text}")
        # Compact logs line
        if self._recent_logs:
            last = list(self._recent_logs)[-1]
            frame.append(f"  {cy}│{rs}  {di}{last}{rs}")
        frame.append(f"  {cy}└{'─' * 52}┘{rs}")

        # Overwrite previous frame with ANSI cursor-up
        if self._last_frame_lines:
            sys.stdout.write(f"\033[{self._last_frame_lines}A")  # Move up
            sys.stdout.write("\033[J")  # Clear to end
        sys.stdout.write("\n".join(frame) + "\n")
        sys.stdout.flush()
        self._last_frame_lines = len(frame)

    def update_dashboard(
        self,
        completed: int,
        action: str = "",
        rate_limit: str = "?",
    ) -> None:
        """Update the live dashboard."""
        self._completed = completed
        self._current_action = action
        self._rate_limit = rate_limit

        if self.rich and self._live:
            self._live.update(self._build_rich_dashboard())
        elif not self.rich:
            self._print_basic_dashboard_frame()

    def add_log_entry(self, icon: str, msg: str, style: str = "dim") -> None:
        """Add an entry to the recent logs ring."""
        ts = time.strftime("%H:%M:%S")
        entry = f"{ts} │ {icon} {msg}"
        self._recent_logs.append(entry)

    def stop_dashboard(self) -> None:
        """Stop the live dashboard."""
        if self.rich and self._live:
            try:
                self._live.stop()
            except Exception:
                pass
        self._live = None

    # ═══════════════════════════════════════════════════════════════════════
    #  AUTH & TARGET LOG LINES
    # ═══════════════════════════════════════════════════════════════════════

    def log_auth(self, username: str, following: int) -> None:
        if self.rich:
            self._console.print(f"  ℹ Authenticated as: [bold white]{username}[/bold white]")
            self._console.print(f"  ℹ Currently following: [bold]{following}[/bold]")
            self._console.print()
        else:
            print(f"  [i] Authenticated as: {username}")
            print(f"  [i] Currently following: {following}\n", flush=True)

    def log_target(self, target: int, delay: float, batch: int, batch_delay: int, eta: str) -> None:
        if self.rich:
            t = Table.grid(padding=(0, 2))
            t.add_column(style="dim"); t.add_column()
            t.add_row("Target:", f"[bold cyan]{target}[/bold cyan] users")
            t.add_row("Delay:", f"{delay}s")
            t.add_row("Batch:", f"{batch} users (cooldown {batch_delay}s)")
            t.add_row("Est. time:", f"[yellow]{eta}[/yellow]")
            self._console.print(t)
            self._console.print()
        else:
            print(f"  Target: {target} users")
            print(f"  Delay: {delay}s | Batch: {batch} | Cooldown: {batch_delay}s")
            print(f"  Estimated time: {eta}\n", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  ACTION LOGGING (also adds to recent logs)
    # ═══════════════════════════════════════════════════════════════════════

    def log_page(self, page: int, count: int, rate_limit: str) -> None:
        if self.rich:
            self._console.print(f"  [dim]Page {page}:[/dim] {count} users  [dim](limit: {rate_limit})[/dim]")
        else:
            print(f"  Page {page}: {count} users (limit: {rate_limit})", flush=True)

    def log_unfollow(self, n: int, total: int, name: str, rate_limit: str) -> None:
        action = "Would unfollow" if self.dry_run else "Unfollowed"
        if self.rich:
            style = "magenta" if self.dry_run else "green"
            icon = f"[{style}]◇[/{style}]" if self.dry_run else f"[green]✔[/green]"
            self._console.print(
                f"  {icon} [{n}/{total}] {action} [bold white]@{name}[/bold white]  "
                f"[dim](limit: {rate_limit})[/dim]"
            )
        else:
            c = Colors.MAGENTA if self.dry_run else Colors.GREEN
            icon = f"{c}◇{Colors.RESET}" if self.dry_run else f"{c}✔{Colors.RESET}"
            print(f"  {icon} [{n}/{total}] {action} @{name}  {Colors.DIM}(limit: {rate_limit}){Colors.RESET}", flush=True)

        # Add to recent logs ring
        self._recent_logs.append(f"✔ {action} @{name}")

    def log_skip(self, name: str, reason: str = "Whitelisted") -> None:
        if self.rich:
            self._console.print(f"  [yellow]⚠[/yellow] Skipped [bold white]@{name}[/bold white] [dim]({reason})[/dim]")
        else:
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} Skipped @{name} {Colors.DIM}({reason}){Colors.RESET}", flush=True)
        self._recent_logs.append(f"⚠ Skipped @{name}")

    def log_rate_limit(self, remaining: int) -> None:
        if self.rich:
            self._console.print(f"  [yellow]![/yellow] Rate limit low ({remaining}) — cooling down...")
        else:
            print(f"  {Colors.YELLOW}!{Colors.RESET} Rate limit low ({remaining}) — cooling down...", flush=True)

    def log_error(self, msg: str) -> None:
        if self.rich:
            self._console.print(f"  [red]✗[/red] {msg}")
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {msg}", flush=True)

    def log_warn(self, msg: str) -> None:
        if self.rich:
            self._console.print(f"  [yellow]![/yellow] {msg}")
        else:
            print(f"  {Colors.YELLOW}!{Colors.RESET} {msg}", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  FINAL SUMMARY
    # ═══════════════════════════════════════════════════════════════════════

    def log_final(self, unfollowed: int, elapsed: str) -> None:
        if self.rich:
            self._console.print()
            self._console.print(Panel(
                f"[bold green]DONE[/bold green] — "
                f"{'Would have ' if self.dry_run else ''}unfollowed "
                f"[bold]{unfollowed}[/bold] users in [yellow]{elapsed}[/yellow]",
                border_style="green", box=box.DOUBLE,
            ))
        else:
            print(f"\n{'=' * 50}")
            if self.dry_run:
                print(f"  DONE: Would have unfollowed {unfollowed} users")
            else:
                print(f"  DONE: Unfollowed {unfollowed} users in {elapsed}")
            print(f"{'=' * 50}", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIMATED COOLDOWN COUNTDOWN
    # ═══════════════════════════════════════════════════════════════════════

    def cooldown(self, seconds: int, reason: str = "Batch limit reached") -> None:
        """Display animated cooldown countdown bar."""
        if self.rich:
            from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

            with Progress(
                SpinnerColumn(spinner_name="dots"),
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
            print(f"\n  {Colors.YELLOW}⏳ {reason}. Cooling down...{Colors.RESET}")
            bar_width = 35
            for i in range(seconds, 0, -1):
                filled = max(0, int(bar_width * (seconds - i) / seconds))
                bar = "\u2588" * filled + "\u2591" * (bar_width - filled)
                print(f"\r  [{Colors.YELLOW}{bar}{Colors.RESET}] {i}s remaining ", end="", flush=True)
                time.sleep(1)
            print("\n", flush=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def is_whitelisted(self, name: str) -> bool:
        return name.lower() in {w.lower() for w in self.whitelist}


def check_rich_available() -> bool:
    return RICH_AVAILABLE
