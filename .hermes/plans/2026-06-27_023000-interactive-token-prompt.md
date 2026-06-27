# Interactive Token Input Feature — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** When `gh-unfollow` is run without a token, interactively prompt the user to paste their `GITHUB_TOKEN` with masked input, validate it against the GitHub API, and optionally persist it for future sessions.

**Architecture:** Add a new `prompt_token()` function in main.py that falls through to interactive input after all existing auto-detection methods fail. Use `getpass.getpass()` for masked input (cross-platform), validate via a `GET /user` API call, and offer to save to `%TEMP%/gh_token.txt` with user consent. Add new UI methods to `ui.py` for the prompt display. TTY-aware — if stdin is piped, skip interactive prompt and show the existing error message.

**Tech Stack:** Python 3.8+ stdlib (`getpass`, `os`, `sys`), existing `urllib.request` for validation, Rich (optional) for styled prompt display.

---

### Task 0: Create the plan directory structure

**Objective:** Ensure `.hermes/plans/` exists under the project root.

**Files:**
- Create: `.hermes/plans/.gitkeep` (empty marker)

**Step 1: Create directory**
```bash
mkdir -p .hermes/plans
touch .hermes/plans/.gitkeep
```

**Step 2: Add to .gitignore**
Ensure `.hermes/` is in `.gitignore` (or don't track plans).

---

### Task 1: Add `prompt_token()` function to `src/main.py`

**Objective:** Create a function that interactively prompts for a token when all automated methods fail, validates it, and returns a valid token or exits.

**Files:**
- Modify: `src/main.py:57-127` (replace `read_token` with enhanced version)
- Modify: `src/ui.py` (add prompt/validation UI methods)

**Step 1: Add `prompt_token()` function after line 56**
```python
def prompt_token(ui: UI) -> str:
    """Interactively prompt the user for a GitHub token with masked input.

    Falls back to the standard error-and-exit if stdin is not a TTY
    (e.g., piped input, CI environment).

    Returns a validated token, or exits the process on failure/abort.
    """
    import getpass

    if not sys.stdin.isatty():
        # Cannot prompt interactively — show standard error and exit
        ui.log_error("No GitHub token found and interactive input is not available (stdin is not a TTY).")
        ui.log_error("Provide a token via one of:")
        ui.log_error("  1. --token CLI flag")
        ui.log_error("  2. GITHUB_TOKEN environment variable")
        ui.log_error("  3. Token file at %TEMP%/gh_token.txt")
        ui.log_error("  4. Git credential store (git config credential.helper)")
        ui.log_error("\nCreate a token at: https://github.com/settings/tokens")
        ui.log_error("Required scope: user:follow (classic) or Followers:Read/Write (fine-grained)")
        sys.exit(1)

    ui.show_prompt_banner()

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            ui.log_warn(f"Attempt {attempt} of {max_attempts}")

        try:
            token = getpass.getpass(ui.get_prompt_text())
        except (KeyboardInterrupt, EOFError):
            ui.log_error("\nPrompt cancelled by user.")
            sys.exit(1)

        token = token.strip()

        if not token:
            ui.log_warn("Token cannot be empty.")
            continue

        # Validate the token
        ui.show_validating()
        code, rem, body = api_request(token, "GET", "https://api.github.com/user")

        if code == 200:
            user_data = json.loads(body)
            ui.show_auth_success(user_data["login"], user_data.get("following", 0))

            # Offer to save
            if ui.prompt_save_token():
                try:
                    save_path = os.path.join(tempfile.gettempdir(), "gh_token.txt")
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(token)
                    ui.show_token_saved(save_path)
                except OSError as e:
                    ui.log_warn(f"Could not save token: {e}")

            file_log("Auth: using interactively provided token")
            return token

        elif code == 401:
            ui.show_auth_error("Invalid token — authentication failed.")
            ui.show_auth_error("Check that the token is correct and not expired.")
        elif code == 403:
            ui.show_auth_error("Token lacks required permissions.")
            ui.show_auth_error("Required scope: user:follow (classic) or Followers:Read/Write (fine-grained)")
        else:
            ui.show_auth_error(f"Unexpected error (HTTP {code}). Check your network and token.")

    ui.log_error("Too many failed attempts. Exiting.")
    sys.exit(1)
```

**Step 2: Write a failing test for `prompt_token`**
Create `tests/test_prompt_token.py`:
```python
"""Tests for interactive token prompting."""
import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# Add path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.main import prompt_token

class TestPromptToken(unittest.TestCase):

    def test_no_tty_falls_back_to_error(self):
        """When stdin is not a TTY, prompt_token should exit with error."""
        ui = MagicMock()
        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.exit") as mock_exit:
            prompt_token(ui)
            mock_exit.assert_called_once_with(1)
            ui.log_error.assert_called()

    def test_valid_token_returned_after_success(self):
        """A valid token should be returned after successful validation."""
        ui = MagicMock()
        ui.get_prompt_text.return_value = ">"
        ui.show_validating = MagicMock()
        ui.show_auth_success = MagicMock()
        ui.prompt_save_token.return_value = False

        with patch("sys.stdin.isatty", return_value=True), \
             patch("getpass.getpass", return_value="ghp_validtoken"), \
             patch("src.main.api_request", return_value=(200, "4999", b'{"login":"testuser","following":10}')):
            token = prompt_token(ui)
            self.assertEqual(token, "ghp_validtoken")

    def test_empty_token_retried(self):
        """Empty token should trigger retry."""
        ui = MagicMock()
        ui.get_prompt_text.return_value = ">"
        ui.show_auth_success = MagicMock()
        ui.prompt_save_token.return_value = False

        with patch("sys.stdin.isatty", return_value=True), \
             patch("getpass.getpass", side_effect=["", "ghp_goodtoken"]), \
             patch("src.main.api_request", return_value=(200, "4999", b'{"login":"x","following":0}')):
            token = prompt_token(ui)
            self.assertEqual(token, "ghp_goodtoken")

    def test_invalid_token_fails_after_max_attempts(self):
        """After 3 failed attempts, should exit."""
        ui = MagicMock()
        ui.get_prompt_text.return_value = ">"
        ui.show_auth_error = MagicMock()

        with patch("sys.stdin.isatty", return_value=True), \
             patch("getpass.getpass", return_value="bad_token"), \
             patch("src.main.api_request", return_value=(401, "?", b"")), \
             patch("sys.exit") as mock_exit:
            prompt_token(ui)
            mock_exit.assert_called_once_with(1)
```

**Step 3: Run tests to verify they fail**
```bash
python -m pytest tests/test_prompt_token.py -v
```
Expected: FAIL — `prompt_token` not defined

**Step 4: Modify `read_token()` call site in `main()`**

In the `main()` function (around line 230), replace:
```python
token = read_token(args.token, ui)
```
with:
```python
token = read_token(args.token, ui)
if not token:
    token = prompt_token(ui)
```

But this won't work because `read_token` currently calls `sys.exit(1)` when no token is found. We need to refactor `read_token` to return `None` instead of exiting, and let `main()` handle the fallback.

**Modified `read_token()` — remove sys.exit(1), return None:**
```python
def read_token(token_arg: str | None = None, ui: UI | None = None) -> str | None:
    # ... (same logic, but instead of sys.exit(1), return None)
    # At the end:
    return None  # instead of sys.exit(1)
```

**Step 5: Run tests to verify they now pass**
```bash
python -m pytest tests/test_prompt_token.py -v
```
Expected: 4 tests PASS

---

### Task 2: Add UI methods for token prompt to `src/ui.py`

**Objective:** Add display methods for the interactive token prompt workflow — banner, prompt text, validation spinner, auth success/failure, save confirmation.

**Files:**
- Modify: `src/ui.py` (add methods to `UI` class)

**Step 1: Add UI methods to the `UI` class**

Add these methods inside the `UI` class (after `log_error`):

```python
    # ── Interactive Token Prompt ─────────────────────────────────────────

    def show_prompt_banner(self):
        """Show the token prompt introduction banner."""
        if self.rich:
            self._console.print()
            self._console.print(Panel(
                "[bold cyan]GitHub Token Required[/bold cyan]\n\n"
                "[dim]No token was found via CLI flags, environment variables,\n"
                "or saved files. Let's connect your account interactively.[/dim]\n\n"
                "[yellow]Your token will NOT be displayed on screen.[/yellow]\n"
                "[dim]Create one at: https://github.com/settings/tokens[/dim]\n"
                "[dim]Scope needed: user:follow (classic) or Followers:Read/Write (fine-grained)[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
            ))
        else:
            print(f"""
  {Colors.CYAN}{Colors.BOLD}╭── GitHub Token Required ───────────────────────────────────╮{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}                                                            {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}  No token was found via CLI flags, env vars, or      {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}  saved files. Let's connect interactively.            {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}                                                            {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}  {Colors.YELLOW}Your token will NOT be shown on screen.{Colors.RESET}               {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}  {Colors.DIM}Create one: https://github.com/settings/tokens{Colors.RESET}        {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}│{Colors.RESET}  {Colors.DIM}Scope: user:follow or Followers:Read/Write{Colors.RESET}          {Colors.CYAN}│{Colors.RESET}
  {Colors.CYAN}╰────────────────────────────────────────────────────────────╯{Colors.RESET}
""")

    def get_prompt_text(self) -> str:
        """Return the prompt string for getpass."""
        if self.rich:
            return "  [cyan]?[/cyan] Paste your GitHub token: "
        return "  > Paste your GitHub token: "

    def show_validating(self):
        """Show a validation-in-progress indicator."""
        if self.rich:
            self._console.print("  [yellow]⠋[/yellow] Validating token...", end="\r")
        else:
            sys.stdout.write(f"  {Colors.YELLOW}{spinner_char()}{Colors.RESET} Validating token...")
            sys.stdout.flush()

    def show_auth_success(self, username: str, following: int):
        """Show successful authentication result."""
        if self.rich:
            self._console.print(" " * 40, end="\r")  # Clear spinner line
            self._console.print(f"  [green]✓[/green] Token valid! Connected as [bold white]{username}[/bold white]")
            self._console.print(f"  [dim]Currently following: {following}[/dim]")
            self._console.print()
        else:
            print(f"\r  {Colors.GREEN}✓{Colors.RESET} Token valid! Connected as {username}")
            print(f"  {Colors.DIM}Currently following: {following}{Colors.RESET}")
            print()

    def show_auth_error(self, msg: str):
        """Show authentication error message."""
        if self.rich:
            self._console.print(f"  [red]✗[/red] {msg}")
        else:
            print(f"  {Colors.RED}✗{Colors.RESET} {msg}")

    def prompt_save_token(self) -> bool:
        """Ask if the user wants to save the token for future sessions.
        Returns True if yes, False if no."""
        if not sys.stdin.isatty():
            return False

        if self.rich:
            self._console.print()
            self._console.print(
                "  [yellow]?[/yellow] Save token for future sessions? "
                "[dim](stored in %TEMP%/gh_token.txt)[/dim] "
                "[green]y[/green]/[red]N[/red]",
                end=" ",
            )
        else:
            print()
            sys.stdout.write(
                f"  {Colors.YELLOW}?{Colors.RESET} Save token for future sessions? "
                f"{Colors.DIM}(stored in %TEMP%/gh_token.txt){Colors.RESET} "
                f"[{Colors.GREEN}y{Colors.RESET}/{Colors.RED}N{Colors.RESET}] "
            )
            sys.stdout.flush()

        try:
            answer = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            return False

        return answer == "y" or answer == "yes"

    def show_token_saved(self, path: str):
        """Confirm token was saved."""
        if self.rich:
            self._console.print(f"  [green]✓[/green] Token saved to [dim]{path}[/dim]")
        else:
            print(f"  {Colors.GREEN}✓{Colors.RESET} Token saved to {Colors.DIM}{path}{Colors.RESET}")

    def log_warn(self, msg: str):
        """Log a warning message."""
        if self.rich:
            self._console.print(f"  [yellow]![/yellow] {msg}")
        else:
            print(f"  {Colors.YELLOW}!{Colors.RESET} {msg}")
```

**Step 2: Run existing tests to verify nothing broke**
```bash
python -m pytest tests/test_unfollow.py -v
```
Expected: All previously passing tests still PASS

---

### Task 3: Refactor `read_token()` to return `None` instead of `sys.exit(1)`

**Objective:** Change the contract of `read_token` so it returns `None` when no token is found, allowing `main()` to fall through to `prompt_token()`. The `sys.exit(1)` call moves into `main()` as the ultimate fallback.

**Files:**
- Modify: `src/main.py:60-127` (read_token function)
- Modify: `src/main.py:230` (call site in main)

**Step 1: Refactor read_token to return None instead of exiting**

Replace the end of `read_token` (lines 118-127):
```python
    # No token found
    return None
```

Remove the error logging block (lines 119-127) — those become the responsibility of `main()`.

**Step 2: Update call site in `main()`**

Around line 230, replace:
```python
token = read_token(args.token, ui)
```
with:
```python
token = read_token(args.token, ui)
if token is None:
    token = prompt_token(ui)
```

**Step 3: Run tests**
```bash
python -m pytest tests/ -v
```
Expected: All tests PASS, including new prompt_token tests

---

### Task 4: Integration test — full end-to-end dry-run with prompt

**Objective:** Verify the full flow works end-to-end: no token → prompt → input → validation → proceed.

**Files:**
- Create: `tests/test_integration_prompt.py`

**Step 1: Write integration test**
```python
"""Integration test for the token prompt workflow."""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.main import main, read_token

class TestTokenPromptIntegration(unittest.TestCase):

    def test_read_token_returns_none_when_no_token_found(self):
        """read_token should return None when no token sources exist."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_token(token_arg=None, ui=None)
            self.assertIsNone(result)

    def test_read_token_still_works_with_env_var(self):
        """read_token should still return token from env var."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_env123"}):
            result = read_token(token_arg=None, ui=None)
            self.assertEqual(result, "ghp_env123")

    def test_read_token_still_works_with_cli_arg(self):
        """read_token should return token from CLI argument."""
        with patch.dict(os.environ, {}, clear=True):
            result = read_token(token_arg="ghp_cli456", ui=None)
            self.assertEqual(result, "ghp_cli456")
```

**Step 2: Run integration tests**
```bash
python -m pytest tests/test_integration_prompt.py -v
```
Expected: 3 tests PASS

---

### Task 5: Verify full tool still works end-to-end

**Objective:** Run the actual tool with and without token to confirm nothing is broken.

**Step 1: Test with existing token (should skip prompt)**
```bash
cd C:\Users\Fameu\projects\gh-unfollow
python -u src/main.py --dry-run -n 2 --token "$(gh auth token)"
```
Expected: Banner → auth success → dry-run output → summary. No prompt.

**Step 2: Test without any token (should show prompt)**
```bash
cd C:\Users\Fameu\projects\gh-unfollow
GITHUB_TOKEN="" python -u src/main.py --dry-run -n 2
```
Expected: Banner → "GitHub Token Required" prompt → paste token → validation → dry-run → summary.

**Step 3: Test with invalid token via env var (should show prompt after failing env var)**
```bash
cd C:\Users\Fameu\projects\gh-unfollow
GITHUB_TOKEN="invalid" python -u src/main.py --dry-run -n 2
```
Expected: Banner → "Cannot fetch user info (HTTP 401)" → "GitHub Token Required" prompt → paste valid token → works.

Actually — wait. `get_user_info` is called before `read_token` returns in the current flow? No, let me re-read. In `main()`:
1. `token = read_token(args.token, ui)` — gets token
2. `user = get_user_info(token)` — fetches user info using token

If `read_token` returns the env var token "invalid", `get_user_info` will fail with HTTP 401. We need to handle that differently.

Actually, let's reconsider. If an invalid token is found via env var, we should:
- Try to use it
- If `get_user_info` fails, show error AND THEN fall through to prompt

Let me update the plan...

**Revised approach for invalid-token-from-env:**
In `main()`, wrap the `get_user_info` call in a try/except or check:
```python
token = read_token(args.token, ui)
if token is None:
    token = prompt_token(ui)

user = get_user_info(token)
if user is None and not args.token:
    # Env var token failed — prompt
    token = prompt_token(ui)
    user = get_user_info(token)
```

But `get_user_info` currently calls `sys.exit(1)` on failure. We need to refactor it to return `None` on failure too. This is getting complex. Let me simplify.

**Simpler approach:** Handle the token fallback entirely in `read_token` + `prompt_token`. Don't change `get_user_info`. The flow is:
1. `read_token()` tries all sources, returns token or None
2. If None → `prompt_token()` interactively gets a valid one
3. `get_user_info()` uses the validated token

This way, `prompt_token()` validates internally and only returns a confirmed-valid token. If it can't get one, it exits.

That's cleaner. No changes to `get_user_info` needed.

**Step 4: Test invalid env-var token followed by interactive prompt**
```bash
cd C:\Users\Fameu\projects\gh-unfollow
GITHUB_TOKEN="invalid" python -u src/main.py --dry-run -n 2
```
Expected: `read_token` returns "invalid" → `get_user_info` fails → exits with error. No interactive prompt (because a token WAS found, it was just invalid).

Wait — that's not ideal UX. Let me reconsider...

**Final approach:** Best UX is:
1. Try all auth sources
2. Validate the found token
3. If invalid → show error AND fall through to interactive prompt (don't exit)
4. If no token at all → show prompt

This means we need to move validation into `read_token` or add a `validate_token` step. Actually, the simplest approach: in `main()`, call `get_user_info` and if it fails, call `prompt_token()`.

```python
token = read_token(args.token, ui)

# Try to use the token and fall through to prompt if it fails
if token:
    user = get_user_info(token)
    if user is None:  # get_user_info exited — won't reach here
        ...  # This won't execute
else:
    token = prompt_token(ui)

user = get_user_info(token)  # Guaranteed to succeed at this point
```

The issue: `get_user_info` calls `sys.exit(1)` so we never reach the fallback.

**Solution:** Refactor `get_user_info` to return `None` on failure instead of exiting.

```python
def get_user_info(token: str) -> dict | None:
    code, _rem, body = api_request(token, "GET", "https://api.github.com/user")
    if code != 200:
        return None
    return json.loads(body)
```

Then in `main()`:
```python
token = read_token(args.token, ui)
user = get_user_info(token) if token else None

if user is None:
    # Token was missing or invalid — prompt interactively
    token = prompt_token(ui)
    user = get_user_info(token)  # prompt_token guarantees valid token

# Now user is guaranteed non-None
```

This is the cleanest approach. Let me update the plan with this.

**Updated file changes:**
- `get_user_info` returns `dict | None` (was `dict`, used to exit(1))
- `read_token` returns `str | None` (was `str`, used to exit(1))
- `main()` orchestrates the fallback

---

### Task 6: Update tests for refactored `get_user_info`

**Objective:** Since `get_user_info` no longer calls `sys.exit(1)`, update the existing tests.

**Files:**
- Modify: `tests/test_unfollow.py`

**Step 1: Update test**
In `TestAPIMocking` class, add:
```python
def test_get_user_info_returns_none_on_failure(self, mock_api):
    mock_api.return_value = (401, "?", b"")
    result = get_user_info("bad_token")
    self.assertIsNone(result)
```

**Step 2: Run tests**
```bash
python -m pytest tests/ -v
```
Expected: All tests PASS

---

### Task 7: Commit everything and push

**Objective:** Finalize the feature branch and push.

**Step 1: Commit**
```bash
git add src/main.py src/ui.py tests/test_prompt_token.py tests/test_integration_prompt.py tests/test_unfollow.py
git commit -m "feat: interactive token prompt with masked input and validation

- prompt_token() prompts for GitHub token when no source found
- Masked input via getpass.getpass() (cross-platform)
- Validates token against GitHub API before accepting
- Offers to save token to %TEMP%/gh\_token.txt for future sessions
- Up to 3 attempts before exit
- TTY-aware: skips prompt on piped/CI environments
- read\_token() now returns None instead of sys.exit(1)
- get\_user\_info() now returns None instead of sys.exit(1)
- Full test coverage for prompt, validation, retry, and auth flows
- Rich UI integration with styled prompt panels and spinners"
```

**Step 2: Push**
```bash
git push origin master
```

**Step 3: Bump version**
Update to v2.1.0 in `src/__init__.py`, `src/main.py`, `package.json`, `pyproject.toml`.

---

### Risks and Tradeoffs

| Risk | Mitigation |
|------|------------|
| `getpass.getpass()` truncates long tokens | Tokens are ~170 chars; getpass handles up to console limit (~4KB) |
| Piped/CI environments can't prompt | TTY check — falls back to existing error message |
| Token saved in plaintext in TEMP | Warn user; TEMP is user-specific and typically private |
| Rich `Console.input()` vs `getpass` | `getpass` is stdlib and works cross-platform; Rich's input doesn't mask |
| `prompt_token` calls `api_request` which needs imports | Already imported at module level in main.py |

### Open Questions

- Should we also support `--token-prompt` as an explicit flag to force interactive mode even when other sources exist? (Nice-to-have, YAGNI for now)
- Should we offer to save to git credential store instead of file? (Complex, YAGNI)

---

### Summary of Files Changed

| File | Change Type | Lines Changed |
|------|-------------|---------------|
| `src/main.py` | Modify | ~60 lines added, ~10 removed |
| `src/ui.py` | Modify | ~100 lines added |
| `tests/test_prompt_token.py` | Create | ~80 lines |
| `tests/test_integration_prompt.py` | Create | ~40 lines |
| `tests/test_unfollow.py` | Modify | ~10 lines added |
| `src/__init__.py` | Modify | 1 line (version bump) |
| `package.json` | Modify | 1 line (version bump) |
| `pyproject.toml` | Modify | 1 line (version bump) |
