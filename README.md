# InstaReciprocal v1.0

A local-first Instagram reciprocal-follow relationship manager for Windows.
InstaReciprocal imports Instagram's downloaded JSON account data, normalizes usernames,
compares followers vs. following, manages a protected whitelist, tracks review decisions in a local SQLite database,
and provides a dark CustomTkinter desktop interface.


## Locked product decisions
- Windows desktop target
- Dark UI planned for a later phase
- Compare all accounts (no account-type filtering)
- Whitelist enabled in the product design
- Review-before-unfollow; no automated unfollowing

## Safety and scope
This phase does **not** log in to Instagram, scrape profiles, use session cookies, or
perform follow/unfollow actions. It only reads a ZIP or extracted folder from Instagram's
"Download your information" export. The export is a snapshot, so results can become stale.

## Requirements
- Python 3.11+
- No third-party runtime dependencies

## Run
```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pytest
```

## Expected Instagram export files
Typical JSON exports contain:
- `followers_and_following/followers_1.json` (sometimes several `followers_2.json`, etc.)
- `followers_and_following/following.json`

The importer also searches recursively for these filenames in an extracted export directory
or ZIP archive. It accepts common Instagram JSON structures:
- follower list entries containing `string_list_data[].value`
- following export object containing `relationships_following`
- account records with `title` or `username` where appropriate

## Example usage
```powershell
python -m instareciprocal.cli --input "C:\Users\You\Downloads\instagram-export.zip" --output ".\exports\phase1-import.json"
```

Or use an extracted directory:
```powershell
python -m instareciprocal.cli --input "C:\Users\You\Downloads\instagram-export" --output ".\exports\phase1-import.json"
```

The output contains normalized usernames, source filenames, import timestamp, and counts.
It does not contain passwords, cookies, or private login information.

## Project layout
```text
InstaReciprocal/
├── instareciprocal/
│   ├── __init__.py
│   ├── importer.py
│   ├── normalizer.py
│   ├── parser.py
│   └── cli.py
├── tests/
│   ├── test_normalizer.py
│   ├── test_parser.py
│   └── test_importer.py
├── requirements.txt
└── README.md
```

## Phase 1 acceptance criteria
- Reads ZIP archives and extracted folders.
- Finds split follower files.
- Parses follower and following JSON formats.
- Normalizes usernames consistently and removes duplicates.
- Reports clear errors for missing or malformed input.
- Includes automated tests.


## Phase 2 — Comparison engine

Compare a Phase 1 import and write JSON + CSV reports:
```powershell
python -m instareciprocal.compare_cli --input "exports\phase1-import.json"
```

Optional whitelist file: `data/whitelist.json` (a JSON array of usernames):
```json
[
  "close_friend",
  "important_account"
]
```

Add/remove names in that file before running the comparison. Whitelisted accounts remain
visible in `not_following_back` and appear under `protected`, but are excluded from
`review_queue`. The tool only generates a review list; it never unfollows anyone.

Reports are written to `exports/comparison-report.json` and
`exports/comparison-report.csv`.


## Phase 3 — Dark desktop GUI

Install dependencies and launch:
```powershell
pip install -r requirements.txt
python run_gui.py
```

The GUI includes a dark dashboard, import button, comparison refresh, searchable lists,
selection controls, profile-opening links, and whitelist editor. It only opens profiles
in your browser; it does not automate Instagram actions.


## Phase 4 — Review manager

Review decisions are stored locally in `data/instareciprocal.db` (SQLite):
- `pending`
- `reviewed`
- `skipped`
- `unfollowed_manually`

Use the row actions in the desktop app to record decisions. The "Unfollowed" action asks
you to confirm that you already unfollowed the account manually on Instagram; it only
records that confirmation and never performs an Instagram action. Every status change
is recorded in the local review event history.


### Import individual JSON files

The desktop Import button now accepts:
- One Instagram ZIP archive; or
- `following.json` plus `followers_1.json` (and every additional `followers_2.json`, etc. file).

When selecting separate JSON files, hold **Ctrl** while clicking to select the follower
file(s) and `following.json` together. Do not select only one side of the export.


## Phase 5 — Bulk review, scan history and analytics

- Bulk mark selected accounts as `reviewed`, `skipped`, or reset to `pending`.
- Bulk actions never mark accounts as unfollowed; that remains an individual manual confirmation.
- Open selected profiles in batches of up to 10, with confirmation between batches.
- Scan snapshots are saved in the local SQLite database and deduplicated by export timestamp.
- History compares the latest two distinct exports for new/lost followers and following changes.
- Existing review decisions remain stored in the same local database.


## Phase 6 — Windows executable packaging

This project is packaged as a Windows **onedir** application. Build it on Windows
(not Linux/macOS), using Python 3.11 and the project virtual environment.

1. Extract the project folder.
2. Open Command Prompt in the `InstaReciprocal` folder.
3. Run `build_windows.bat`.
4. The executable will be at:
   `dist\InstaReciprocal\InstaReciprocal.exe`

Keep the entire `dist\InstaReciprocal` folder together. The `data` and `exports`
folders are stored beside the executable, not inside the temporary PyInstaller bundle.
This lets the app save its SQLite database, whitelist, imported export, and reports
without administrator permissions. Back up the `data` and `exports` folders before
replacing the application with a newer build.

Precompiled release packages (`InstaReciprocal-v1.0.0-windows-x64.zip`) can simply be extracted and run immediately by launching `InstaReciprocal.exe`.
Alternatively, you can build from source on Windows using `build_windows.bat` or `pyinstaller InstaReciprocal.spec`.

