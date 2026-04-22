---
name: home-assistant
description: Interact with the user's local Home Assistant instance — list entities/devices, read/control states, call services, and manage automations. Use when the user mentions Home Assistant, HA, smart home, automations, lights/switches/sensors they control, or references entities like `light.*`, `switch.*`, `sensor.*`.
---

# Home Assistant

Talk to the user's local Home Assistant via its REST + WebSocket APIs.

## Config

Credentials are at `~/.claude/skills/home-assistant/config.json` (created by the pi agent). Do **not** reprint or log the token.

```json
{ "url": "http://homeassistant.local:8123/", "token": "<long-lived>" }
```

If the file is missing, say so and stop — don't invent a URL.

## Preferred interface: the helper script

A Node helper lives next to this file at `~/.claude/skills/home-assistant/ha.mjs`. It handles config loading, auth, JSON, and (when needed) WebSocket. Use it for everything — it works on this Windows/git-bash setup where `jq` isn't installed.

```bash
node ~/.claude/skills/home-assistant/ha.mjs <command> [args...]
```

Commands:

| Command | Purpose |
|---|---|
| `entities [domain] [name]` | Compact table of entity_id / state / friendly_name. `domain` like `light`, `switch`, `sensor`. `name` is a substring match on entity_id or friendly_name. |
| `services [domain]` | List available services, optionally filtered to one domain. |
| `automations` | List `automation.*` entities with state and last_triggered. |
| `devices [filter]` | Physical devices from the device registry (WebSocket). Filter matches name, manufacturer, model, id. |
| `entity-registry [filter]` | Entity registry entries (WebSocket) — includes platform, device_id, area_id, disabled_by. Richer than `/api/states`. |
| `areas` | Area registry (WebSocket) — area names and ids, used to correlate entities/devices to rooms. |
| `rest <METHOD> <PATH> [JSON_BODY]` | Raw REST call. Use for anything not covered above. |

Examples:
```bash
node ~/.claude/skills/home-assistant/ha.mjs entities light kitchen
node ~/.claude/skills/home-assistant/ha.mjs services light
node ~/.claude/skills/home-assistant/ha.mjs automations
node ~/.claude/skills/home-assistant/ha.mjs devices "TP-Link"
node ~/.claude/skills/home-assistant/ha.mjs rest GET /api/states/sun.sun
node ~/.claude/skills/home-assistant/ha.mjs rest POST /api/services/light/turn_on '{"entity_id":"light.kitchen","brightness_pct":60}'
```

The script exits non-zero and writes the HTTP error to stderr on failure.

## REST endpoint map

For `rest` calls, the common paths:

| Purpose | Method | Path |
|---|---|---|
| All entity states | GET | `/api/states` |
| One entity | GET | `/api/states/<entity_id>` |
| Force a state | POST | `/api/states/<entity_id>` with `{state, attributes}` |
| List services | GET | `/api/services` |
| Call a service | POST | `/api/services/<domain>/<service>` with JSON body |
| History | GET | `/api/history/period/<ISO>?filter_entity_id=...` |
| Logbook | GET | `/api/logbook/<ISO>` |
| Config | GET | `/api/config` |
| Error log | GET | `/api/error_log` |
| Render template | POST | `/api/template` with `{"template":"..."}` |
| Check config | POST | `/api/config/core/check_config` |
| Reload automations | POST | `/api/services/automation/reload` |

Note: this install returns 404 for bare `/api/` — use `/api/config` as a sanity check instead.

## Automations

Config-API endpoints for CRUD:

| Action | Method | Path |
|---|---|---|
| Read one | GET | `/api/config/automation/config/<id>` |
| Create/update | POST | `/api/config/automation/config/<id>` (body is the automation) |
| Delete | DELETE | `/api/config/automation/config/<id>` |

For `<id>`, use epoch seconds when creating (`date +%s`). After any write, call `POST /api/services/automation/reload` and verify the new `automation.<slug>` appears in `node ha.mjs entities automation`.

Automation body shape:
```json
{
  "alias": "Porch light at sunset",
  "description": "",
  "trigger": [{ "platform": "sun", "event": "sunset" }],
  "condition": [],
  "action": [{ "service": "light.turn_on", "target": { "entity_id": "light.porch" } }],
  "mode": "single"
}
```

## REST vs WebSocket — pick the right one

HA exposes two parallel APIs. Use both; they aren't interchangeable.

| Need | Use | Why |
|---|---|---|
| Current state of an entity | REST `/api/states` | Snapshot read, lightweight. |
| Call a service (turn on, set brightness, trigger automation) | REST `/api/services/...` | Operational; REST is the simplest fit. |
| Render a template, history, logbook, config, error log | REST | Only exposed over REST. |
| **Device registry** (manufacturer, model, hardware) | WebSocket `config/device_registry/list` | Not exposed over REST. |
| **Entity registry** (platform, device_id, area_id, disabled) | WebSocket `config/entity_registry/list` | Richer than `/api/states`; REST only has runtime state. |
| **Area registry** (rooms) | WebSocket `config/area_registry/list` | Not exposed over REST. |
| Anything labelled `config/*/list` in the HA WS docs | WebSocket | Registry-style metadata is WS-only. |

Rule of thumb: **operational → REST, registry/metadata → WebSocket.** The `ha.mjs` helper hides the transport choice; pick the command that matches intent and it routes correctly.

When the user says "devices", clarify if unsure: physical hardware (`devices`) vs controllable things (`entities`). For "what lights do I have", `entities light` is what they want. For "what Aqara sensors do I have", `devices Aqara`.

## Rules

- Read config each invocation; never assume values from earlier turns.
- Never print, log, or echo the token.
- Before destructive or physical-world actions (delete automation, unlock a lock, open a garage, change HVAC setpoint far from current), confirm the exact `entity_id` and desired target state with the user first.
- Summarise — don't dump raw `/api/states` responses into chat. 500+ entities is typical; filter and show a short table.
- After automation writes, always `automation.reload` and verify the entity appears.
- If `homeassistant.local` fails to resolve, ask the user for a LAN IP — don't guess.
