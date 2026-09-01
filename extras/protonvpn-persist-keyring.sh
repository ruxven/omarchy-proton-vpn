#!/bin/bash
set -euo pipefail

# Pin Omarchy's passwordless gnome-keyring as Secret Service "default".
#
# Proton stores a JSON+PEM secret that inserts literal newlines into the
# unencrypted INI keyring. gnome-keyring then refuses to load it, Chrome
# creates an encrypted "Default" keyring, and you get password dialogs
# plus a signed-out Proton session after reboot.
#
# This script folds those newlines, quarantines extra encrypted keyrings,
# and points the default alias at Default_keyring.keyring.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
KEYRING_DIR="${PROTONVPN_KEYRING_DIR:-${HOME}/.local/share/keyrings}"
KEYRING_FILE="${KEYRING_DIR}/Default_keyring.keyring"
DEFAULT_FILE="${KEYRING_DIR}/default"
QUARANTINE_DIR="${PROTONVPN_KEYRING_QUARANTINE:-${KEYRING_DIR}.quarantine}"
SKIP_DAEMON="${PROTONVPN_KEYRING_SKIP_DAEMON:-0}"

usage() {
  echo "Usage: ${0##*/} [--prep|--unlock|--repair]" >&2
  exit 2
}

ensure_passwordless_keyring() {
  mkdir -p "${KEYRING_DIR}"
  if [[ ! -f "${KEYRING_FILE}" ]]; then
    cat >"${KEYRING_FILE}" <<EOF
[keyring]
display-name=Default keyring
ctime=$(date +%s)
mtime=0
lock-on-idle=false
lock-after=false
EOF
  fi
  printf "Default_keyring\n" >"${DEFAULT_FILE}"
  chmod 700 "${KEYRING_DIR}"
  chmod 600 "${KEYRING_FILE}"
  chmod 644 "${DEFAULT_FILE}"
}

sanitize_ini_keyring() {
  local helper
  for helper in \
    "${SCRIPT_DIR}/sanitize_keyring.py" \
    "${HOME}/.config/omarchy/bin/sanitize_keyring.py"
  do
    if [[ -f "${helper}" ]]; then
      python3 "${helper}" "${KEYRING_FILE}"
      return 0
    fi
  done
}

quarantine_competing_keyrings() {
  mkdir -p "${QUARANTINE_DIR}"
  local moved=0
  local path
  shopt -s nullglob
  for path in \
    "${KEYRING_DIR}/Default.keyring" \
    "${KEYRING_DIR}/login.keyring" \
    "${KEYRING_DIR}"/Default_keyring_[0-9]*.keyring
  do
    [[ -f "${path}" ]] || continue
    mv -f "${path}" "${QUARANTINE_DIR}/"
    moved=1
  done
  shopt -u nullglob
  return $(( 1 - moved ))
}

kill_all_daemons() {
  [[ "${SKIP_DAEMON}" == "1" ]] && return 0
  systemctl --user stop gnome-keyring-daemon.service 2>/dev/null || true
  local proc exe
  for proc in /proc/[0-9]*; do
    exe=$(readlink "${proc}/exe" 2>/dev/null || true)
    if [[ "${exe}" == */gnome-keyring-daemon ]]; then
      kill "${proc#/proc/}" 2>/dev/null || true
    fi
  done
  sleep 0.2
}

set_default_alias() {
  [[ "${SKIP_DAEMON}" == "1" ]] && return 0
  python3 - <<'PY' || true
import gi
gi.require_version("Secret", "1")
from gi.repository import Secret

try:
    service = Secret.Service.get_sync(Secret.ServiceFlags.LOAD_COLLECTIONS, None)
except Exception:
    raise SystemExit(0)
target = None
for collection in service.get_collections() or []:
    path = collection.get_object_path() or ""
    if path.endswith("/Default_5fkeyring") and "Default_5fkeyring_" not in path:
        target = collection
        break
if target is None:
    for collection in service.get_collections() or []:
        if collection.get_label() == "Default keyring" and not collection.get_locked():
            target = collection
            break
if target is not None:
    service.set_alias_sync("default", target)
PY
}

restart_keyring_daemon() {
  [[ "${SKIP_DAEMON}" == "1" ]] && return 0
  kill_all_daemons
  systemctl --user start gnome-keyring-daemon.service
  sleep 0.5
}

prep() {
  ensure_passwordless_keyring
  sanitize_ini_keyring
  quarantine_competing_keyrings || true
}

persist() {
  local force_restart=${1:-0}
  ensure_passwordless_keyring
  sanitize_ini_keyring
  local moved=0
  if quarantine_competing_keyrings; then
    moved=1
  fi
  if (( force_restart || moved )); then
    restart_keyring_daemon
  fi
  set_default_alias
}

case "${1:-}" in
  "") persist 0 ;;
  --prep) prep ;;
  --unlock) set_default_alias ;;
  --repair) persist 1 ;;
  -h|--help) usage ;;
  *) usage ;;
esac
