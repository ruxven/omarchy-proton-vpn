#!/bin/bash
set -euo pipefail

# Optional extras. The plugin itself is installed with:
#   omarchy plugin add <git-url> --enable
# This script does not copy plugin files. It only pins gnome-keyring so
# Proton stays signed in across Omarchy reboots, and adds SUPER+SHIFT+V
# plus a menu entry.

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PLUGIN_ID="io.github.vibe.protonvpn"
MENU_FILE="${HOME}/.config/omarchy/extensions/omarchy-menu.jsonc"
BIND_FILE="${HOME}/.config/hypr/bindings.lua"
PATCH="${ROOT}/patch_config.py"
PERSIST_SRC="${ROOT}/protonvpn-persist-keyring.sh"
SANITIZE_SRC="${ROOT}/sanitize_keyring.py"
PERSIST_DST="${HOME}/.config/omarchy/bin/protonvpn-persist-keyring.sh"
SANITIZE_DST="${HOME}/.config/omarchy/bin/sanitize_keyring.py"
DROPIN_DIR="${HOME}/.config/systemd/user/gnome-keyring-daemon.service.d"
DROPIN_FILE="${DROPIN_DIR}/protonvpn-passwordless.conf"

fail() {
  echo "extras/install-session: $*" >&2
  exit 1
}

backup_file() {
  local path=$1
  [[ -f "${path}" ]] || return 0
  cp -a "${path}" "${path}.bak.$(date +%s)"
}

command -v python3 &>/dev/null || fail "missing command: python3"
command -v omarchy &>/dev/null || fail "missing command: omarchy"

echo "Installing Proton VPN session extras (keyring pin, SUPER+SHIFT+V, menu)"

backup_file "${MENU_FILE}"
mkdir -p "$(dirname "${MENU_FILE}")"
[[ -f "${MENU_FILE}" ]] || printf '{\n}\n' >"${MENU_FILE}"
python3 "${PATCH}" menu "${MENU_FILE}"

backup_file "${BIND_FILE}"
if [[ -f "${BIND_FILE}" ]]; then
  python3 "${PATCH}" bindings "${BIND_FILE}"
  hyprctl reload >/dev/null || true
fi

mkdir -p "$(dirname "${PERSIST_DST}")" "${DROPIN_DIR}"
install -m 755 "${PERSIST_SRC}" "${PERSIST_DST}"
install -m 644 "${SANITIZE_SRC}" "${SANITIZE_DST}"
cat >"${DROPIN_FILE}" <<EOF
[Service]
ExecStartPre=${PERSIST_DST} --prep
ExecStartPost=${PERSIST_DST} --unlock
EOF
omarchy hook install post-boot "${PERSIST_DST}"
systemctl --user daemon-reload
"${PERSIST_DST}" --repair

echo
echo "Done. These extras are not part of omarchy plugin add."
echo "  SUPER+SHIFT+V toggles ${PLUGIN_ID}."
echo "  Remove with: extras/uninstall-session.sh"
