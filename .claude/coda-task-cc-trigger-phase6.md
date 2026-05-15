# Coda task — Wire cc-trigger investigations to autonomous PR + auto-deploy + watchdog

**Status**: Pending (Coda MCP was disconnected at creation time; paste this manually into the TTE/SB task board)
**Created**: 2026-05-15
**Related Task Master ID**: `10`
**Repo task file**: `.taskmaster/tasks/tasks.json` (entry `10`)

---

## TL;DR

cc-trigger currently spawns `claude --print` to investigate alerts and posts the summary to Discord. The investigators **already correctly identify root causes** end-to-end. They just can't open PRs / auto-deploy because the cc-trigger workdir has no git checkout + no `gh` auth. Close the loop = Phase 6 steps 4-7 from `.claude/phase6-spec-2026-05-14.md` (which was descoped on 2026-05-14 to ship the simpler MVP).

## Why this matters now (real-world proof)

**2026-05-15 incident**: Today's `pipenv lock` for the pyotp work silently wiped `requests` from `Pipfile.lock` (it had been added inline on the VPS 2026-05-05 but never landed in Pipfile). The rebuilt `tte:phase4` image had no `requests`, so `tte/snapshot_worker.py:15 import requests` raised `ModuleNotFoundError` every time the maintenance loop tried to start. Container crashed ~1 second into "Browser ready", auto-restarted, and crash-looped for 6 hours.

| Time (UTC) | Event |
|---|---|
| 03:46 | Container starts on new (broken) image |
| 03:52:20 | First `tte-container-restart` Discord alert fires |
| 03:42-04:57 | Investigator Claude spawns identify the EXACT bug (`tte/snapshot_worker.py:15` + `Pipfile` missing entry + `Pipfile.lock` regen needed). Discord receives detailed root-cause summaries. |
| 04:57 | Investigator produces the EXACT 3-line fix and the EXACT files to edit (Pipfile, Pipfile.lock, snapshot_worker.py). No PR opened — no git access in cc-trigger workdir. |
| 05:43, 05:53, etc. | More Discord alerts (DEDUPE'd within 1h cooldowns) |
| 11:48 IST = 06:18 UTC | Sammy finally notices and asks "check on TTE" |
| 12:00 IST = 06:30 UTC | Human applies the same fix the investigator already wrote 1h 21m ago |

**Net: 1h 21m of avoidable downtime** because the cc-trigger investigator can analyze but not act. With auto-PR + auto-deploy, the fix would have shipped at ~05:00 UTC and tte-1 would have been healthy by 05:10 UTC — before Sammy was awake.

## Scope (Phase 6 steps 4-7)

### STEP 4 — Writer Claude opens PR
- Give the spawned investigator a writable git checkout (`/opt/stockbuddy/repos/Tradingview-to-Everywhere`)
- `gh` auth scoped to TTE + SB repos only (deploy-key-style PAT OR GitHub App install)
- After diagnosis, investigator runs `git checkout -b fix/auto-{alert-name}-{date}`, applies the patch, commits, pushes, opens PR via `gh pr create`
- Already producing the patch — just needs the act-on-it side wired

### STEP 5 — Reviewer Claude audits the diff
- SEPARATE Claude spawn (different cwd, different prompt) with the existing `feature-dev:code-reviewer` sub-agent system
- Posts review comments to GitHub via `gh pr comment`
- Important: this is **cc-trigger orchestrating two sequential claude spawns**, NOT a writer-claude tool call. Sammy's 2026-05-14 objection ("one Claude can't call another Claude") doesn't apply.

### STEP 6 — CI gate + auto-merge
- `gh pr checks <pr#> --watch` polls until green
- On green: `gh pr merge <pr#> --squash --delete-branch`
- On failure: detailed Discord post + HALT

### STEP 7 — Post-merge auto-deploy + watchdog
- Post-merge hook: `git pull` + `docker compose up -d --build` for the affected service
- 10-minute health-degrade monitor compares pre-deploy baseline (snapshot success rate, container restart count, error log rate) vs post-deploy
- On regression > threshold: auto-revert via `git revert` + redeploy
- All transitions Discord-posted

## Acceptance criteria

| # | Criterion |
|---|---|
| AC1 | Simulated alert (kill tte-1 → triggers container-restart) → investigator spawn → Discord diagnosis → writer spawn opens PR → reviewer spawn posts review → on green CI + approve → auto-merge + auto-deploy fires, all within 10 min of original alert |
| AC2 | Watchdog measures regression on baseline metrics (snapshot success rate, restart delta, error log rate) over 10 min post-deploy; threshold breach → `git revert` + redeploy |
| AC3 | Pre-commit + reviewer-Claude veto prevent secrets / `.env*` / credential patterns from being committed |
| AC4 | Max 2 PR opens per source alert ID, then HALT + Discord-page Sammy (no infinite spawn loops) |
| AC5 | E2E smoke test (kill tte-1 → verify auto-PR + auto-merge + auto-deploy + watchdog) passes from cold-boot |

## Risks to design around

1. **Infinite spawn loops**: writer creates broken PR → reviewer rejects → writer retries → ad infinitum. Cap retries (AC4).
2. **Auto-deploy regressions**: watchdog must compare against real baseline, not just "errors went up." Reuse the existing `tte-checks.*` scripts as the regression-signal source (they already dedupe via `/opt/stockbuddy/cc-state/check-state/`).
3. **Secret exfiltration**: writer Claude must NOT commit anything from `/opt/stockbuddy/secrets/` or any matched credential pattern. Pre-commit hook gate.
4. **gh auth scope**: cc-trigger.service runs as `stockbuddy` user. Use deploy-key-style PAT scoped to TTE + SB only, OR a GitHub App with limited install. Don't reuse Sammy's personal `gh auth`.
5. **Spawn-of-spawn confusion**: Sammy's 2026-05-14 objection — orchestration must be **cc-trigger's `server.js`**, not a writer-Claude tool call. Writer Claude is a subprocess of server.js; reviewer Claude is a separate subprocess of server.js. They never call each other directly.

## Reference docs in repo

- `.claude/phase6-spec-2026-05-14.md` — original (descoped) spec with full architecture
- `.claude/monitoring-run-criteria.md` — criteria for when to fire watchdog regression alerts
- `.claude/coda-closure-2026-05-14.md` — context on why Phase 6 4-7 was dropped on 2026-05-14
- `.claude/diagnosis-2026-05-14.md` — incident report demonstrating the investigator's analytical capability
- `/opt/stockbuddy/cc-trigger/server.js` (KVM8) — current Discord-only handler; add post-investigation hooks for steps 4-7
- `/opt/stockbuddy/monitoring/checks/*.sh` (KVM8) — existing check scripts that already POST to cc-trigger
- GitHub PRs #39 + #40 — reference for how manual writer-claude flow currently produces patches

## Out of scope

- Cross-repo orchestration (single-repo TTE + SB for now)
- Multi-VPS coordination
- Replacing the existing 6 monitoring checks (reuse as-is)

## Estimated effort

8–12 hours focused work. Most of it is wiring the spawn-orchestration logic in `server.js`, plus a real `gh` auth dance for the bot account. Wire-up of the spawn ordering + secret-veto + watchdog regression detector is the hard part — the actual PR-opening and merge-and-deploy primitives are just `gh` + `docker compose` calls.

## Notes

- Created 2026-05-15 12:13 IST after manual fix of the `requests` regression. The fix was identical to the investigator's auto-produced patch — just took 1h 21m of human latency to apply.
- This task is the natural follow-up to the 2026-05-14 monitoring/cc-trigger work; that work proved the alarm + analysis layer; this task proves the action layer.
- Coda MCP was disconnected at creation; paste this file's contents into the TTE/SB task board manually, OR after Coda MCP is restored ask Claude to upsert it.
