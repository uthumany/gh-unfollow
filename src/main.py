"""gh-unfollow — Bulk unfollow GitHub users with smart rate limiting.

Usage:
    gh-unfollow [OPTIONS]
    gh-unfollow -n 500 --delay 1.5
    gh-unfollow --dry-run

Environment Variables:
    GITHUB_TOKEN     GitHub personal access token (user:follow scope required)
    GH_UNFOLLOW_LOG  Custom log file path

Examples:
    gh-unfollow                          # Unfollow 100 users
    gh-unfollow -n 500                   # Unfollow 500 users
    gh-unfollow -n 0                     # Unfollow ALL users
    gh-unfollow --dry-run                # Preview mode (no actual unfollows)
    gh-unfollow --token ghp_xxxx         # Auth via CLI flag
    GITHUB_TOKEN=ghp_xxxx gh-unfollow    # Auth via env var
"""

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import timedelta

__version__ = "1.0.1"

LOGFILE = os.path.join(tempfile.gettempdir(), "gh-unfollow.log")
DRY_RUN = False


def log(msg: str) -> None:
    """Log a message to stdout and the log file."""
    line = f"{time.strftime('%H:%M:%S')}  {msg}"
    print(line, flush=True)
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except OSError:
        pass  # Log file write is best-effort


def banner() -> None:
    """Print the tool banner."""
    print(r"""
  ╔══════════════════════════════════════════╗
  ║           GH-UNFOLLOW  v{ver}            ║
  ║   Bulk Unfollow GitHub Users — Fast      ║
  ╚══════════════════════════════════════════╝
""".format(ver=__version__), flush=True)


def read_token(token_arg: str | None = None) -> str:
    """Read GitHub token from multiple sources.

    Priority:
    1. --token CLI argument
    2. GITHUB_TOKEN environment variable
    3. gh_token.txt in TEMP directory
    4. Git credential store (if available)
    """
    # 1. CLI argument
    if token_arg:
        log("Auth: using --token CLI argument")
        return token_arg.strip()

    # 2. Environment variable
    env_token = os.environ.get("GITHUB_TOKEN", "")
    if env_token:
        log("Auth: using GITHUB_TOKEN env var")
        return env_token.strip()

    # 3. Token file in temp directory
    token_paths = [
        os.path.join(tempfile.gettempdir(), "gh_token.txt"),
        "/tmp/gh_token.txt",
    ]
    for p in token_paths:
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8") as f:
                    token = f.read().strip()
                if token:
                    log(f"Auth: using token from {p}")
                    return token
            except OSError:
                continue

    # 4. Git credential store
    try:
        import subprocess

        proc = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in proc.stdout.split("\n"):
            if line.startswith("password="):
                token = line.split("=", 1)[1].strip()
                if token:
                    log("Auth: using token from git credential store")
                    return token
    except Exception:
        pass

    # No token found
    log("ERROR: No GitHub token found!")
    log("Provide a token via one of:")
    log("  1. --token CLI flag")
    log("  2. GITHUB_TOKEN environment variable")
    log("  3. Token file at %TEMP%/gh_token.txt")
    log("  4. Git credential store (git config credential.helper)")
    log("\nCreate a token at: https://github.com/settings/tokens")
    log("Required scope: user:follow (classic) or Followers:Read/Write (fine-grained)")
    sys.exit(1)


def api_request(token: str, method: str, url: str) -> tuple[int, str, bytes]:
    """Make an authenticated GitHub API request.

    Returns (status_code, rate_limit_remaining, response_body).
    """
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "gh-unfollow/{}".format(__version__))
    try:
        resp = urllib.request.urlopen(req)
        return (
            resp.status,
            resp.headers.get("X-RateLimit-Remaining", "?"),
            resp.read(),
        )
    except urllib.error.HTTPError as e:
        return (
            e.code,
            e.headers.get("X-RateLimit-Remaining", "?") if e.headers else "?",
            b"",
        )


def get_user_info(token: str) -> dict:
    """Fetch authenticated user info."""
    code, rem, body = api_request(token, "GET", "https://api.github.com/user")
    if code != 200:
        log(f"ERROR: Cannot fetch user info (HTTP {code})")
        log("Check your token permissions (user:follow scope required)")
        sys.exit(1)
    return json.loads(body)


def fetch_following_page(token: str, page: int) -> list[dict]:
    """Fetch one page of users you're following."""
    url = f"https://api.github.com/user/following?page={page}&per_page=100"
    code, rem, body = api_request(token, "GET", url)
    if code != 200:
        log(f"ERROR fetching page {page}: HTTP {code}")
        return []
    return json.loads(body)


def unfollow_user(token: str, username: str) -> tuple[int, str]:
    """Unfollow a single user. Returns (status_code, rate_limit_remaining)."""
    url = f"https://api.github.com/user/following/{username}"
    code, rem, _ = api_request(token, "DELETE", url)
    return code, rem


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        prog="gh-unfollow",
        description="Bulk unfollow GitHub users with smart rate limiting.",
        epilog="Repo: https://github.com/uthumany/gh-unfollow",
    )
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=100,
        help="Number of users to unfollow (0 = all, default: 100)",
    )
    p.add_argument(
        "-d",
        "--delay",
        type=float,
        default=2.0,
        help="Seconds between individual unfollows (default: 2.0)",
    )
    p.add_argument(
        "-b",
        "--batch",
        type=int,
        default=30,
        help="Users per batch before a cooldown pause (default: 30)",
    )
    p.add_argument(
        "-B",
        "--batch-delay",
        type=int,
        default=60,
        help="Seconds to pause between batches (default: 60)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview who would be unfollowed without actually unfollowing",
    )
    p.add_argument(
        "--token",
        type=str,
        default=None,
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    p.add_argument(
        "--logfile",
        type=str,
        default=None,
        help="Custom path for the progress log file",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"gh-unfollow {__version__}",
    )
    return p.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()

    global LOGFILE, DRY_RUN
    if args.logfile:
        LOGFILE = args.logfile
    DRY_RUN = args.dry_run

    banner()

    # Clear log file
    try:
        with open(LOGFILE, "w", encoding="utf-8") as f:
            f.write("")
    except OSError:
        pass

    # Auth
    token = read_token(args.token)

    # User info
    user = get_user_info(token)
    following_count = user.get("following", 0)
    log(f"Authenticated as: {user['login']}")
    log(f"Currently following: {following_count}")
    log(f"Rate limit remaining: checking...")

    target = args.count if args.count > 0 else following_count
    target = min(target, following_count)

    if DRY_RUN:
        log(f"\n{'='*50}")
        log(f"DRY RUN MODE — no actual unfollows will be performed")
        log(f"Would unfollow up to {target} users")
        log(f"{'='*50}\n")

    log(f"Target: {target} users")
    log(f"Delay: {args.delay}s | Batch: {args.batch} | Batch pause: {args.batch_delay}s")
    log(f"Estimated time: {_estimate_time(target, args.delay, args.batch, args.batch_delay)}")
    log(f"Log file: {LOGFILE}\n")

    if following_count == 0:
        log("You're not following anyone. Nothing to do!")
        return

    unfollowed = 0
    failures = 0
    page = 1
    seen_users: set[str] = set()
    start_time = time.time()

    while unfollowed < target:
        users = fetch_following_page(token, page)
        if not users:
            break

        log(f"Page {page}: {len(users)} users fetched")

        for u in users:
            if unfollowed >= target:
                break

            name = u["login"]

            # Skip already-processed users (dynamic list issue)
            if name in seen_users:
                continue
            seen_users.add(name)

            if DRY_RUN:
                unfollowed += 1
                log(f"  [{unfollowed}/{target}] Would unfollow: {name}")
                continue

            code, rem = unfollow_user(token, name)

            if code == 204:
                unfollowed += 1
                failures = 0
                log(f"  [{unfollowed}/{target}] Unfollowed {name}  (limit: {rem})")
            elif code == 403:
                log(f"  Rate limited! Waiting 60s before retry...")
                time.sleep(60)
                code2, rem2 = unfollow_user(token, name)
                if code2 == 204:
                    unfollowed += 1
                    log(f"  [{unfollowed}/{target}] Unfollowed {name} (retry ok)")
            elif code == 404:
                pass  # Already not following
            else:
                log(f"  HTTP {code} for {name}")
                failures += 1

            if failures >= 5:
                log("Too many consecutive failures. Stopping.")
                sys.exit(1)

            # Rate limit check
            try:
                r = int(rem)
            except (ValueError, TypeError):
                r = 5000
            if r < 100:
                log(f"  Low rate limit ({r}), waiting 60s...")
                time.sleep(60)
            else:
                time.sleep(args.delay)

            # Batch cooldown
            if unfollowed > 0 and unfollowed % args.batch == 0:
                log(f"  --- Batch of {args.batch} done, pausing {args.batch_delay}s ---")
                time.sleep(args.batch_delay)

        if len(users) < 100:
            break
        page += 1

    elapsed = time.time() - start_time
    td = str(timedelta(seconds=int(elapsed)))

    log(f"\n{'='*50}")
    if DRY_RUN:
        log(f"DONE: Would have unfollowed {unfollowed} users")
    else:
        log(f"DONE: Unfollowed {unfollowed} users in {td}")
    log(f"Log saved to: {LOGFILE}")
    log(f"{'='*50}")


def _estimate_time(
    target: int, delay: float, batch: int, batch_delay: int
) -> str:
    """Estimate total run time."""
    batches = target // batch
    total = (target * delay) + (batches * batch_delay)
    if total < 60:
        return f"~{int(total)}s"
    elif total < 3600:
        return f"~{int(total / 60)}m {int(total % 60)}s"
    else:
        hours = int(total // 3600)
        minutes = int((total % 3600) // 60)
        return f"~{hours}h {minutes}m"


if __name__ == "__main__":
    main()
