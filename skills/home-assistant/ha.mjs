#!/usr/bin/env node
// Home Assistant helper. Reads config from ~/.pi/agent/home-assistant.json.
//
// Usage:
//   node ha.mjs rest <METHOD> <PATH> [JSON_BODY]
//     e.g. node ha.mjs rest GET /api/
//          node ha.mjs rest GET /api/states
//          node ha.mjs rest POST /api/services/light/turn_on '{"entity_id":"light.kitchen"}'
//
//   node ha.mjs entities [domainFilter] [nameFilter]
//     Compact table of entity_id | state | friendly_name, optionally filtered.
//
//   node ha.mjs devices [textFilter]
//     WebSocket call to config/device_registry/list (physical devices).
//
//   node ha.mjs services [domain]
//     Lists available services (optionally filtered to one domain).
//
//   node ha.mjs automations
//     Lists automation.* entities with their state and last_triggered.
//
// Output is plain text for `rest`/`entities`/`devices`/`services`/`automations`
// summaries, or raw JSON when the body looks like JSON. Exit code is non-zero
// on HTTP failure so callers can detect errors.

import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const CONFIG_PATH = join(dirname(fileURLToPath(import.meta.url)), "config.json");

function loadConfig() {
  if (!existsSync(CONFIG_PATH)) {
    console.error(`Missing config file: ${CONFIG_PATH}`);
    process.exit(2);
  }
  const cfg = JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
  if (!cfg.url || !cfg.token) {
    console.error(`Config at ${CONFIG_PATH} must have 'url' and 'token'.`);
    process.exit(2);
  }
  cfg.url = cfg.url.replace(/\/+$/, "");
  return cfg;
}

async function rest(method, path, body) {
  const cfg = loadConfig();
  const url = cfg.url + (path.startsWith("/") ? path : "/" + path);
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${cfg.token}`,
      "Content-Type": "application/json",
    },
    body: body ? body : undefined,
  });
  const text = await res.text();
  if (!res.ok) {
    console.error(`HTTP ${res.status} ${res.statusText}: ${text}`);
    process.exit(1);
  }
  return text;
}

async function websocket(messageId, payload) {
  const cfg = loadConfig();
  const wsUrl = cfg.url.replace(/^http/, "ws") + "/api/websocket";
  // Node 22 has a built-in WebSocket.
  return await new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const timeout = setTimeout(() => {
      try { ws.close(); } catch {}
      reject(new Error("Timed out talking to Home Assistant."));
    }, 10000);
    const finish = (fn) => { clearTimeout(timeout); try { ws.close(); } catch {} fn(); };
    ws.onerror = () => finish(() => reject(new Error(`Could not connect to ${wsUrl}`)));
    ws.onmessage = (event) => {
      const msg = JSON.parse(String(event.data));
      if (msg.type === "auth_required") { ws.send(JSON.stringify({ type: "auth", access_token: cfg.token })); return; }
      if (msg.type === "auth_invalid") { finish(() => reject(new Error(msg.message || "HA token rejected."))); return; }
      if (msg.type === "auth_ok") { ws.send(JSON.stringify({ id: messageId, ...payload })); return; }
      if (msg.id === messageId) {
        if (!msg.success) finish(() => reject(new Error(msg.error?.message || "WS call failed.")));
        else finish(() => resolve(msg.result));
      }
    };
  });
}

function formatEntitiesTable(items) {
  if (!items.length) return "(no matches)";
  const rows = items.map((s) => ({
    entity_id: s.entity_id,
    state: String(s.state).slice(0, 40),
    friendly_name: s.attributes?.friendly_name || "",
  }));
  const w = (k) => Math.max(k.length, ...rows.map((r) => r[k].length));
  const cols = ["entity_id", "state", "friendly_name"];
  const widths = Object.fromEntries(cols.map((c) => [c, w(c)]));
  const line = (r) => cols.map((c) => String(r[c]).padEnd(widths[c])).join("  ");
  const header = line(Object.fromEntries(cols.map((c) => [c, c])));
  const sep = cols.map((c) => "-".repeat(widths[c])).join("  ");
  return [header, sep, ...rows.map(line)].join("\n");
}

const [, , cmd, ...rest_args] = process.argv;

try {
  if (cmd === "rest") {
    const [method, path, body] = rest_args;
    if (!method || !path) { console.error("Usage: ha.mjs rest <METHOD> <PATH> [JSON_BODY]"); process.exit(2); }
    const text = await rest(method.toUpperCase(), path, body);
    process.stdout.write(text);
    if (!text.endsWith("\n")) process.stdout.write("\n");
  } else if (cmd === "entities") {
    const [domain, name] = rest_args;
    const all = JSON.parse(await rest("GET", "/api/states"));
    let filtered = all;
    if (domain) filtered = filtered.filter((s) => s.entity_id.startsWith(domain + "."));
    if (name) {
      const n = name.toLowerCase();
      filtered = filtered.filter((s) =>
        s.entity_id.toLowerCase().includes(n) ||
        String(s.attributes?.friendly_name || "").toLowerCase().includes(n)
      );
    }
    filtered.sort((a, b) => a.entity_id.localeCompare(b.entity_id));
    console.log(`Matched ${filtered.length} of ${all.length} entities`);
    console.log(formatEntitiesTable(filtered));
  } else if (cmd === "services") {
    const [domain] = rest_args;
    const all = JSON.parse(await rest("GET", "/api/services"));
    const list = domain ? all.filter((d) => d.domain === domain) : all;
    for (const d of list) {
      console.log(`\n== ${d.domain} ==`);
      for (const [svc, meta] of Object.entries(d.services || {})) {
        console.log(`  ${d.domain}.${svc}  — ${meta.description || meta.name || ""}`);
      }
    }
  } else if (cmd === "automations") {
    const all = JSON.parse(await rest("GET", "/api/states"));
    const autos = all.filter((s) => s.entity_id.startsWith("automation."));
    autos.sort((a, b) => a.entity_id.localeCompare(b.entity_id));
    console.log(`Automations: ${autos.length}`);
    for (const a of autos) {
      const lt = a.attributes?.last_triggered || "never";
      console.log(`- ${a.entity_id}  [${a.state}]  last_triggered=${lt}  alias="${a.attributes?.friendly_name || ""}"`);
    }
  } else if (cmd === "devices") {
    const [filter] = rest_args;
    const devices = await websocket(1, { type: "config/device_registry/list" });
    let list = Array.isArray(devices) ? devices : [];
    if (filter) {
      const terms = filter.toLowerCase().split(/\s+/).filter(Boolean);
      list = list.filter((d) => {
        const h = [d.name_by_user, d.name, d.manufacturer, d.model, d.id].filter(Boolean).join(" ").toLowerCase();
        return terms.every((t) => h.includes(t));
      });
    }
    list.sort((a, b) => String(a.name_by_user || a.name || "").localeCompare(String(b.name_by_user || b.name || "")));
    console.log(`Devices: ${list.length}`);
    for (const d of list) {
      const name = d.name_by_user || d.name || "(unnamed)";
      const parts = [d.manufacturer, d.model].filter(Boolean).join(" / ");
      console.log(`- ${name}${parts ? "  — " + parts : ""}  [id=${d.id}]`);
    }
  } else if (cmd === "entity-registry") {
    const [filter] = rest_args;
    const entries = await websocket(1, { type: "config/entity_registry/list" });
    let list = Array.isArray(entries) ? entries : [];
    if (filter) {
      const terms = filter.toLowerCase().split(/\s+/).filter(Boolean);
      list = list.filter((e) => {
        const h = [e.entity_id, e.name, e.original_name, e.platform, e.device_id, e.area_id]
          .filter(Boolean).join(" ").toLowerCase();
        return terms.every((t) => h.includes(t));
      });
    }
    list.sort((a, b) => String(a.entity_id).localeCompare(String(b.entity_id)));
    console.log(`Entity registry entries: ${list.length}`);
    for (const e of list) {
      const name = e.name || e.original_name || "";
      const dis = e.disabled_by ? `  [disabled=${e.disabled_by}]` : "";
      console.log(`- ${e.entity_id}  platform=${e.platform}  area=${e.area_id || "-"}  device=${e.device_id || "-"}${dis}  name="${name}"`);
    }
  } else if (cmd === "areas") {
    const areas = await websocket(1, { type: "config/area_registry/list" });
    const list = Array.isArray(areas) ? areas : [];
    list.sort((a, b) => String(a.name).localeCompare(String(b.name)));
    console.log(`Areas: ${list.length}`);
    for (const a of list) {
      console.log(`- ${a.name}  [id=${a.area_id}]${a.floor_id ? "  floor=" + a.floor_id : ""}`);
    }
  } else {
    console.error("Usage:");
    console.error("  node ha.mjs rest <METHOD> <PATH> [JSON_BODY]");
    console.error("  node ha.mjs entities [domainFilter] [nameFilter]");
    console.error("  node ha.mjs services [domain]");
    console.error("  node ha.mjs automations");
    console.error("  node ha.mjs devices [textFilter]");
    console.error("  node ha.mjs entity-registry [textFilter]");
    console.error("  node ha.mjs areas");
    process.exit(2);
  }
} catch (err) {
  console.error(String(err?.message || err));
  process.exit(1);
}
