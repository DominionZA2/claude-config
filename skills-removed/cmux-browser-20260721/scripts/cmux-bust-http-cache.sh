#!/usr/bin/env bash
# Clear cmux WKWebView HTTP network cache WITHOUT wiping cookies/login.
#
# Use when a localhost page is stuck on old JS/CSS despite Fast Refresh / reloads.
# Root cause is usually Cache-Control: immutable on stable /_next/static URLs in dev.
#
# Safe: only deletes NetworkCache + related disk cache under com.cmuxterm.app.
# Does NOT delete WebsiteData (cookies, localStorage) or browser profiles.
#
# Usage:
#   cmux-bust-http-cache.sh              # purge cache only
#   cmux-bust-http-cache.sh --reload surface:80   # purge + reload surface
#   cmux-bust-http-cache.sh --verify http://localhost:3000/_next/static/chunks/webpack.js

set -euo pipefail

RELOAD_SURFACE=""
VERIFY_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reload)
      RELOAD_SURFACE="${2:-}"
      shift 2
      ;;
    --verify)
      VERIFY_URL="${2:-}"
      shift 2
      ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

CACHE_ROOT="${HOME}/Library/Caches/com.cmuxterm.app"
NETWORK_CACHE="${CACHE_ROOT}/WebKit/NetworkCache"
CACHE_DB_GLOB="${CACHE_ROOT}/Cache.db*"

purged=0

if [[ -d "$NETWORK_CACHE" ]]; then
  rm -rf "$NETWORK_CACHE"
  echo "purged=${NETWORK_CACHE}"
  purged=1
else
  echo "missing=${NETWORK_CACHE} (ok if never used)"
fi

# Electron-style cache db sometimes also holds assets
shopt -s nullglob
for f in ${CACHE_ROOT}/Cache.db ${CACHE_ROOT}/Cache.db-shm ${CACHE_ROOT}/Cache.db-wal; do
  if [[ -e "$f" ]]; then
    rm -f "$f"
    echo "purged=${f}"
    purged=1
  fi
done
shopt -u nullglob

if [[ "$purged" -eq 0 ]]; then
  echo "status=nothing_to_purge"
else
  echo "status=purged"
fi

if [[ -n "$VERIFY_URL" ]]; then
  echo "verify_url=${VERIFY_URL}"
  # Show what the server is currently advertising (new loads must not be immutable in dev)
  curl -sI "$VERIFY_URL" | tr -d '\r' | grep -iE '^(HTTP/|cache-control:|etag:)' || true
fi

if [[ -n "$RELOAD_SURFACE" ]]; then
  if ! command -v cmux >/dev/null 2>&1; then
    echo "error: cmux CLI not found; cache purged but could not reload ${RELOAD_SURFACE}" >&2
    exit 1
  fi
  # Navigate away then back forces script re-fetch after network cache wipe
  current_url="$(cmux browser "$RELOAD_SURFACE" get url 2>/dev/null || true)"
  if [[ -z "$current_url" || "$current_url" == "about:blank" ]]; then
    cmux browser "$RELOAD_SURFACE" reload || true
    echo "reloaded=${RELOAD_SURFACE} mode=reload"
  else
    cmux browser "$RELOAD_SURFACE" navigate "about:blank" || true
    sleep 0.3
    cmux browser "$RELOAD_SURFACE" navigate "$current_url" || true
    echo "reloaded=${RELOAD_SURFACE} mode=navigate-away-back url=${current_url}"
  fi
fi

echo "note=Auth/session preserved (WebsiteData not touched). New /_next/* loads should re-fetch."
