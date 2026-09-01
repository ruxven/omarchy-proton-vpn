#!/bin/bash
set -euo pipefail

# Undo extras/install-session.sh. Does not remove the plugin.

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MENU_FILE="${HOME}/.config/omarchy/extensions/omarchy-menu.jsonc"
BIND_FILE="${HOME}/.config/hypr/bindings.lua"
PATCH="${ROOT}/patch_config.py"
PERSIST_DST="${HOME}/.config/omarchy/bin/protonvpn-persist-keyring.sh"
SANITIZE_DST="${HOME}/.config/omarchy/bin/sanitize_keyring.py"
HOOK_FILE="${HOME}/.config/omarchy/hooks/post-boot.d/protonvpn-persist-keyring.sh"
DROPIN_FILE="${HOME}/.config/systemd/user/gnome-keyring-daemon.service.d/protonvpn-passwordless.conf"

echo "Removing Proton VPN session extras"

if [[ -f "${MENU_FILE}" ]]; then
  python3 "${PATCH}" menu "${MENU_FILE}" --remove
fi

if [[ -f "${BIND_FILE}" ]]; then
  python3 "${PATCH}" bindings "${BIND_FILE}" --remove
  hyprctl reload >/dev/null || true
fi

rm -f "${HOOK_FILE}" "${PERSIST_DST}" "${SANITIZE_DST}" "${DROPIN_FILE}"
rmdir "$(dirname "${DROPIN_FILE}")" 2>/dev/null || true
systemctl --user daemon-reload || true
systemctl --user restart gnome-keyring-daemon.service || true

echo "Extras removed. Plugin is unchanged: omarchy plugin remove io.github.vibe.protonvpn"
