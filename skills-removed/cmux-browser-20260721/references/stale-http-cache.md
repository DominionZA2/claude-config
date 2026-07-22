# Stale HTTP cache in cmux (WKWebView)

## Root cause

1. Next.js **dev** uses **stable** asset URLs under `/_next/static/chunks/...` (no content hash in the path for many chunks).
2. Portal `next.config.mjs` used to set:

   `Cache-Control: public, max-age=31536000, immutable`

   on `/_next/static/*` for **all** environments (including dev).
3. WKWebView (cmux browser) honours `immutable` and will **not revalidate** that URL for up to a year.
4. Code changes + Fast Refresh / soft reload still leave the **old JS** running in the tab.
5. Agents then waste long sessions believing the feature is broken.

Production is fine: hashed filenames mean new deploys are new URLs.

## Permanent fixes (already applied in main portal + API-763 worktree)

| Layer | What |
|-------|------|
| `server.mjs` | In `dev`, rewrite Cache-Control to `no-store, must-revalidate` for `/_next/*` and `/__nextjs*` |
| `next.config.mjs` | `/_next/static` uses `nextStaticCache`: no-store in non-production, immutable only in production |
| `start-dev-server.sh` | Copies canonical `server.mjs` guard into worktrees that lack `installDevNoStoreHeaders` |
| `cmux-bust-http-cache.sh` | Deletes cmux `NetworkCache` (not cookies) + optional surface reload |

## Agent procedure

1. Prefer prevention (server headers).
2. If UI ≠ source after one honest reload:

```bash
/Users/michaelsmit/ai-context/skills/cmux-browser/scripts/cmux-bust-http-cache.sh \
  --reload surface:N \
  --verify http://localhost:PORT/_next/static/chunks/webpack.js
```

3. Confirm verify output is **not** `immutable`.
4. Only then debug application logic.

## What NOT to do

- Do not switch `localhost` ↔ `127.0.0.1` as the primary fix (drops login; different origin).
- Do not clear the whole browser profile (logs the user out).
- Do not assume Fast Refresh always replaced the module WKWebView is executing.
- Do not trust `fetch(url)` without `cache: 'no-store'` as proof the **script tag** loaded fresh code.

## Manual verify

```bash
curl -sI "http://localhost:3000/_next/static/chunks/webpack.js" | grep -i cache-control
# expect: no-store (dev)
```
