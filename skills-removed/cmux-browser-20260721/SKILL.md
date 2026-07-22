---
name: cmux-browser
description: End-user browser automation with cmux. Use when you need to open sites, interact with pages, wait for state changes, and extract data from cmux browser surfaces.
---

# Browser Automation with cmux

Use this skill for browser tasks inside cmux webviews.

## Focus policy (MANDATORY)

Browser automation must not change the user's active workspace, pane, or surface unless
the user explicitly asks to switch focus.

- Always create browser surfaces with `cmux browser open <url> --focus false`, even on
  cmux versions where false is already the CLI default.
- When using `cmux new-surface --type browser`, always pass `--focus false`.
- Do not use `cmux browser tab new`, `cmux open <url>`, the macOS `open` command, or a
  clicked terminal link to create an automation target. Those paths can select the new
  browser tab or pane.
- Prefer an existing matching browser surface when one is already open.
- NEVER pass `--focus true` or call a focus command. "Open it", "show it", "open it
  here in a tab", "display it" are all requests to CREATE the surface, NOT to steal
  focus — the user may be working in another workspace, and `--focus true` switches
  their active workspace mid-task. Open with `--focus false` and let the end-of-turn
  notification bring them back.
- The ONLY exception: the user uses the literal words "focus", "switch me to it",
  "take me there", or equally unambiguous switch-my-focus language in their CURRENT
  message. When in doubt, do not focus.

## Stale JS / HTTP cache (MANDATORY — do not ignore)

WKWebView caches aggressively. If a localhost app ever served
`Cache-Control: public, max-age=…, immutable` on **stable** asset URLs
(e.g. Next.js `/_next/static/chunks/...` in **dev**), cmux will keep
serving **old JS for up to a year** even after Fast Refresh and reloads.

**Symptoms (this is cache, not your bug):**
- Source and `.next` show the new value; network/UI still behaves like old code
- `curl -sI` shows new headers/content; the open tab does not
- `fetch(url, {cache:'no-store'})` from eval sees new code; script tags do not

**Permanent prevention (portal):**
- `server.mjs` forces `no-store` on `/_next/*` in development
- `next.config.mjs` must **not** set `immutable` / year-long max-age on `/_next/static` when `NODE_ENV !== 'production'`

**If you suspect stale cache — purge then reload (auth preserved):**

```bash
/Users/michaelsmit/ai-context/skills/cmux-browser/scripts/cmux-bust-http-cache.sh \
  --reload surface:N \
  --verify http://localhost:3000/_next/static/chunks/webpack.js
```

Expect verify line: `cache-control: no-store` (or `must-revalidate`) — **never** `immutable` on localhost dev.

**Agent rule:** After editing frontend code, if UI results disagree with source for >1 attempt, run `cmux-bust-http-cache.sh --reload <surface>` **before** deep-diving “logic bugs”. Do not spend the session fighting cache.

Does **not** clear cookies/localStorage (only NetworkCache). Prefer this over switching host (`127.0.0.1` vs `localhost`) or logging out.

**If the bust script does NOT fix it — the surface's web process has the old JS in its
in-memory cache.** That cache survives the NetworkCache purge, `reload`, and even
navigating to a different URL. Proof pattern: add a marker string to the source (e.g. a
`[fx1]` suffix on a console.log), confirm `curl`/in-page `fetch` of the chunk shows the
marker, but the executed log doesn't. The ONLY fix is a **new browser surface** (new web
process; cookies/login persist because WebsiteData is shared):

```bash
cmux --json browser open <same-url> --focus false  # lands in the same pane without stealing focus
cmux close-surface --surface surface:OLD   # drop the poisoned tab
```

Never declare frontend code "verified" from a surface that has ever shown this symptom —
replace the surface first, then verify.

## Core Workflow

0. If the task targets a tab the user ALREADY has open, find it first (see "Find an Existing Browser Surface" below) instead of opening a new one.
1. Open or target a browser surface.
2. Verify navigation with `get url` before waiting or snapshotting.
3. Snapshot (`--interactive`) to get fresh element refs.
4. Act with refs (`click`, `fill`, `type`, `select`, `press`).
5. Wait for state changes.
6. Re-snapshot after DOM/navigation changes.

```bash
cmux --json browser open https://example.com --focus false
# use returned surface ref, for example: surface:7

cmux browser surface:7 get url
cmux browser surface:7 wait --load-state complete --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
cmux browser surface:7 fill e1 "hello"
cmux --json browser surface:7 click e2 --snapshot-after
cmux browser surface:7 snapshot --interactive
```

## Find an Existing Browser Surface

When the task is to act on a tab the user ALREADY has open (e.g. "the browser in the
other pane", "my open tab"), DISCOVER it — do not `browser open` a new one. The one
command that answers this is `cmux tree --all`: it lists every window/workspace/pane and,
for each surface, its type, title, and current URL.

```bash
cmux tree --all                              # full layout: shows [browser] surfaces + URLs
cmux tree --all | grep -i browser            # just the browser surfaces
```

Each `[browser]` line gives you the `surface:N` ref and its URL directly, e.g.:
`surface:18 [browser] "Aura Portal" ... http://localhost:3000/...` — then act on `surface:18`.

`cmux identify --json` only reports the CALLER/focused surface, so it is NOT how you find a
tab in another pane. Use `tree --all` for that. (Narrower listers also exist:
`cmux list-pane-surfaces`, `cmux list-panes` — but `tree --all` is the fast path.)

## Surface Targeting

```bash
# identify current context (caller/focused surface ONLY)
cmux identify --json

# open routed to a specific topology target (CREATES a new surface)
cmux browser open https://example.com --workspace workspace:2 --window window:1 --focus false --json
```

Notes:
- CLI output defaults to short refs (`surface:N`, `pane:N`, `workspace:N`, `window:N`).
- UUIDs are still accepted on input; only request UUID output when needed (`--id-format uuids|both`).
- Keep using one `surface:N` per task unless you intentionally switch.

## Wait Support

cmux supports wait patterns similar to agent-browser:

```bash
cmux browser <surface> wait --selector "#ready" --timeout-ms 10000
cmux browser <surface> wait --text "Success" --timeout-ms 10000
cmux browser <surface> wait --url-contains "/dashboard" --timeout-ms 10000
cmux browser <surface> wait --load-state complete --timeout-ms 15000
cmux browser <surface> wait --function "document.readyState === 'complete'" --timeout-ms 10000
```

## Common Flows

### Form Submit

```bash
cmux --json browser open https://example.com/signup --focus false
cmux browser surface:7 get url
cmux browser surface:7 wait --load-state complete --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
cmux browser surface:7 fill e1 "Jane Doe"
cmux browser surface:7 fill e2 "jane@example.com"
cmux --json browser surface:7 click e3 --snapshot-after
cmux browser surface:7 wait --url-contains "/welcome" --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
```

### Clear an Input

```bash
cmux browser surface:7 fill e11 "" --snapshot-after --json
cmux browser surface:7 get value e11 --json
```

### Stable Agent Loop (Recommended)

```bash
# navigate -> verify -> wait -> snapshot -> action -> snapshot
cmux browser surface:7 get url
cmux browser surface:7 wait --load-state complete --timeout-ms 15000
cmux browser surface:7 snapshot --interactive
cmux --json browser surface:7 click e5 --snapshot-after
cmux browser surface:7 snapshot --interactive
```

If `get url` is empty or `about:blank`, navigate first instead of waiting on load state.

## Deep-Dive References

| Reference | When to Use |
|-----------|-------------|
| [references/commands.md](references/commands.md) | Full browser command mapping and quick syntax |
| [references/stale-http-cache.md](references/stale-http-cache.md) | Stale JS / immutable Cache-Control / cmux NetworkCache purge |
| [references/snapshot-refs.md](references/snapshot-refs.md) | Ref lifecycle and stale-ref troubleshooting |
| [references/authentication.md](references/authentication.md) | Login/OAuth/2FA patterns and state save/load |
| [references/authentication.md#saving-authentication-state](references/authentication.md#saving-authentication-state) | Save authenticated state right after login |
| [references/session-management.md](references/session-management.md) | Multi-surface isolation and state persistence patterns |
| [references/video-recording.md](references/video-recording.md) | Current recording status and practical alternatives |
| [references/proxy-support.md](references/proxy-support.md) | Proxy behavior in WKWebView and workarounds |

## Ready-to-Use Templates

| Template | Description |
|----------|-------------|
| [templates/form-automation.sh](templates/form-automation.sh) | Snapshot/ref form fill loop |
| [templates/authenticated-session.sh](templates/authenticated-session.sh) | Login once, save/load state |
| [templates/capture-workflow.sh](templates/capture-workflow.sh) | Navigate + capture snapshots/screenshots |

## Limits (WKWebView)

These commands currently return `not_supported` because they rely on Chrome/CDP-only APIs not exposed by WKWebView:
- viewport emulation
- offline emulation
- trace/screencast recording
- network route interception/mocking
- low-level raw input injection

Use supported high-level commands (`click`, `fill`, `press`, `scroll`, `wait`, `snapshot`) instead.

## Troubleshooting

### `js_error` on `snapshot --interactive` or `eval`

Some complex pages can reject or break the JavaScript used for rich snapshots and ad-hoc evaluation.

Recovery steps:

```bash
cmux browser surface:7 get url
cmux browser surface:7 get text body
cmux browser surface:7 get html body
```

- Use `get url` first so you know whether the page actually navigated.
- Fall back to `get text body` or `get html body` when `snapshot --interactive` or `eval` returns `js_error`.
- If the page is still failing, navigate to a simpler intermediate page, then retry the task from there.
