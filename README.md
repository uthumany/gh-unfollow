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
  <a href="https://github.com/uthumany/gh-unfollow/blob/main/LICENSE"><img src="https://img.shields.io/github/license/uthumany/gh-unfollow?color=blue" alt="License"></a>
  <a href="https://github.com/uthumany/gh-unfollow"><img src="https://img.shields.io/github/stars/uthumany/gh-unfollow?style=social" alt="GitHub Stars"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+"></a>
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
| 📦 **Zero Dependencies** | Pure Python standard library — nothing to install beyond Python 3.8+ |
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

> ⚠️ **Never commit your token!** Always use environment variables or the `--token` flag.

---

## ⚙️ Options Reference

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--count` | `-n` | `100` | Number of users to unfollow (`0` = all) |
| `--delay` | `-d` | `2.0` | Seconds between individual unfollows |
| `--batch` | `-b` | `30` | Users per batch before a cooldown pause |
| `--batch-delay` | `-B` | `60` | Seconds to pause between batches |
| `--dry-run` | — | `false` | Preview without actually unfollowing |
| `--token` | — | — | GitHub personal access token |
| `--logfile` | — | `%TEMP%/gh-unfollow.log` | Custom log file path |
| `--version` | — | — | Print version and exit |
| `--help` | `-h` | — | Show help message |

---

## 🧠 Rate Limiting Strategy

| Parameter | Default | Purpose |
|-----------|---------|---------|
| Per-unfollow delay | 2s | Stays well under GitHub's 5000 req/hr limit |
| Batch size | 30 users | Groups unfollows for manageable pauses |
| Batch cooldown | 60s | Lets rate limit bucket refill |
| Auto-retry on 403 | ∞ | Waits 60 seconds, then retries the same user |
| Low-limit threshold | <100 remaining | Preemptive 60s pause to avoid hitting the hard cap |

**Sustained speed:** ~18 unfollows/minute  
**1000 unfollows:** ~50 minutes  

> Safe for accounts with up to 5000 users followed. For larger accounts, increase `--batch-delay` or decrease `--batch`.

---

## 🔧 How It Works

1. **Authenticate** using one of the four supported methods
2. **Fetch** the authenticated user's info (login name, total following count)
3. **Paginate** through the `/user/following` GitHub API endpoint (100 users per page)
4. **Unfollow** each user with a `DELETE` request to `/user/following/{username}`
5. **Rate-limit** between requests with configurable delays
6. **Log** every action to both stdout and a log file

### Architecture

```
gh-unfollow
├── bin/gh-unfollow          # Shell entry point (npm/npx compatible)
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
A: Yes. The tool implements proper rate limiting and auto-retry. Use `--dry-run` first to preview.

**Q: Does this require admin permissions?**  
A: No. You only need a personal access token with `user:follow` scope — same permissions as clicking "Unfollow" on the GitHub website.

**Q: Can I undo an unfollow?**  
A: No — unfollows are permanent. The tool does not store who you unfollowed (by design). Use `--dry-run` and save the log file if you want a record.

**Q: How long does it take to unfollow 1000 users?**  
A: ~50 minutes at default speed (2s delay, 30/batch, 60s cooldown). Use `--delay 1.0 -b 50 -B 30` for ~25 minutes.

**Q: What happens if I get rate limited?**  
A: The tool auto-detects 403 errors and low rate limits, waits 60 seconds, and retries. It will keep going until all targeted users are unfollowed.

**Q: Which Python versions are supported?**  
A: Python 3.8 through 3.13.

**Q: Does it work on Windows?**  
A: Yes! Fully tested on Windows 10/11, macOS, and Linux.

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
