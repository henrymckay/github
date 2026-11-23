# Reading list

A small local web app for one person to keep a reading list: add books, track progress, search and see simple stats.

Records: [`DEPENDENCIES.md`](DEPENDENCIES.md), [`costs.csv`](costs.csv), [`verification.csv`](verification.csv).

> [!NOTE]
> Unsigned plan, written 2026-11-23 in autonomous mode by a scheduled run of a stored prompt on the owner's account.
> Every decision is *(proposed)* or *(by precedent)* until the owner reviews it.

## Brief

### Goal

Keep a reading list on your own machine.
Done when `uv run reading-list` starts the app, and in the browser a person can add a book, record pages read, find it by search and see the totals change on the stats screen.

### Terms

- **Book** — one title on the list, with its author, page count, pages read, status, rating and notes.
- **Status** — where a book stands: `to read`, `reading` or `finished`.
- **Progress** — pages read against the book's page count, shown as a percentage.
- **Library** — the screen listing every book, with search and the add form.
- **Stats** — the screen of totals over the library.

### Requirements

- **R1** Add books.
  - Cost: a store and a form; dropping it leaves nothing.
- **R2** Track progress.
  - Cost: pages read per book and a status that follows them.
- **R3** Search.
  - Cost: a text filter plus status filter and sort over the library.
- **R4** See simple stats.
  - Cost: one screen of totals and one chart.
- **R5** Runs locally with one command.
  - Cost: everything installs from `uv.lock`; no Node, no database server.

### Not yet

- **Accounts or sharing** — earned by a second person using the same list.
- **Book lookup by ISBN from an online catalogue** — earned by typing titles becoming the chore; it adds an outside call.
- **Import and export (Goodreads CSV)** — earned by an existing list to bring in.
- **Reading goals and an `abandoned` status** — earned by asking for them.

## Design

### Inputs

- **Form input from the browser** — what the person types; untrusted text, validated at the route and escaped on render; class *personal* (secure-project).

### Data flow

1. **Form or query** — parsed and validated into a `Draft` or a search request at the driver. (IO)
2. **Rules** — pure functions settle status from progress, filter and sort the library, and summarise it for the stats.
3. **Store** — one SQLite file, one row per book keyed by `id`, written on each change. (IO)

### Outputs

**`books.db`** — SQLite in the user data directory (`platformdirs`), overridable with `--db`; overwritten in place, row by row; read only by this app; class *personal*, never leaves the machine.

| column | type | meaning |
|---|---|---|
| id | integer | key |
| title | text | not empty |
| author | text | may be empty |
| pages | integer, null | page count, null when unknown |
| pages_read | integer | 0 to `pages` |
| status | text | `to_read`, `reading` or `finished` |
| rating | integer, null | 1 to 5 |
| notes | text | free text |
| added_on | text | ISO date |
| finished_on | text, null | ISO date, set when finished |

### Interface

```bash
uv run reading-list
```

```text
Reading list running at http://127.0.0.1:8000 — data in /home/me/.local/share/reading-list/books.db
Press Ctrl+C to stop.
```

Options `--port` and `--db`; exit 0 on Ctrl+C, 2 on a bad option, 1 when the port is taken, with one line on standard error saying what to do.

| method | path | returns |
|---|---|---|
| GET | `/` | Library, `?q=&status=&sort=` |
| POST | `/books` | add a book, then the Library |
| GET | `/books/{id}` | the edit screen |
| POST | `/books/{id}` | save edits |
| POST | `/books/{id}/progress` | record pages read |
| POST | `/books/{id}/delete` | delete |
| GET | `/stats` | Stats |
| GET | `/api/books` | the library as JSON, same query as `/` |
| GET | `/api/stats` | the stats as JSON |

- **Library** — answers "what am I reading and how far along?": search box, status filter and sort on one row, a collapsible add form, then one row per book with title, author, status chip, progress bar with `120 / 350 pages · 34%`, an inline pages-read field and edit; empty state "No books yet — add the first one above", and "No books match" with a clear link for a search.
- **Stats** — answers "how much am I reading?": tiles for books, reading now, finished this year and pages read; average rating; a bar chart of books finished per month over the last 12 months; a count per status.
- **Edit** — the full form for one book, with delete.
- **Design** — the house system (design-interface) as CSS variables, Inter bundled, light and dark with a remembered toggle, usable at 390 px; best in class here means instant, no-JavaScript-needed forms like a well-made server-rendered app, with search that filters as you type.

### Runs on

- **App** — the owner's machine only, bound to `127.0.0.1`; $0.
- **Teardown** — delete the repo checkout and `books.db`; nothing else is created.
- **Threat model** — no secret; the risk is another website or a DNS-rebound name posting to the local server, stopped by rejecting any `Host` outside loopback and any cross-origin `POST` (secure-project, Guard what is served); stored text is escaped by Jinja autoescape.
- **Unattended runs** — this build ran in a cloud session on this repository alone, with no secret; the app itself runs only when the owner starts it.

### Errors

- **Empty title, pages read past the page count, rating outside 1–5** — the form is shown again with the message beside the field and status 422.
- **Unknown book id** — 404 page with a link back to the Library.
- **Port in use** — exit 1: "Port 8000 is in use — try `uv run reading-list --port 8001`".

### Decisions

- **D1 Server-rendered HTML with FastAPI and Jinja2** over a Vite and React front end — one language, nothing to build, forms work without JavaScript; cost: no client-side state, fine for one user; overrides `write-entry-points`, Dashboard, whose pick is for data dashboards (proposed).
- **D2 SQLite through the standard library** over Parquet or JSON — small single-writer state (store-data); cost: none at this size (by precedent).
- **D3 Status follows progress** — pages read above 0 moves `to read` to `reading`; reaching the page count finishes the book and stamps `finished_on`; marking finished fills pages read (proposed).
- **D4 Search in Python over all books** over SQL `LIKE` or FTS5 — a personal list is hundreds of rows, so no index or speed budget is needed (proposed).
- **D5 Chart as inline SVG drawn by the template** over ECharts — one bar series needs no library or JavaScript; overrides `write-entry-points`, Dashboard, on the chart library (proposed).
- **D6 Small build path, built in the main session** over the full path, although the data is classed personal — nothing leaves the machine and there is no credential; the final review by a fresh agent and the acceptance run still run; overrides `build-project`, Pick the path (proposed).
- **D7 Python 3.15** with `typer`, `fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `platformdirs` (setup-python, by precedent).

## Delivery

### Verification

- **R1** — `test_when_add_book_then_listed`, and the edit and delete tests in `tests/suite/reading_list/drive/test_app.py`.
- **R2** — `tests/suite/reading_list/transform/test_book.py` status rules, and `test_when_record_progress_then_percentage_shown`.
- **R3** — `test_book.py` search and sort tests, and `test_when_search_then_only_matches_listed`.
- **R4** — `test_stats.py`, and `test_when_stats_then_tiles_show_totals`.
- **R5** — a fresh clone, `uv run reading-list`, then a browser session adding a book, recording progress, searching and opening stats.
- **Acceptance** — the suite at both coverage levels (core 100% branches), `ruff`, `pyright` strict, and the R5 run with screenshots at 1440 and 390 px in light and dark.

### Milestones

- [ ] **M1 Core and store** — R1 to R4 rules; done when the core is at 100% branch coverage and the store round-trips.
- [ ] **M2 Web app** — R1 to R5; done when the R5 run passes and the screenshots read right.

## Open

### Assumptions

- **A1** One person, one machine — the brief says "runs locally"; a second user would need accounts.
- **A2** The owner has `uv`; it installs Python 3.15 itself.

### Questions

None.

### Ideas

- **I1** ISBN lookup from Open Library to fill title, author and pages — saves typing; costs an outside call and its error handling.
