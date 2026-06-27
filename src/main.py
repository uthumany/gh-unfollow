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
    GITHUB_TOKEN=*** gh-unfollow    # Auth via env var
    gh-unfollow --whitelist user1,user2  # Skip specific users
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

# Add parent to path for direct execution
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui import UI, check_rich_available, Colors

__version__ = "2.3.0"

LOGFILE = os.path.join(tempfile.gettempdir(), "gh-unfollow.log")


# ─── Logging ────────────────────────────────────────────────────────────────


def file_log(msg: str) -> None:
    """Write a message to the log file only (not stdout)."""
    line = f"{time.strftime('%H:%M:%S')}  {msg}"
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
    except OSError:
        pass


# ─── Auth ───────────────────────────────────────────────────────────────────


def read_token(token_arg: str | None = None, ui: UI | None = None) -> str:
    """Read GitHub token from multiple sources.

    Priority:
    1. --token CLI argument
    2. GITHUB_TOKEN environment variable
    3. gh_token.txt in TEMP directory
    4. Git credential store (if available)
    """
    _log = ui.log_error if ui else lambda m: print(f"ERROR: {m}")

    # 1. CLI argument
    if token_arg:
        file_log("Auth: using --token CLI argument")
        return token_arg.strip()

    # 2. Environment variable
    env_token = os.environ.get("GITHUB_TOKEN", "")
    if env_token:
        file_log("Auth: using GITHUB_TOKEN env var")
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
                    file_log(f"Auth: using token from {p}")
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
                    file_log("Auth: using token from git credential store")
                    return token
    except Exception:
        pass

    # No token found
    _log("No GitHub token found!")
    _log("Provide a token via one of:")
    _log("  1. --token CLI flag")
    _log("  2. GITHUB_TOKEN environment variable")
    _log("  3. Token file at %TEMP%/gh_token.txt")
    _log("  4. Git credential store (git config credential.helper)")
    _log("\nCreate a token at: https://github.com/settings/tokens")
    _log("Required scope: user:follow (classic) or Followers:Read/Write (fine-grained)")
    sys.exit(1)


# ─── API ────────────────────────────────────────────────────────────────────


def api_request(token: str, method: str, url: str) -> tuple[int, str, bytes]:
    """Make an authenticated GitHub API request."""
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", f"gh-unfollow/{__version__}")
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
    code, _rem, body = api_request(token, "GET", "https://api.github.com/user")
    if code != 200:
        print(f"ERROR: Cannot fetch user info (HTTP {code})")
        print("Check your token permissions (user:follow scope required)")
        sys.exit(1)
    return json.loads(body)


def fetch_following_page(token: str, page: int) -> tuple[list[dict], str]:
    """Fetch one page of users you're following. Returns (users, rate_limit)."""
    url = f"https://api.github.com/user/following?page={page}&per_page=100"
    code, rem, body = api_request(token, "GET", url)
    if code != 200:
        return [], rem
    return json.loads(body), rem


def unfollow_user(token: str, username: str) -> tuple[int, str]:
    """Unfollow a single user. Returns (status_code, rate_limit_remaining)."""
    url = f"https://api.github.com/user/following/{username}"
    code, rem, _ = api_request(token, "DELETE", url)
    return code, rem


# ─── CLI Args ───────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        prog="gh-unfollow",
        description="Bulk unfollow GitHub users with smart rate limiting.",
        epilog="Repo: https://github.com/uthumany/gh-unfollow",
    )
    p.add_argument(
        "-n", "--count", type=int, default=100,
        help="Number of users to unfollow (0 = all, default: 100)",
    )
    p.add_argument(
        "-d", "--delay", type=float, default=2.0,
        help="Seconds between individual unfollows (default: 2.0)",
    )
    p.add_argument(
        "-b", "--batch", type=int, default=30,
        help="Users per batch before a cooldown pause (default: 30)",
    )
    p.add_argument(
        "-B", "--batch-delay", type=int, default=60,
        help="Seconds to pause between batches (default: 60)",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Preview who would be unfollowed without actually unfollowing",
    )
    p.add_argument(
        "--token", type=str, default=None,
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    p.add_argument(
        "--logfile", type=str, default=None,
        help="Custom path for the progress log file",
    )
    p.add_argument(
        "--whitelist", type=str, default="",
        help="Comma-separated list of usernames to NEVER unfollow",
    )
    p.add_argument(
        "--whitelist-file", type=str, default="",
        help="File with one username per line to NEVER unfollow",
    )
    p.add_argument(
        "--inactive-days", type=int, default=0,
        help="Only unfollow users inactive for more than N days",
    )
    p.add_argument(
        "--non-mutual", action="store_true",
        help="Only unfollow users who don't follow you back",
    )
    p.add_argument(
        "--interactive", action="store_true",
        help="Manually select who to unfollow from an interactive menu",
    )
    p.add_argument(
        "--backup", type=str, default="",
        help="Export following list to JSON file (bypasses unfollow)",
    )
    p.add_argument(
        "--restore", type=str, default="",
        help="Re-follow users from a backup JSON file (bypasses unfollow)",
    )
    p.add_argument(
        "--no-rich", action="store_true",
        help="Disable rich terminal UI (use basic mode)",
    )
    p.add_argument(
        "--no-color", action="store_true",
        help="Disable all ANSI colors in output",
    )
    p.add_argument(
        "--version", action="version", version=f"gh-unfollow {__version__}",
    )
    return p.parse_args()


# ─── Feature: Whitelist from File ───────────────────────────────────────────


def load_whitelist_file(filepath: str) -> list[str]:
    """Load whitelist usernames from a file (one per line)."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        file_log(f"Whitelist file not found: {filepath}")
        print(f"ERROR: Whitelist file not found: {filepath}")
        sys.exit(1)
    except OSError as e:
        file_log(f"Error reading whitelist file: {e}")
        print(f"ERROR: Cannot read whitelist file: {e}")
        sys.exit(1)


# ─── Feature: Inactive User Cleanup ─────────────────────────────────────────


def check_inactive(token: str, username: str) -> tuple[bool, str]:
    """Check if a user has been inactive for the specified days.
    Returns (is_inactive, last_active_date_or_error).
    """
    url = f"https://api.github.com/users/{username}/events/public?per_page=1"
    code, _rem, body = api_request(token, "GET", url)
    if code != 200:
        return True, "api error"  # Treat API errors as inactive (unfollow)
    events = json.loads(body)
    if not events:
        return True, "no public events"
    try:
        last_active = events[0]["created_at"]
        return False, last_active  # Has activity
    except (KeyError, IndexError):
        return True, "unknown"


def filter_inactive(
    token: str, users: list[dict], days: int, ui: UI
) -> list[dict]:
    """Filter users to only those inactive for more than `days`."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - (days * 86400)
    inactive: list[dict] = []
    active_count = 0

    for i, u in enumerate(users):
        name = u["login"]
        ui.update_dashboard(0, f"Checking activity: {name}", "?")
        is_inactive, last = check_inactive(token, name)

        if is_inactive:
            inactive.append(u)
            file_log(f"INACTIVE {name} (last: {last})")
        else:
            active_count += 1
            try:
                last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                days_ago = int((now - last_dt).total_seconds() / 86400)
                ui.log_skip(name, f"Active ({days_ago}d ago)")
            except Exception:
                ui.log_skip(name, "Active")
            file_log(f"ACTIVE {name} (keeping)")

        # Rate-limit between activity checks
        if i < len(users) - 1:
            time.sleep(0.5)  # Gentle delay between event queries

    ui.log_warn(f"Filtered: {len(inactive)} inactive, {active_count} active (kept)")
    return inactive


# ─── Feature: Non-Mutual Unfollow ───────────────────────────────────────────


def fetch_followers(token: str, ui: UI) -> set[str]:
    """Fetch all followers and return a set of usernames."""
    followers: set[str] = set()
    page = 1
    ui.log_warn("Fetching your followers list...")
    while True:
        url = f"https://api.github.com/user/followers?page={page}&per_page=100"
        code, _rem, body = api_request(token, "GET", url)
        if code != 200:
            break
        batch = json.loads(body)
        if not batch:
            break
        for u in batch:
            followers.add(u["login"])
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.3)
    file_log(f"Followers fetched: {len(followers)}")
    ui.log_warn(f"Found {len(followers)} followers")
    return followers


# ─── Feature: Interactive Selection Mode ────────────────────────────────────


def interactive_select(
    users: list[dict], ui: UI
) -> list[dict]:
    """Let the user interactively select who to unfollow. Returns selected users."""
    selected: list[dict] = []
    batch_size = 50

    for i in range(0, len(users), batch_size):
        batch = users[i : i + batch_size]
        print(f"\n  Batch {i // batch_size + 1}: {len(batch)} users")
        print(f"  {'─' * 50}")
        for j, u in enumerate(batch):
            print(f"  [{Colors.CYAN}{i + j + 1:>3}{Colors.RESET}] @{u['login']}")

        print(f"\n  Enter numbers to unfollow (e.g. 1,3,5-8), 'all', or 'none': ", end="")
        try:
            choice = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            choice = "none"

        if choice == "all":
            selected.extend(batch)
        elif choice == "none":
            continue
        else:
            try:
                indices = _parse_range(choice, i)
                for idx in indices:
                    if 0 <= idx - i - 1 < len(batch):
                        selected.append(batch[idx - i - 1])
            except ValueError:
                print(f"  {Colors.RED}Invalid input. Skipping batch.{Colors.RESET}")

    print(f"\n  Selected {len(selected)} users to unfollow.\n")
    return selected


def _parse_range(spec: str, offset: int) -> list[int]:
    """Parse '1,3,5-8' into a list of int indices."""
    indices: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            indices.extend(range(int(a.strip()), int(b.strip()) + 1))
        else:
            indices.append(int(part))
    return indices


# ─── Feature: Backup & Restore ──────────────────────────────────────────────


def cmd_backup(token: str, filepath: str, ui: UI) -> None:
    """Export the full following list to a JSON file."""
    from datetime import datetime, timezone

    ui.log_warn("Backing up following list...")
    users = []
    page = 1
    while True:
        batch, _rem = fetch_following_page(token, page)
        if not batch:
            break
        for u in batch:
            users.append(u["login"])
        ui.update_dashboard(len(users), f"Backed up {len(users)} users", "?")
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.5)

    backup = {
        "version": 1,
        "date": datetime.now(timezone.utc).isoformat(),
        "source": "gh-unfollow",
        "count": len(users),
        "users": users,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2)

    ui.log_final(len(users), "0s")
    file_log(f"Backup saved: {filepath} ({len(users)} users)")


def cmd_restore(token: str, filepath: str, ui: UI, delay: float, batch: int, batch_delay: int) -> None:
    """Re-follow users from a backup JSON file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            backup = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        ui.log_error(f"Cannot read backup file: {e}")
        sys.exit(1)

    users = backup.get("users", [])
    total = len(users)
    ui.log_warn(f"Restoring {total} users from backup...")
    ui.start_dashboard(total, "?")

    restored = 0
    for i, username in enumerate(users):
        url = f"https://api.github.com/user/following/{username}"
        code, rem, _ = api_request(token, "PUT", url)
        if code == 204:
            restored += 1
            ui.log_unfollow(restored, total, username, rem)
            ui.update_dashboard(restored, f"Re-followed {username}", rem)
        elif code == 403:
            ui.log_rate_limit(0)
            ui.cooldown(60, "Rate limit hit — retrying")
            code2, rem2, _ = api_request(token, "PUT", url)
            if code2 == 204:
                restored += 1
                ui.update_dashboard(restored, f"Re-followed {username}", rem2)
        else:
            ui.log_error(f"HTTP {code} for @{username}")
        time.sleep(delay)
        if restored > 0 and restored % batch == 0:
            ui.cooldown(batch_delay, f"Batch of {batch} done")

    ui.stop_dashboard()
    td = str(timedelta(seconds=0))
    ui.log_final(restored, td)
    file_log(f"Restored {restored}/{total} users from {filepath}")


# ─── Main ───────────────────────────────────────────────────────────────────


def main() -> None:
    """Entry point."""
    args = parse_args()

    global LOGFILE
    if args.logfile:
        LOGFILE = args.logfile

    # Parse whitelist
    whitelist = [w.strip() for w in args.whitelist.split(",") if w.strip()]
    if args.whitelist_file:
        whitelist.extend(load_whitelist_file(args.whitelist_file))

    # Initialize UI
    ui = UI(
        version=__version__,
        dry_run=args.dry_run,
        no_color=args.no_color or args.no_rich,
        whitelist=whitelist,
    )

    if args.no_rich and check_rich_available():
        file_log("Rich UI disabled via --no-rich flag")

    # Show banner
    ui.show_banner()

    # Clear log file
    try:
        with open(LOGFILE, "w", encoding="utf-8") as f:
            f.write("")
    except OSError:
        pass

    # Auth
    token = read_token(args.token, ui)

    # ── Backup mode (bypasses unfollow) ─────────────────────────────────
    if args.backup:
        cmd_backup(token, args.backup, ui)
        return

    # ── Restore mode (bypasses unfollow) ────────────────────────────────
    if args.restore:
        cmd_restore(token, args.restore, ui, args.delay, args.batch, args.batch_delay)
        return

    # User info
    user = get_user_info(token)
    following_count = user.get("following", 0)
    ui.log_auth(user["login"], following_count)

    target = args.count if args.count > 0 else following_count
    target = min(target, following_count)

    eta = _estimate_time(target, args.delay, args.batch, args.batch_delay)
    ui.log_target(target, args.delay, args.batch, args.batch_delay, eta)
    file_log(f"Target: {target} | ETA: {eta} | Log: {LOGFILE}")

    if following_count == 0:
        ui.log_final(0, "0s")
        return

    # ── Feature: Non-mutual mode ────────────────────────────────────────
    followers_set: set[str] = set()
    if args.non_mutual:
        followers_set = fetch_followers(token, ui)

    # Start dashboard
    ui.start_dashboard(target, "?")

    unfollowed = 0
    skipped = 0
    failures = 0
    page = 1
    seen_users: set[str] = set()
    start_time = time.time()

    # ── Feature: Interactive mode — collect full following list first ────
    if args.interactive:
        ui.log_warn("Fetching full following list for interactive selection...")
        all_users: list[dict] = []
        ip = 1
        while True:
            batch, _rem = fetch_following_page(token, ip)
            if not batch:
                break
            all_users.extend(batch)
            if len(batch) < 100:
                break
            ip += 1
            time.sleep(0.3)
        # Apply non-mutual filter if enabled
        if args.non_mutual:
            all_users = [u for u in all_users if u["login"] not in followers_set]
            ui.log_warn(f"After non-mutual filter: {len(all_users)} users")
        selected = interactive_select(all_users, ui)
        # Directly unfollow the selected users
        for u in selected[:target] if not args.dry_run else selected:
            name = u["login"]
            if ui.is_whitelisted(name):
                skipped += 1
                ui.log_skip(name)
                continue
            if args.dry_run:
                unfollowed += 1
                ui.log_unfollow(unfollowed, len(selected), name, "?")
                ui.update_dashboard(unfollowed, f"[SIM] {name}", "?")
                continue
            code, rem = unfollow_user(token, name)
            if code == 204:
                unfollowed += 1
                ui.log_unfollow(unfollowed, len(selected), name, rem)
                ui.update_dashboard(unfollowed, name, rem)
        ui.stop_dashboard()
        elapsed = time.time() - start_time
        ui.log_final(unfollowed, str(timedelta(seconds=int(elapsed))))
        return

    while unfollowed < target:
        users, rem = fetch_following_page(token, page)
        if not users:
            break

        # ── Feature: Inactive filter ────────────────────────────────────
        if args.inactive_days > 0:
            users = filter_inactive(token, users, args.inactive_days, ui)

        ui.log_page(page, len(users), rem)
        file_log(f"Page {page}: {len(users)} fetched (limit: {rem})")

        for u in users:
            if unfollowed + skipped >= target and not args.dry_run:
                break
            if unfollowed >= target:
                break

            name = u["login"]

            if name in seen_users:
                continue
            seen_users.add(name)

            # Check whitelist
            if ui.is_whitelisted(name):
                skipped += 1
                ui.log_skip(name)
                file_log(f"SKIP {name} (whitelisted)")
                continue

            # ── Feature: Non-mutual filter ──────────────────────────────
            if args.non_mutual and name in followers_set:
                skipped += 1
                ui.log_skip(name, "Mutual — kept")
                file_log(f"SKIP {name} (mutual)")
                continue

            if args.dry_run:
                unfollowed += 1
                ui.log_unfollow(unfollowed, target, name, rem)
                ui.update_dashboard(unfollowed, f"[SIM] {name}", rem)
                file_log(f"SIM {name}")
                continue

            code, rem = unfollow_user(token, name)

            if code == 204:
                unfollowed += 1
                failures = 0
                ui.log_unfollow(unfollowed, target, name, rem)
                ui.update_dashboard(unfollowed, name, rem)
                file_log(f"OK {name} (limit: {rem})")
            elif code == 403:
                ui.log_rate_limit(0)
                file_log(f"RATE-LIMIT retrying {name}")
                ui.cooldown(60, "Rate limit hit — retrying")
                code2, rem2 = unfollow_user(token, name)
                if code2 == 204:
                    unfollowed += 1
                    ui.log_unfollow(unfollowed, target, name, rem2)
                    ui.update_dashboard(unfollowed, name, rem2)
                    file_log(f"OK {name} (retry)")
            elif code == 404:
                file_log(f"NOP {name} (already not following)")
                pass
            else:
                ui.log_error(f"HTTP {code} for @{name}")
                file_log(f"ERR {name} HTTP {code}")
                failures += 1

            if failures >= 5:
                ui.log_error("Too many consecutive failures. Stopping.")
                file_log("STOP: too many failures")
                ui.stop_dashboard()
                sys.exit(1)

            # Rate limit check
            try:
                r = int(rem)
            except (ValueError, TypeError):
                r = 5000
            if r < 100:
                ui.log_rate_limit(r)
                file_log(f"LOW-LIMIT {r}, pausing 60s")
                time.sleep(60)
            else:
                time.sleep(args.delay)

            # Batch cooldown
            if unfollowed > 0 and unfollowed % args.batch == 0:
                file_log(f"BATCH cooldown {args.batch_delay}s")
                ui.cooldown(args.batch_delay, f"Batch of {args.batch} done")

        if len(users) < 100:
            break
        page += 1

    ui.stop_dashboard()

    elapsed = time.time() - start_time
    td = str(timedelta(seconds=int(elapsed)))

    total = unfollowed + skipped
    ui.log_final(unfollowed, td)
    if skipped > 0:
        file_log(f"DONE: {unfollowed} unfollowed, {skipped} skipped (whitelist) in {td}")
    else:
        file_log(f"DONE: {unfollowed} unfollowed in {td}")
    file_log(f"Log saved: {LOGFILE}")


def _estimate_time(target: int, delay: float, batch: int, batch_delay: int) -> str:
    """Estimate total run time."""
    batches = target // batch if batch > 0 else 0
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
