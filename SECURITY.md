# Security

This plugin runs unsandboxed inside `omarchy-shell`, like every Omarchy
plugin. It:

- stores no credentials, tokens, or account data
- never sees your Proton password or 2FA code (those go to the CLI TTY)
- makes no network requests of its own except NAT-PMP to the VPN gateway
  `10.2.0.1` while port forwarding is on
- never asks for root; CLI install uses Omarchy's installer terminal
- runs commands as argv lists, except the sign-in username which is
  allow-listed and single-quoted before it reaches the terminal launcher
- writes `~/.local/state/vibe-protonvpn/` (recents, Always On, nudge) and,
  only if you change split tunneling, `features.split_tunneling` in
  Proton's `~/.config/Proton/VPN/settings.json`

Kill Switch / NetShield / port forwarding only ever pass allow-listed
keys and values to `protonvpn config set`.

`extras/install-session.sh` additionally installs a gnome-keyring drop-in
so Proton's session survives reboot on Omarchy. That is optional, local,
and not part of `omarchy plugin add`.
