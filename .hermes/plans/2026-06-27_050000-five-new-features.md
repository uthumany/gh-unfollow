# 5 New Features — Implementation Plan

> **Goal:** Add whitelist-file, inactive-user cleanup, non-mutual unfollow, interactive selection, and backup/restore to gh-unfollow.

**Architecture:** Each feature is a self-contained pipeline step that runs BEFORE the main unfollow loop. They filter the user list down to only the desired targets. Backup/restore are separate commands that bypass the unfollow flow entirely.

**Files affected:**
- `src/main.py` — new CLI args, feature functions, main() orchestration
- `src/ui.py` — new UI methods for interactive mode, backup/restore prompts
- `tests/test_features.py` — new test file

---

## Feature 1: Whitelist from File

**New flag:** `--whitelist-file WHITELIST_FILE`

**Logic:**
1. Read file, one username per line
2. Merge with `--whitelist` comma-separated list
3. Pass combined set to UI constructor

**Implementation:**
- In `parse_args()`, add `--whitelist-file` string arg
- In `main()`, after parsing `--whitelist`, also read file if provided
- Merge: `whitelist = set(csv_whitelist) | set(file_whitelist)`

---

## Feature 2: Inactive User Cleanup

**New flag:** `--inactive-days N`

**Logic:**
1. For each user in following list, fetch their public events: `GET /users/{username}/events/public`
2. Find the latest event's `created_at` timestamp
3. Calculate days since last activity
4. If days > N, add to target list; otherwise skip
5. Log skipped users as "Active — skipped"

**Rate limit concern:** Fetching events per user multiplies API calls. Solution: fetch in batches with cooldown, use `per_page=1` to minimize data transfer.

**Implementation:**
- New function `filter_inactive(token, users, days, ui)` — returns filtered list
- Calls `GET /users/{username}/events/public?per_page=1` per user
- Rate-limit aware: cooldown between event queries
- Progress: show "Checking activity..." with spinner

---

## Feature 3: Non-Mutual Unfollow

**New flag:** `--non-mutual`

**Logic:**
1. Fetch ALL followers: paginate `GET /user/followers?per_page=100`
2. Store followers in a set
3. During unfollow loop, skip any user who IS in the followers set
4. Log kept users as "Mutual — kept"

**Implementation:**
- New function `fetch_followers(token, ui)` — returns set of follower usernames
- Paginated fetch with rate limiting
- In main loop: `if name in followers_set: skip`

---

## Feature 4: Interactive Selection Mode

**New flag:** `--interactive`

**Logic:**
1. Fetch following list in batches of 50
2. Display checkbox-style list using `rich` (if available) or simple numbered list
3. User toggles selection via space/enter
4. Only selected users get unfollowed
5. After batch processed, load next batch

**Implementation:**
- New function `interactive_select(users, ui)` — returns list of selected usernames
- Uses `rich.prompt` if available, else falls back to numbered input
- Batched: process 50 at a time, ask "Continue to next batch? [Y/n]"

---

## Feature 5: Backup and Restore

**New flags:** `--backup FILE` and `--restore FILE`

**Logic (Backup):**
1. Fetch full following list (paginated)
2. Save to JSON: `{"backup_date": "...", "count": N, "users": [...]}`

**Logic (Restore):**
1. Read JSON file
2. For each username, send `PUT /user/following/{username}`
3. Use same rate-limiting engine
4. Log progress with "Re-followed @{name}"

**Implementation:**
- New functions: `cmd_backup(token, filepath, ui)` and `cmd_restore(token, filepath, ui)`
- Backup bypasses unfollow loop entirely
- Restore uses rate-limited PUT calls
- Backup format: `{"version": 1, "date": "ISO", "users": ["user1", "user2", ...]}`
