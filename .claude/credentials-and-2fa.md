# TTE bot credentials + 2FA

## Credentials file (do NOT commit / echo)

The live TradingView account email + password are kept at:

```
C:\Users\dassa\Passwords and tokens\Tradingview accounts credentials.md
```

Use the `Read` tool whenever you need them. Never paste them into chat, log them, or copy them into any other file.

## 2FA status as of 2026-05-15

TradingView's "suspicious activity" detector keeps re-enabling 2FA on the bot account regardless of CLAUDE.md's "2FA must be disabled" rule.

**Auto-2FA via pyotp is currently DISABLED.** PR #40 shipped the pyotp integration (`tte/browser/tradingview.py::_maybe_auto_submit_totp()`), but the base32 secret captured during the 2026-05-15 re-setup (`4ZE3CWH77ER37PSQ`) turned out to NOT be the secret TV actually stored — TV rejected every code derived from it with `"Incorrect verification code (403)"`, even when injected via the proven-working DevTools method. Secret was removed from `/opt/stockbuddy/secrets/.env.tte.1`. The pyotp code path in `sign_in()` short-circuits when the env var is absent (backward-compat preserved).

## Current recovery procedure for container restarts

Until the correct TOTP secret is captured, **use a backup code** to bypass 2FA. **TradingView backup codes are reusable** (verified 2026-05-15 — Nili logged in with a code that Sammy is still also using) — they're not single-use like most 2FA systems. So once you have a set of 6, they're effectively permanent until Sammy explicitly regenerates them. Pick any code from the file:

1. Read backup codes from `C:\Users\dassa\Passwords and tokens\tradingview backup codes.txt`. The file uses `# CODE -- USED <date>` to mark consumed codes.
2. Start tte-1: `docker compose up -d tte-1` from `/opt/stockbuddy` on KVM8.
3. Wait for the log line `Waiting up to 60s for sign-in (enter 2FA code if prompted)`.
4. Inject the next unused backup code via the DevTools script:
   ```bash
   scp tte_2fa_inject.py root@168.231.103.163:/tmp/
   ssh root@168.231.103.163 \
     "docker cp /tmp/tte_2fa_inject.py tte-1:/tmp/tte_2fa_inject.py && \
      docker exec --user root tte-1 chmod 644 /tmp/tte_2fa_inject.py && \
      docker exec tte-1 python3 /tmp/tte_2fa_inject.py 'BACKUPCODE'"
   ```
   The inject script auto-reads the live DevTools port from `/home/tte/chrome-profile/TTE/DevToolsActivePort` inside the container. Template lives at `C:/Users/dassa/AppData/Local/Temp/tte_2fa_inject.py`.
5. Within ~30s, log shows `Successfully signed in to TradingView` → `Browser ready` → maintenance loop runs.
6. No need to mark codes as "used" — they're reusable.

Backup code budget: TV's "Generate new codes" flow regenerates the ENTIRE batch — all prior codes are invalidated atomically. Since codes are reusable, regenerating is only necessary if Sammy explicitly wants a fresh set (e.g., after sharing a code with someone like Nili and now wanting to rotate). As of 2026-05-15 06:08 UTC: 6 active codes in the file, none consumed by mere use.

### How to regenerate backup codes autonomously

The local Chrome attached to `chrome-devtools-mcp` (TTE profile, Sammy's username `SamaaraDas`) can run this end-to-end without manual interaction:

1. Stop tte-1 first: `docker stop tte-1` — avoids the "Session disconnected — only one session allowed per user" race when the local Chrome signs in.
2. Local Chrome navigates to `https://www.tradingview.com/accounts/signin/`, fills email/password (read from `Tradingview accounts credentials.md`), submits.
3. 2FA prompt appears — inject a backup code via `evaluate_script` (native value setter + dispatch input/change/keydown). Do NOT use `mcp__chrome-devtools__fill` for React-controlled 2FA inputs; React state doesn't see the value change. Don't bother trying the `id_code` selector — use the type=text fallback when the form has exactly one input.
4. Navigate to `https://www.tradingview.com/settings/#account-settings` (NOT `/u/#account-security` — that redirects to the public profile).
5. Click "Generate new codes" button → TV prompts for the current password.
6. Fill the password (same native-setter trick), click Continue.
7. TV displays 6 new backup codes in a modal — read them via `evaluate_script` against the modal's StaticText elements.
8. Click "Copy codes and continue" to finalize.
9. Persist the codes to `C:\Users\dassa\Passwords and tokens\tradingview backup codes.txt`.
10. Start tte-1 again: `docker compose up -d tte-1`. If the cookie volume is fresh / invalidated, inject the FIRST new backup code into tte-1's 2FA prompt via the existing `tte_2fa_inject.py` DevTools script. If cookies survived, tte-1 will sign in automatically.

### Important behavioral note (verified 2026-05-15)

TV's "Session disconnected — only one session allowed" modal that pops up when signing in from a second browser does NOT necessarily invalidate the cookies in the FIRST session's user-data-dir. After signing in via local Chrome and burning through the 2FA flow, tte-1's existing cookies from the earlier-today backup-code sign-in were STILL VALID — tte-1 restarted and reached "Browser ready" without seeing the 2FA prompt at all.

### Why does the container survive once signed in?

Selenium-controlled Chrome persists cookies in the `tte1-userdata` Docker volume (`/home/tte/chrome-profile/TTE/Default`). Once a successful sign-in lands the session cookies, subsequent container restarts can re-use them — `sign_in()` finds the products menu within the initial 5s wait and skips the credentials + 2FA flow entirely. The 2FA pain only happens when:

- Cookies expire (TV server-side session timeout)
- Cookies get invalidated (suspicious-activity flag)
- The user-data-dir volume is wiped / recreated

## Pyotp auto-2FA work — PARKED, NOT BLOCKING

PR #40 shipped the pyotp `_maybe_auto_submit_totp` path with the correct architecture (JS event dispatch, URL-gated polling, input-count-gated fallback). The blocker is that TV's "Disable 2FA" flow requires an email/SMS verification step which can't be fully automated without reading Sammy's inbox. Until that's available:

- **Backup-code workflow above is the primary recovery path.** It works, it's reliable, it's documented end-to-end, and it can be re-run autonomously when codes run low.
- The pyotp code in `tte/browser/tradingview.py::_maybe_auto_submit_totp()` remains in the image but inert (no `TRADINGVIEW_TOTP_SECRET` in env). When/if a verified-correct secret becomes available, populate the env var and the path reactivates with no code changes.

Skip directly to writing an unverified secret to env is what caused the 2026-05-15 90-min outage. Don't repeat that.
