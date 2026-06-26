"""gh-unfollow — Bulk unfollow GitHub users with smart rate limiting.

CLI tool to mass-unfollow GitHub users. Features:
- Configurable unfollow target count
- Intelligent rate limiting with batch pauses
- Auto-retry on rate limit errors
- Progress logging with real-time output
- Cross-platform (Windows, macOS, Linux)
- Zero external dependencies (stdlib only)
- Multiple auth methods (env var, file, git credential)

Usage:
    gh-unfollow [OPTIONS]

Examples:
    gh-unfollow                          # Unfollow 100 users (default)
    gh-unfollow -n 500                   # Unfollow 500 users
    gh-unfollow -n 1000 --delay 1.5      # Faster unfollows
    gh-unfollow --dry-run                # Preview who you'd unfollow
    gh-unfollow --token ghp_xxxx         # Provide token directly
"""

__version__ = "1.0.1"
