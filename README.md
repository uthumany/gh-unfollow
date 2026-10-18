<!-- SEO: gh-unfollow — bulk unfollow GitHub users, mass unfollow github, clean github following, github unfollow tool, github following cleanup, batch unfollow github, unfollow everyone github -->

<h1 align="center">
  <code>gh-unfollow</code>
</h1>

<p align="center">
  <strong>Bulk Unfollow GitHub Users — Fast. Smart. Zero Dependencies.</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/gh-unfollow"><img src="https://img.shields.io/npm/v/gh-unfollow?color=cb0000&label=npm" alt="npm version"></a>
  <a href="https://pypi.org/project/gh-unfollow/"><img src="https://img.shields.io/pypi/v/gh-unfollow?color=3775A9&label=pypi" alt="PyPI version"></a>
  <a href="https://github.com/uthumany/gh-unfollow/blob/master/LICENSE"><img src="https://img.shields.io/github/license/uthumany/gh-unfollow?color=blue" alt="License"></a>
  <a href="https://github.com/uthumany/gh-unfollow"><img src="https://img.shields.io/github/stars/uthumany/gh-unfollow?style=social" alt="GitHub Stars"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
  <a href="#"><img src="https://img.shields.io/badge/dependencies-0-green" alt="Zero Dependencies"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey" alt="Platforms"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/install-npm-cb0000?logo=npm" alt="npm">
  <img src="https://img.shields.io/badge/install-yarn-2C8EBB?logo=yarn" alt="yarn">
  <img src="https://img.shields.io/badge/install-pnpm-F69220?logo=pnpm" alt="pnpm">
  <img src="https://img.shields.io/badge/install-bun-000000?logo=bun" alt="bun">
  <img src="https://img.shields.io/badge/install-pip-3775A9?logo=pypi" alt="pip">
  <img src="https://img.shields.io/badge/install-uv-DE4BFC?logo=python" alt="uv">
</p>

---

## 📖 Table of Contents
- [What is gh-unfollow?](#-what-is-gh-unfollow)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage & Examples](#-usage--examples)
- [Authentication](#-authentication)
- [Options Reference](#-options-reference)
- [Rate Limiting Strategy](#-rate-limiting-strategy)
- [How It Works](#-how-it-works)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔥 What is gh-unfollow?

**gh-unfollow** is a blazing-fast CLI tool to **bulk unfollow GitHub users** with intelligent rate limiting, automatic retry on failures, and cross-platform support. Clean up your GitHub following list from thousands to zero in minutes.

> **Perfect for:** developers who followed too many people over the years, bots that need GitHub following cleanup, or anyone who wants a fresh start on their GitHub social graph.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ⚡ **Bulk Unfollow** | Unfollow hundreds or thousands of users in a single run |
| 🧠 **Smart Rate Limiting** | Configurable delays, batch pauses, and auto-retry on 403 errors |
| 👁️ **Dry-Run Mode** | Preview who you'd unfollow without actually unfollowing |
| 🔐 **Multiple Auth Methods** | CLI flag, env var, token file, or git credential store |
| 🖥️ **Cross-Platform** | Windows, macOS, and Linux — all supported |
| 📦 **Zero Dependencies** | Pure Python standard library — nothing to install beyond Python 3.10+ |
| 📊 **Real-Time Progress** | See every unfollow as it happens, with estimated time remaining |
| 📝 **Detailed Logging** | Full log file saved for audit and review |
| 🔄 **Auto-Retry** | Automatically retries after rate limit cooldowns |
| 🎨 **Beautiful Terminal UI** | ASCII banner and formatted output for a premium CLI experience |

---

## 🚀 Quick Start

```bash
# Install globally via npm (recommended)
npm install -g gh-unfollow

# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Unfollow 100 users (default)
gh-unfollow

# Unfollow 500 users with custom speed
gh-unfollow -n 500 --delay 1.5

# Preview without unfollowing (dry-run)
gh-unfollow --dry-run
```

---

## 📦 Installation

### npm (recommended)
```bash
npm install -g gh-unfollow
```

### yarn
```bash
yarn global add gh-unfollow
```

### pnpm
```bash
pnpm add -g gh-unfollow
```

### bun
```bash
bun add -g gh-unfollow
```

### pip / uv
```bash
pip install gh-unfollow
# or
uv pip install gh-unfollow
```

### npx / bunx (one-off)
```bash
npx gh-unfollow --dry-run
bunx gh-unfollow -n 500
```

The npm package is a thin cross-platform launcher; it requires **Node.js 14+** and
**Python 3.10+**. It does not install Python for you. The launcher resolves the
bundled Python entry point from the installed package, including npm's symlinked
`.bin` layout.

### From Source
```bash
git clone https://github.com/uthumany/gh-unfollow.git
cd gh-unfollow
pip install -e .
gh-unfollow --version
```

---

## 📋 Usage & Examples

### Basic Usage

```bash
# Unfollow 100 users (default)
gh-unfollow

# Unfollow a specific number
gh-unfollow -n 500

# Unfollow ALL users you're following
gh-unfollow -n 0

# Dry-run — preview only, no actual unfollows
gh-unfollow --dry-run

# Fast mode — 1 second between unfollows
gh-unfollow --delay 1.0 -b 50 -B 30

# Slow & safe — 5 seconds between unfollows
gh-unfollow --delay 5 -b 10 -B 120
```

### With Authentication

```bash
# Env var (recommended for CI/CD)
export GITHUB_TOKEN="github_pat_..."
gh-unfollow

# CLI flag
gh-unfollow --token "ghp_your_token_here"

# Token file
echo "ghp_your_token_here" > /tmp/gh_token.txt
gh-unfollow

# Git credential store (auto-detected)
git config --global credential.helper store
gh-unfollow
```

### Output Example

```
  ╔══════════════════════════════════════════╗
  ║           GH-UNFOLLOW  v1.0.0            ║
  ║   Bulk Unfollow GitHub Users — Fast      ║
  ╚══════════════════════════════════════════╝

17:02:03  Authenticated as: octocat
17:02:03  Currently following: 847
17:02:03  Target: 500 users
17:02:03  Delay: 2.0s | Batch: 30 | Batch pause: 60s
17:02:03  Estimated time: ~20m 40s
17:02:03
17:02:05  Page 1: 100 users fetched
17:02:07    [1/500] Unfollowed user1  (limit: 4998)
17:02:09    [2/500] Unfollowed user2  (limit: 4997)
...
17:22:45  ==================================================
17:22:45  DONE: Unfollowed 500 users in 20m 42s
17:22:45  ==================================================
```

---

## 🔐 Authentication

gh-unfollow supports **four authentication methods**, checked in this order:

| Priority | Method | Setup |
|----------|--------|-------|
| 1 | `--token` CLI flag | `gh-unfollow --token ghp_xxx` |
| 2 | `GITHUB_TOKEN` env var | `export GITHUB_TOKEN=ghp_xxx` |
| 3 | Token file | `echo "ghp_xxx" > %TEMP%/gh_token.txt` |
| 4 | Git credential store | `git credential fill` auto-detect |

### Token Requirements

You need a GitHub personal access token with the **`user:follow`** scope:

- **Classic PAT:** [Create token](https://github.com/settings/tokens) → check `user:follow`
- **Fine-grained PAT:** [Create token](https://github.com/settings/personal-access-tokens/new) → select "Followers" → "Read and Write"

> **Credential safety:** prefer `GITHUB_TOKEN` over `--token`, which can appear
> in shell history or process listings. Never commit a token.

A connected GitHub integration may allow repository access while lacking account
Followers permissions. If `/user/following` returns 403 "Resource not accessible by
integration", use a credential with Followers read access for previews/backups and
read/write for unfollow/restore. Repository administration alone is not enough.

Public activity is incomplete: GitHub only exposes a limited events history, and
private activity is not visible. `--inactive-days` keeps users whose activity is
unknown; an empty feed is not evidence that an account is inactive.

---

## ⚙️ Options Reference

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--count` | `-n` | `100` | Number of users to unfollow (`0` = all) |
| `--delay` | `-d` | `2.0` | Seconds between individual unfollows |
| `--batch` | `-b` | `30` | Users per batch before a cooldown pause |
| `--batch-delay` | `-B` | `60` | Seconds to pause between batches |
| `--dry-run` | — | `false` | Preview unfollow or restore without changing relationships |
| `--token` | — | — | GitHub personal access token |
| `--logfile` | — | `%TEMP%/gh-unfollow.log` | Custom log file path |
| `--whitelist` | — | empty | Comma-separated usernames to keep (case-insensitive) |
| `--whitelist-file` | — | empty | One username per line; blank lines/comments ignored |
| `--inactive-days` | — | `0` | Select users with an observed public event older than N days; unknown activity is kept |
| `--non-mutual` | — | `false` | Keep people who follow you back |
| `--interactive` | — | `false` | Choose from the filtered list, then apply count and pacing |
| `--backup` | — | empty | Atomically export the complete following list to JSON |
| `--restore` | — | empty | Re-follow usernames from a validated backup; supports dry-run |
| `--no-rich` / `--no-color` | — | `false` | Use plain terminal output |
| `--version` | — | — | Print version and exit |
| `--help` | `-h` | — | Show help message |

---

## 🧠 Rate Limiting Strategy

| Parameter | Default | Purpose |
|-----------|---------|---------|
| Per-unfollow delay | 2s | Stays well under GitHub's 5000 req/hr limit |
| Batch size | 30 users | Groups unfollows for manageable pauses |
| Batch cooldown | 60s | Lets rate limit bucket refill |
| Rate-limit retries | 3 attempts per user | Honor Retry-After/reset headers when supplied; otherwise back off |
| Permission errors | Stop | A permission-denied 403 is not treated as a rate limit |
| Network/read errors | Stop | Failed reads never become empty lists or successful backups |

Actual throughput depends on GitHub's primary and secondary rate limits. No
configuration guarantees that a large cleanup will complete without interruption.
A run can stop after partial completion: review its output and log before retrying.

---

## 🔧 How It Works

1. **Authenticate** using one of the four supported methods
2. **Fetch** the authenticated user's info (login name, total following count)
3. **Snapshot** every page of `/user/following` before any deletion, so removing users cannot shift later pages
4. **Filter and select**, applying the requested count after exclusions; then **unfollow** each user with a `DELETE` request to `/user/following/{username}`
5. **Rate-limit** between requests with configurable delays
6. **Log** every action to both stdout and a log file

### Architecture

```
gh-unfollow
├── bin/gh-unfollow.js       # Cross-platform Node entry point (npm/npx compatible)
├── src/
│   ├── __init__.py          # Package metadata
│   └── main.py              # Core CLI logic (stdlib only)
├── tests/
│   └── test_unfollow.py     # Comprehensive test suite
├── package.json             # npm/yarn/pnpm/bun manifest
├── pyproject.toml           # Python build config (pip/uv)
├── setup.py / setup.cfg     # Legacy pip support
└── MANIFEST.in              # Distribution file list
```

---

## ❓ FAQ

**Q: Is this safe to use?**  
A: It is a destructive tool: unfollows cannot be undone automatically. Review a
`--dry-run` result first, keep the default pacing unless you understand the
trade-off, and stop if the API reports an unexpected failure. The tool does not
promise recovery from every network or API error.

**Q: Does this require admin permissions?**  
A: No. You only need a personal access token with `user:follow` scope — same permissions as clicking "Unfollow" on the GitHub website.

**Q: Can I undo an unfollow?**  
A: Export first with `gh-unfollow --backup following.json`. You can later preview re-following with `gh-unfollow --restore following.json --dry-run`, then restore without `--dry-run`. This creates new follows; it cannot restore historical relationship metadata or guarantee that deleted/unavailable accounts can be followed.

**Q: How long does it take to unfollow 1000 users?**  
A: Timing varies with API latency and rate limits; roughly an hour at default pacing (2s delay, 30/batch, 60s cooldown). Use `--delay 1.0 -b 50 -B 30` for ~25 minutes.

**Q: What happens if I get rate limited?**  
A: The tool applies configured pacing and handles supported rate-limit responses.
Review the output and log after any interruption; do not assume that every
network or API failure was retried or completed.

**Q: Which Python versions are supported?**  
A: Python 3.10+ is required; CI covers 3.10 through 3.13.

**Q: Does it work on Windows?**  
A: The npm launcher supports Windows through `py -3` or `python`; it requires Python 3.10+. CI includes launcher smoke checks on Windows, macOS, and Linux. These smoke checks do not perform live follows or unfollows.

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

```bash
git clone https://github.com/uthumany/gh-unfollow.git
cd gh-unfollow
pip install -e ".[dev]"
python -m pytest tests/ -v
```

---

## 📄 License

MIT © 2026 [Uthuman & Co](https://uthuman.com)

---

<p align="center">
  <sub>Built with ❤️ by <a href="https://uthuman.com">Uthuman & Co</a></sub>
</p>
