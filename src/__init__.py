"""gh-unfollow — Bulk unfollow GitHub users with smart rate limiting.

CLI tool to mass-unfollow GitHub users. Features:
- Premium terminal UI with animated dashboard (when rich is installed)
- ASCII FIGlet banner
- Live progress bar with ETA
- Color-coded output (green/yellow/red/cyan)
- Rate-limit cooldown countdown bar
- Dry-run mode with distinct magenta theme
- Whitelist support (skip specific users)
- Configurable unfollow target, delays, and batch sizes
- Auto-retry on rate limit errors
- Cross-platform (Windows, macOS, Linux)
- Zero external dependencies (rich is optional for premium UI)
- Multiple auth methods (env var, file, git credential)

Usage:
    gh-unfollow [OPTIONS]

Examples:
    gh-unfollow                          # Unfollow 100 users
    gh-unfollow -n 500                   # Unfollow 500
    gh-unfollow --dry-run                # Preview mode
    gh-unfollow --whitelist user1,user2  # Skip specific users
    gh-unfollow --no-rich                # Basic terminal mode
    gh-unfollow --token ghp_xxxx         # Provide token directly
"""

__version__ = "2.1.0"
