# Changelog

## [2.3.1] - 2026-10-18

### Fixed
- Snapshot the complete following list before selection or mutation; count only eligible users.
- Fail closed on incomplete API reads, invalid responses, permission errors and network failures.
- Respect inactivity thresholds while keeping accounts with unknown public activity.
- Validate backup data, write backups atomically and honor restore dry-runs.
- Share paced execution across modes and bound genuine rate-limit retries.
- Use a cross-platform Node launcher and clean npm package contents.

### Compatibility
- Python 3.10+ is required; Node.js 14+ is required for the npm launcher.
- No live follow/unfollow mutation has been validated with the connected credential.


All notable changes to `gh-unfollow` will be documented in this file.

---

## [2.0.0] — 2026-06-27

### Added
- 🎨 **Premium terminal UI** with Rich library (optional — falls back to basic mode)
- 🖼️ ASCII FIGlet banner with cyan theming
- 📊 Live progress dashboard with animated spinners, progress bar, elapsed/ETA
- 🎨 Color-coded output: green (success), yellow (warning/rate-limit), red (error), cyan (banner)
- ⏳ Animated cooldown countdown bar for rate-limit and batch pauses
- 🟣 Dry-run mode with distinct magenta/purple theme and warnings
- 🛡️ `--whitelist` flag to protect specific users from unfollow
- 🔧 `--no-rich` flag to force basic terminal mode
- 🎯 `--no-color` flag to disable all ANSI colors
- 📦 `pip install gh-unfollow[ui]` for premium UI dependencies

### Changed
- Complete UI rewrite with modular `src/ui.py`
- Version bumped to 2.0.0 (breaking visual change, API unchanged)

---

## [1.0.1] — 2026-06-27

### Fixed
- Fixed npm bin paths for proper global install

## [1.0.0] — 2026-06-27

### Added
- 🚀 Initial release — bulk unfollow GitHub users
- ⚡ Smart rate limiting with configurable delays and batch pauses
- 🔄 Auto-retry on HTTP 403 rate limit errors
- 👁️ `--dry-run` mode to preview unfollows without executing
- 📊 Real-time progress logging to stdout and log file
- 🔐 Multiple auth methods
- 🖥️ Cross-platform support
- 📦 Zero external dependencies
- 📦 Installable via npm, yarn, pnpm, bun, pip, uv
