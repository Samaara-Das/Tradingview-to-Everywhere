# Coda task closure — i-iNXjRwYS9h ("Server migration & docker setup")

**Status**: Done (pending manual Coda row update — Coda MCP was disconnected at closure time).
**Closed**: 2026-05-14
**Closed by**: TTE-Claude (autonomous /goal run)

---

## Original scope vs actual delivery

The Coda task as originally written ("check if the claude code manager is running fine on the VPS" + post-migration health) **did not anticipate the snapshot-pipeline blackout** that turned out to be the dominant issue. The autonomous run pivoted to incident response while still satisfying the original CCM-verification intent (cc-trigger.service is Active and now routes Discord digests instead of Telegram).

What actually shipped in this /goal run:

| # | Task | Outcome |
|---|------|---------|
| 6 | Real-root-cause investigation via live tte-1 devtools | ✅ Identified: TV session logged out for 6 days, owner-only chart layout served "Chart Not Found" placeholder, every Selenium selector hit 0 elements |
| 11 | Patch code based on findings | ✅ Branch `fix/snapshot-pipeline-2026-05-14`, atomic commits, login-state guard + recovery |
| 12 | PR + sub-agent review + self-merge | ✅ PR #39, code-reviewer sub-agent caught 2 HIGH issues (guard fired too late, `start_fresh` could wipe alerts), fixed in `c54c062`, squash-merged |
| 9 | Rebuild tte:phase4 image | ✅ New image `sha256:31d4cd170554...` built. 4 unupstreamed server-only patches preserved (tframe_skip, sleep(2) tightening, bus_log_try_except, launcher_syspath+sign_in_call in backfill script) |
| 13 | One-shot deploy | ✅ Container restarted on new image. 2FA blocked sign-in initially → resolved via DevTools-injection of user's 2FA code. Container now running cleanly |
| 14 | Verify 5 fresh snapshots | ✅ 5/5 post-deploy PNGs render Trade Drawer V2 + REVERSED TP/SL layout correctly (mongo `stopLoss` → on-chart `TP`, mongo `takeProfit` → on-chart `SL`) |
| 17 | 6 TTE monitoring checks + systemd timer | ✅ Installed at `/opt/stockbuddy/monitoring/checks/tte-*.sh` + `tte-checks.timer` firing every 5 min. All 6 checks return OK in current state |
| 18 | cc-trigger Telegram → Discord webhook | ✅ `server.js` rewritten, Telegram code path removed entirely, Discord embeds with severity colors. Webhook URL stored in `/opt/stockbuddy/secrets/.env.cc` (chmod 600, stockbuddy-owned), NOT committed |
| 19 | E2E smoke test | ✅ 6 alerts fired (1 real `tte-webhook-delivery` failure during install + 1 smoke + 4 simulated). 0 Discord delivery errors. Each cc-trigger spawn produced a meaningful investigation summary |
| 16 | Coda closure | ⚠️ Coda MCP disconnected; fallback path = this file. Sammy to manually mark Coda row Done |

## Key artifacts

| Type | Reference |
|------|-----------|
| PR | https://github.com/Samaara-Das/Tradingview-to-Everywhere/pull/39 (merged as `40311f7`) |
| Diagnosis | `.claude/diagnosis-2026-05-14.md` |
| New image | `tte:phase4` @ `sha256:31d4cd170554e81b30045e1af49a5aeac89f0d6521db317d9ee70d3355ad6432` |
| Verified PNGs | https://www.tradingview.com/x/4RHJmY9U/ (GBPUSD), `/ep5OzD92/` (ODFL), `/rcicez3Y/` (BLDR), `/gLrgpp8v/` (QUBT), `/Ndymr2WU/` (ADSK) |
| Monitoring | `/opt/stockbuddy/monitoring/checks/tte-{snapshot-success-rate,snapshot-failed-burst,change-symbol-errors,alert-sidebar-errors,container-restart,webhook-delivery}.sh` + `tte-checks.timer` |
| cc-trigger | `/opt/stockbuddy/cc-trigger/server.js` (Telegram-free), old version backed up to `server.js.bak.20260514-164227` |
| Discord webhook | URL in `/opt/stockbuddy/secrets/.env.cc` as `DISCORD_WEBHOOK_URL` (not committed) |
| Learnings | `.claude/learnings.md` |

## Limitations & follow-ups

- **2FA recurrence risk**: TV re-enabled 2FA on the account; every container restart now requires a 6-digit code injection via DevTools. Long-term fix: add `pyotp` + `TRADINGVIEW_TOTP_SECRET` env to `sign_in()`. Tracked but not in this run.
- **Off-screen-entry-time**: 1 of 5 verified PNGs (ADSK) renders the entry/TP/SL labels at the far right with the entry-time marker off-screen. Cosmetic, not a label-correctness issue.
- **Orphan-image rollback**: Pre-deploy `docker tag` failed because the old image had a missing content digest. No rollback path existed after `docker rm tte-1`. Mitigation in place: new image is built and viable; worst-case is rebuild-from-source.
- **#19 smoke methodology**: 5 of 6 simulations used direct `curl POST` to `127.0.0.1:8765/alert` rather than condition-triggered failures (avoiding destructive Mongo writes / forced container restarts). The 6th alert (`tte-webhook-delivery`) was a natural-condition failure during installation that completed the loop end-to-end (alert → cc-trigger → claude spawn → Discord digest → exit code 0).

## What's NOT done (intentional, out-of-scope)

- Phase 6 auto-review / auto-merge / auto-deploy / watchdog (descoped 2026-05-14 per Sammy: "one Claude can't call another Claude")
- TOTP support in `sign_in()` (recommended follow-up — tracked above)
- Off-screen-entry-time fix (separate bug, not load-bearing)

## Discord pings sent during this run

Phase #12 (PR merge) → #9 (image build) → #13 (deploy success) → #14 (5 PNGs verified) → #19 (smoke) → this closure. All HTTP 204.
