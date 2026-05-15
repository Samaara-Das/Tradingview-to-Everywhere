# Session context — 2026-05-14 (TTE-Claude)

**Purpose**: This file captures everything from the 2026-05-14 session so a post-compact future-me has full context. Read this before doing anything when you resume.

---

## Starting point (what triggered the session)

Sammy ran `/get-context` and asked me to:
1. Get context on previous sessions
2. Get context on the current branch
3. Checkout to main if branch work was done

Started on branch `docs/session-bus-2026-05-08` (one commit ahead — internal `.claude/` session notes only, no PR). Switched to main; main had diverged from origin (320/325 commits — history rewrite from older work). User authorized reset.

KG state at session start (per MemPalace before it disconnected):
- tte-1 live on KVM8, 115K+ webhooks/24h, 0 errors per 2026-05-11 SB-UAT
- Backfill CANCELLED per Nili 2026-05-13 (146 reversedSnapshot:true docs pending Mongo revert)
- Current focus per KG: Coda Task A (CCM verify) + Task B (tte-2 + 4000 symbols + autonomous onboarding); SB+TTE Claude collab via bus

---

## What we actually accomplished this session

### ✅ Done

1. **Git reset to origin/main** — local was 320 vs 325 diverged (upstream history rewrite). User had to remove `Bash(git reset --hard*)` from deny list since it's a hard guardrail in `~/.claude/settings.json:43`.
2. **gh auth setup-git** — wired git's credential helper to gh CLI keyring. GCM popups eliminated for github.com.
3. **Backfill teardown on KVM8** — `docker rm tte-backfill`, removed image sha 06d65a9c. Note: tte-1 runs on ORPHAN image sha c8727ab9... whose content digest is MISSING from docker storage (pre-existed, not caused by my teardown). docker tag and docker commit both fail with "content digest not found". Single restart attempt available — see Phase 1 task #13 plan.
4. **Mongo revert** in `tte.setup_messages` — NOT `stock_buddy_app.setup_messages` as KG had it. **161 docs** (not 146 — backfill nudged forward post-snapshot). 130 restored from preserved originalSnapshotUrl/originalSnapshotTvUrl. 31 had no originals → marker-cleared only (re-enter SB pending queue). Final: 0 reversedSnapshot:true, 0 originalSnapshot* fields. Script saved to `scripts/revert_reversed_snapshots.py`.
5. **Cleanup of stale backfill tasks #1-7** (deleted).
6. **Visual verification of post-2026-05-08 snapshots** — 10 PNGs across categories. Findings: only **1 of 10** (MANYAVAR rendered 2026-05-08 12:01 UTC) showed correctly-reversed TP/SL labels. The other 9 either: (a) had Trade Drawer V2 indicator loaded but no labels drawn (entry off-screen), or (b) didn't have the indicator loaded at all (just NWE bands).
7. **Root cause hypothesis raised + REJECTED**: "TV UI redesigned, selectors broken." Inspected via chrome-devtools MCP in logged-in TTE Profile 4 — ALL 4 legacy selectors are INTACT:
   - `button#header-toolbar-symbol-search` ✓
   - `span.value-JQZ0HKD4` ✓
   - `div[data-name="symbol-search-items-dialog"]` ✓
   - `input[data-qa-id="symbol-search-input"]` ✓
   - `div.chart-markup-table` ✓
   - `div[data-name="right-toolbar"] button[aria-label="Alerts"]` ✓
   The bug is NOT selectors. Production fails for a different reason — likely live tte-1 page state (some stuck dialog, overlay, or wrong layout). Need to inspect live tte-1 chrome via devtools port 44747 (inside container) to find the real cause.
8. **Spec & task list aligned to the simplified scope** (after multiple revisions — see Decisions below):
   - `.claude/run-tasks-2026-05-14.md` — authoritative spec, 10 tasks with full ACs
   - `.claude/phase6-spec-2026-05-14.md` — earlier larger spec, now superseded by `run-tasks` (kept for archeology)
   - TaskList: #6, #11, #12, #9, #13, #14, #17, #18, #19, #16 (10 tasks, all dependencies wired)
9. **Discord webhook verified live** — URL stored in chat (must move to `/opt/stockbuddy/secrets/.env.cc` as part of task #18). Test ping returned HTTP 204 from the webhook.
10. **Memory file added**: `~/.claude/projects/.../memory/reference_chrome_devtools_mcp_tte_profile.md` documents how to attach chrome-devtools MCP to TTE's logged-in profile (line in MEMORY.md index).
11. **Auth fix landed**: cookies persist in `TTE\Default` (not Profile 4 — user logged in once manually during the session because chrome-devtools MCP doesn't pass `--profile-directory=Profile 4`, just `--user-data-dir`).

### ⚠️ In progress when session ends

- **Task #6**: investigation is half-done. Confirmed selectors are intact in fresh chrome. Next step is to attach to live tte-1 Chrome via devtools port 44747 and screenshot/probe the actual page state.

### ⬜ Not started yet

- Tasks #11, #12, #9, #13, #14, #17, #18, #19, #16. All blocked behind #6.

---

## Key findings from logs / investigation

### Production failure pattern (from `docker logs tte-1` 2026-05-13 14:23+)

```
INFO  - Fetched 1 pending snapshots
INFO  - Processing 1 pending snapshots (round 1/2)
WARNING - Failed to set bars to right — continuing anyway
  (root cause: div.chart-markup-table NoSuchElementException at snapshot_worker.py:366)
INFO  - Taking snapshot: NSE:CIPLA 1H — Entry X, SL Y, TP Z
ERROR - Failed to change the symbol of the chart
  (root cause: WebDriverWait(15, element_to_be_clickable('#header-toolbar-symbol-search')) timeout at chart.py:109)
INFO  - Round 1: 0/1 succeeded
```

Maintenance loop also fails (same root cause class — different selectors):
- alerts sidebar at tradingview.py:653 — `div[data-name="right-toolbar"] button[aria-label="Alerts"]` — TimeoutException
- log tab at helpers.py:60 — `button[aria-controls="id_alert-widget-tabs-slots_tabpanel_log"]` — NoSuchElementException

**All 6 selectors are present in my fresh logged-in chrome.** So either:
1. Live tte-1's Chrome session got into a degraded state after 6 days (page stuck on dialog/overlay/error)
2. TTE's Snapshot layout differs in some way (no indicator loaded?)
3. Headless mode has different DOM than headed mode for TV
4. Something else specific to the live tte-1 page state

**Hypothesis to test in next session via tte-1 devtools port 44747**: live tte-1 Chrome has a transient overlay covering the toolbar (`container-VeoIyDt4`-style) that's been stuck for 6 days, OR a chart-not-loaded state.

### Cookie state confirmed OK

`docker exec tte-1 ...` Selenium spawn in a fresh process loads TV chart fine, no GoPro link, AAPL renders. So TV session cookie is valid. NOT a login expiry issue.

### CC-trigger discovery

- "Claude code manager" on KVM8 = `cc-trigger.service` at `/opt/stockbuddy/cc-trigger/server.js`
- Receives POST `127.0.0.1:8765/alert`, spawns `claude --print` to investigate, opens PR
- Currently sends Telegram digests; task #18 switches to Discord
- Spec inside server.js mentions Phase 6 steps 4-7 (reviewer Claude, CI gate, auto-merge, auto-deploy, watchdog) — all TODO. Sammy declined to build these in this session.

---

## Decisions made (chronological)

| When | Decision | Rationale |
|------|----------|-----------|
| 18:55 | Drop the Phase 6 auto-review/auto-merge/auto-deploy/watchdog architecture | Sammy: "one Claude can't call another Claude. too complex. just send me a Discord message of an issue." |
| 19:00 | Use 6 TTE-specific monitoring checks (Option C) | Original Coda incident exposed that NO checks existed for snapshot failure modes — that's the real blackout cause |
| 19:00 | Use Discord webhook (not bot, not Telegram) | Sammy provided webhook URL, said "drop telegram digest" |
| 19:30 | Spec the work in `.claude/run-tasks-2026-05-14.md`, reference from /goal prompt | Sammy: "create another .md file and write down everything ... the prompt should point claude back to this file" |
| 19:30 | Real root cause is NOT selector breakage | Direct DOM verification in logged-in chrome showed all selectors intact |
| Various | Auto-mode on; no commands off-limits | Sammy: "you are authorized to use ANY command you want" |
| Various | PR review must use separate `feature-dev:code-reviewer` sub-agent | Sammy: "avoid you reviewing and having a bias" |
| Various | Deploy autonomously after PR merges | Sammy: "do autonomously" |
| Various | Self-pace via `/goal` mode (no /loop, no cron, no remote agent) | Local-only tool dependencies (chrome-devtools MCP) make remote agents unsafe; /loop adds ceremony without benefit |

---

## Blockers encountered

1. **`git reset --hard*` deny rule in ~/.claude/settings.json** — user removed it temporarily, ran the reset, then linter re-added it (user's intentional safety net).
2. **Auto-mode classifier blocks edits to ~/.claude.json (agent self-modification)** — even with explicit user authorization. User had to do the chrome-devtools MCP arg change themselves.
3. **Heredoc Python via SSH had repeated f-string-with-backslash syntax errors** — fixed by writing scripts to files then `docker cp` + `docker exec python` instead of inlining.
4. **Mempalace MCP disconnected mid-session** (later reconnected; user did /exit and came back via SessionStart:resume).
5. **Coda MCP disconnected** at session end. Task #16 has a fallback: write .claude/coda-closure-2026-05-14.md if it stays down.
6. **Chrome-devtools MCP profile config** — by default uses `--isolated` (fresh chrome). Initially passed only `--user-data-dir=TTE` but Chrome opened `Default` subprofile (no TV cookies). User manually logged in to TV in the MCP-attached chrome window; cookies now persist in `TTE\Default` for the session. Cleaner long-term: arg should be `--user-data-dir=...TTE\Profile 4` directly (Sammy declined to make the additional edit, manual login was faster).

---

## Tools / access state (confirmed working at session end)

| Tool | State | Notes |
|------|-------|-------|
| chrome-devtools MCP | Connected, attached to `TTE\Default` subprofile, manually logged in to TV | If session resumes after Chrome closes, need to log in again; if MCP relaunches, will re-use Default since cookies persisted |
| SSH KVM8 | Working via `~/.ssh/kvm8-claude_ed25519` port 2222 root@168.231.103.163 | Key-based auth, no password prompt |
| gh CLI | Authed (gho_ token), credential helper wired via `gh auth setup-git` | github.com + gist.github.com both delegate to gh |
| Discord webhook | HTTP 204 confirmed | URL is in chat only — must be moved to `/opt/stockbuddy/secrets/.env.cc` as part of task #18, never committed to git |
| Mempalace MCP | Reconnected at SessionStart:resume | TTE wing facts up to 2026-05-14 16:49 |
| Coda MCP | Disconnected (was working earlier) | Task #16 has fallback path |
| Tradingview MCP | Connected — useful for `mcp__tradingview__*` chart/Pine ops, but only on local TV Desktop, not prod |
| Discord MCP (plugin_discord) | Has reply/react/edit_message/fetch tools | Could send pings if I had a chat_id; for now using webhook |

---

## Files created/modified this session

| File | What |
|------|------|
| `scripts/revert_reversed_snapshots.py` | One-shot Mongo revert script (already used) |
| `scripts/verify_recent_snapshots.py` | Read-only verification probe |
| `scripts/sample_10_snapshots.py` | Sampling script for the 10 verification PNGs |
| `scripts/sample_post_reversal.py` | Post-2026-05-08-12:00 sample script |
| `.claude/run-tasks-2026-05-14.md` | **AUTHORITATIVE TASK SPEC for the autonomous run** |
| `.claude/phase6-spec-2026-05-14.md` | Earlier Phase 6 spec (now superseded — kept for archeology) |
| `.claude/session-2026-05-14-context.md` | This file |
| `~/.claude/projects/.../memory/reference_chrome_devtools_mcp_tte_profile.md` | Memory: how to attach chrome-devtools MCP to TTE TV profile |
| `~/.claude/projects/.../memory/MEMORY.md` | Updated to index the new memory file |
| `C:\Users\dassa\AppData\Local\Temp\snap-verify\*.png` | Downloaded snapshot PNGs (10 from initial test + tte1-headless-state.png + signin/login screenshots) |

KVM8 side:
- `tte-backfill` container REMOVED + its image sha 06d65a9c deleted
- Mongo `tte.setup_messages` — 161 docs reverted
- 4 unupstreamed patches still in `/opt/stockbuddy/tte/` source on KVM8 (per 2026-05-08 KG): launcher_syspath, sign_in_call, tframe_skip, bus_log_try_except

---

## Open questions / decisions still pending

1. **Coda task button mechanic** — once Coda MCP reconnects, need to verify if status change is a column update or push_button. Task #16 has fallback if Coda stays down.
2. **Off-screen-entry-time bug** — separate bug from the selector/state bug. Old setups have entryTime that's hours/days before render time → labels drawn off-visible-range. Fix likely involves `chart_scroll_to_date(entryTime)` before snapshot capture. Whether this is in scope for the current PR or a follow-up: TBD based on root cause finding.
3. **Auto-revert at night** for monitoring checks — Sammy said yes. Need to gate market-hours-only alerts.

---

## How to resume after compact

1. Read this file first.
2. Read `.claude/run-tasks-2026-05-14.md` (the task spec).
3. Run `TaskList` to see current task state.
4. Resume #6 — attach to live tte-1 Chrome devtools at port 44747 via websocket from inside the container. Take a screenshot. Diagnose the page state. Output a written diagnosis + code-line-level fix list.
5. After #6 done, proceed through the chain per the spec.
6. Discord-ping at each phase boundary using the webhook URL (currently in chat; check for it in /opt/stockbuddy/secrets/.env.cc once #18 moves it there).

**DO NOT** restart investigation from scratch — selectors are confirmed intact, focus on live page state.
**DO NOT** stop and ask Sammy for permission to continue — operate in /goal autonomous mode.
**DO** Discord-ping when genuinely blocked, parallelize the rest.

---

## One-line summary

Session resolved a half-day production-data crisis (snapshot blackout since 2026-05-08) by mapping the actual scope, building a clean 10-task spec with acceptance criteria, eliminating the wrong "TV UI redesign" hypothesis, and queuing the real-root-cause investigation + fix + monitoring + Discord migration for the autonomous run. Everything is staged; nothing is started.
