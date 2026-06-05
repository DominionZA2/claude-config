---
name: aura-portal
description: Log into and operate the Aura Portal (v2-portal, Next.js app at localhost:3000). Use when asked to log in as a user, navigate to a portal page, or drive the portal UI. Pairs with the cmux-browser skill for actual browser control.
---

# Aura Portal

Next.js app, served at `http://localhost:3000` (locale-prefixed routes, e.g. `/en/...`).
Drive it with the **cmux-browser** skill. Find the open tab with `cmux tree --all | grep -i browser`; if none, `cmux browser open http://localhost:3000`.

## Credentials

Stored locally, NEVER committed: `~/.claude/skills/aura-portal/creds.local.json`
(gitignored). Shape: `{ "users": { "<alias>": { "platform": "test|live", "email": "...", "password": "..." } } }`.
If the file is missing or the alias isn't there, ask the user for it.

## Log in

1. Go to `http://localhost:3000/en/login` (snapshot to get fresh refs).
2. Click the platform button: **"Live Platform"**, **"Test Platform"**, or **"Custom"** (default Test for dev).
3. `fill` the **"Enter your Email address"** textbox, then **"Enter your password"** textbox.
4. Click **"Sign In"**. Wait for redirect off `/login`.
5. **First-login acknowledgments (EULA + TOS):** a fresh account shows a one-off modal ("Welcome to Aura Portal! … review and accept our License Agreement and Terms of Service"). Expected and authorized — accept to proceed; it won't reappear on later logins. Flow per document (`enhanced-compliance-modal.tsx`): Review → "View Full Agreement Document" → **scroll the PDF container to the bottom** → tick the "I have read and understood" checkbox → 5s min-read timer → Agree. **Gotcha:** the Agree gate (`documentViewed && scrolledToBottom && readTimeElapsed && confirmationChecked`) only flips `scrolledToBottom` on a *real* scroll event — ref-clicking "Scroll to Bottom" does nothing. Use `cmux browser <surface> scroll --selector "div.border.border-neutral-200" --dy 6000`; the checkbox + Agree button only render *after* that. The doc renders as blank PDF.js canvases in test (no content) — that's fine, scroll still works. (Known bug: the 30s manual-download fallback never fires — stale closure on `fallbackMethod` in that component.)

## Log out

User menu is a headlessui `Menu` (top-right "Michael Smit ▾"), logout = `logout(false)` → clears auth, redirects to `/login`. **Gotcha:** the trigger is a headlessui `MenuButton` — a synthetic `.click()` does NOT open it, and its items render in a portal (absent from DOM until open). To open: `focus` the button, then send a real **Enter** keypress. Then click the **"Sign Out"** button and wait for `/login`.

## Navigation map (task → route)

Routes are locale-prefixed and take `?companyId=&brandId=&platform=` query params.

| Task | Route |
|------|-------|
| Roles & permissions | `/en/brand/system-admin/roles` |

(Append new destinations here as we learn them.)

## Test status — SOURCE OF TRUTH (ordered by stakeholder enum)

The test: **does the Roles & Permissions "Stakeholder type" dropdown show the correct options per login, in brand scope and store scope.** Keep this table current as the single source of truth. Legend: ✅ tested · ⬜ to test · ❌ account doesn't exist yet.

| # | Stakeholder | Email | Brand scope | Store scope |
|---|-------------|-------|-------------|-------------|
| 1 | Cosoft | `msmit@cosoft.co.za` | ✅ tested | ⬜ to test |
| 2 | Brand Owner | `msmit+brand-owner@cosoft.co.za` | ✅ tested | ⬜ to test |
| 3 | Brand User | `msmit+brand-user@cosoft.co.za` | ✅ tested | ⬜ to test |
| 4 | Store Owner | `msmit+store-owner@cosoft.co.za` | ✅ tested | ⬜ to test |
| 5 | Store User | `msmit+store-user@savitar.co.za` | ⬜ to test | ⬜ to test |

All `msmit+` aliases share the primary password. Aliases on `@cosoft.co.za` route to the primary inbox; `@savitar.co.za` is a separate brand/domain. EULA/TOS acknowledgments are NOT part of the test — just a one-off login gate (see Log in §5).

Read-only test DB (`reports` user): `server=db.auracloud_test;port=3306`, run via the local `MySql` Docker container's client. Accounts live in `aura_cloud_auth.User` (`Email`, `StakeholderId`); stakeholder names in `aura_cloud_auth.Stakeholder`. Passwords are bcrypt (`$2b$10$`, salted) — never compare hashes to infer equality; log in to test.

## Create a test user — PROVEN RECIPE (API + reset-token, no UI, no email)

Do it via the API, not the website (the create-user modal's headlessui dropdowns don't open under automation). **The emailed-password path is DEAD on test** — the backend has no `SendGridTemplates:PortalPassword`, so create returns `HTTP 400 "...has not been configured"` — **but the user IS still persisted** (commit happens before the email). So ignore the 400 and set the password yourself via reset-token.

Test API base: `https://api.test.aurapos.com` (live = `api.aurapos.com`; from `platform-utils.ts`). Auth as **Cosoft** (`msmit@cosoft.co.za`) — only Cosoft outranks Brand Owner.

```bash
BASE=https://api.test.aurapos.com
# 1. token (login as Cosoft)
TOK=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d '{"EmailAddress":"msmit@cosoft.co.za","Password":"<primary>","SessionName":"React Portal"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["authToken"])')
# 2. a role of that stakeholder must exist (RoleIds is required). Find/confirm it:
curl -s "$BASE/v1/Roles/brands/46/stakeholders/2" -H "Authorization: Bearer $TOK"   # Brand Owner=2; existing role id 742
# (store-scope: $BASE/v1/Roles/brands/46/stores/10810/stakeholders/4 ; create with POST same path if none)
# 3. create user. Brand-scope: ?BrandId=46 only. Store-scope: ?BrandId=46&StoreId=10810. Stakeholder int per enum.
curl -s -X POST "$BASE/v1/users?BrandId=46" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
  -d '{"Id":0,"Name":"Michael","Surname":"The Brand Owner","Email":"msmit+brand-owner@cosoft.co.za","Stakeholder":2,"RoleIds":[742],"PortalUser":{"Id":0,"LoginName":"msmit+brand-owner@cosoft.co.za","IsEnabled":true}}'
# ^ expect HTTP 400 (SendGrid) — the user is created anyway. Get its PortalUserId from aura_cloud_auth.User.
# 4. set password to primary via reset-token (token row is saved before the email send, so it survives):
curl -s -X POST "$BASE/auth/requestpasswordreset" -H 'Content-Type: application/json' -d '{"EmailAddress":"<email>"}'
#    read token:  SELECT Token FROM aura_cloud_auth.PasswordResetToken WHERE LoginId=<PortalUserId> ORDER BY ExpiryDate DESC LIMIT 1;
curl -s -X POST "$BASE/auth/resetpassword" -H 'Content-Type: application/json' \
  -d '{"EmailAddress":"<email>","ResetToken":"<TOKEN>","Password":"<primary>","ConfirmPassword":"<primary>"}'
# 5. verify: POST /auth/login as the new user → expect a token.
```
`PasswordResetToken.LoginId` = the user's `PortalUserId` (not User.Id). Token is an 8-char uppercase GUID slice, plaintext in the DB.

## Stakeholder access rule (Roles & Permissions)

Enum: `Cosoft=1, BrandOwner=2, BrandUser=3, StoreOwner=4, StoreUser=5` (lower number = higher privilege). A user manages **their own level and everything with a higher enum number, and Cosoft is Cosoft-only**. Source: backend `StakeholderExtensions.GetAllowedStakeholders`; client `roles/utils/stakeholders.ts` `getAllowedStakeholderOptions`. The "Stakeholder type" dropdown **default** = the highest level they may manage:

| Logged-in as | Dropdown options | Default |
|--------------|------------------|---------|
| Cosoft | Cosoft, Brand Owner, Brand User, Store Owner, Store User | Cosoft |
| Brand Owner | Brand Owner, Brand User, Store Owner, Store User | Brand Owner |
| Brand User | Brand User, Store Owner, Store User | Brand User |
| Store Owner | Store Owner, Store User | Store Owner |
| Store User | Store User | Store User |

Roles are scoped **brand** (`brandId`, no `storeId`), **store** (`storeId`), **store-group** (`storeGroupId`), or **global** (Cosoft only) — test both brand and store contexts.

## UI automation gotchas (WKWebView + headlessui)

- **headlessui `Menu` / `Listbox` ignore synthetic `.click()`.** The user menu opens via `focus` + real **Enter**. The "Stakeholder type" `SingleSelect` (Catalyst `ListboxWrapper`) will **not** open via click *or* keyboard under automation (`aria-expanded` stays false). **To read its options without opening it, walk the React fiber and grab the `options` prop** — this is the live runtime value for the logged-in user:
  ```js
  const el=document.querySelector("button[aria-haspopup=listbox]");
  const k=Object.keys(el).find(k=>k.startsWith("__reactFiber$"));
  let n=el[k],found=null,h=0; while(n&&h<80){const p=n.memoizedProps; if(p&&Array.isArray(p.options)&&p.options[0]?.label){found=p.options;break;} n=n.return;h++;}
  JSON.stringify(found?.map(o=>o.label))
  ```
- **Custom dropdowns are not native `<select>`** and their options render in a portal only when open — `document.querySelectorAll("select")` returns nothing here.
- **Exact-match refs.** Grepping a snapshot for `Brand User` also matches the user-menu button "Michael The **Brand User**". Match the full ref line / disambiguate by `aria-haspopup` or exact text.
- **When the UI fights you, read the component** (this app is in `~/Source/cloud-worktrees/<task>/v2-portal`) instead of poking — it's faster and exact.
