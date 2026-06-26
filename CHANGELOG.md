# Changelog

All notable changes to `gh-unfollow` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-06-27

### Added
- 🚀 Initial release — bulk unfollow GitHub users
- ⚡ Smart rate limiting with configurable delays and batch pauses
- 🔄 Auto-retry on HTTP 403 rate limit errors
- 👁️ `--dry-run` mode to preview unfollows without executing
- 📊 Real-time progress logging to stdout and log file
- 🔐 Multiple auth methods: `--token` flag, `GITHUB_TOKEN` env var, token file, git credential store
- 🖥️ Cross-platform support (Windows, macOS, Linux)
- 📦 Zero external dependencies (Python stdlib only)
- 📦 Installable via npm, yarn, pnpm, bun, pip, uv
- 🧪 Comprehensive test suite with unit tests
- 📖 Full documentation: README, CHANGELOG, CONTRIBUTING guide
- 🏷️ GitHub issue and PR templates
- 🎨 ASCII banner for terminal aesthetic
