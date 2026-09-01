# Proton VPN for Omarchy

Official `protonvpn` CLI, driven from an Omarchy Quattro bar widget. Map,
country/city picker, Kill Switch, NetShield, Always On, split tunneling,
port forwarding, and traffic. Password and 2FA still go to Proton's own
TTY prompt — this plugin never sees them.

## Install

```bash
omarchy plugin add https://github.com/YOUR_GITHUB_USER/proton-vpn.git --enable
```

That clones this repo into `~/.config/omarchy/plugins/io.github.vibe.protonvpn`,
validates the manifest, and enables the bar widget. Click the Proton mark.
The panel installs `proton-vpn-cli` if it is missing, then walks you through
sign-in.

Local checkout of this repo:

```bash
omarchy plugin add /path/to/proton-vpn --enable
omarchy bar move io.github.vibe.protonvpn --after omarchy.network
```

Requires Omarchy Quattro. A free Proton account works; Plus unlocks country
targeting, P2P, Secure Core, Tor, NetShield ads/trackers, and port forwarding.

## Update

```bash
omarchy plugin update io.github.vibe.protonvpn
```

## Remove

```bash
omarchy plugin remove io.github.vibe.protonvpn
```

That does not uninstall the CLI or sign you out:

```bash
protonvpn disconnect
protonvpn signout
omarchy pkg drop proton-vpn-cli
```

## Use

| Action | Effect |
|---|---|
| Left-click | Open the panel |
| Right-click | Connect fastest / disconnect |
| Middle-click | Refresh |

**Free plan:** Fastest and Random. Plus-only rows fail with a clear error.

**Plus:** country → city drill, P2P / Secure Core / Tor, NetShield
ads+trackers, port forwarding on a P2P server.

The map is offline (Natural Earth + Proton's local server cache). No geo-IP.

Do **not** also install `proton-vpn-gtk-app`. CLI and GUI refuse to run
together. The panel warns if the app is present.

## Settings

Omarchy widget settings: status refresh, nmcli link watch, desktop
notifications.

## Optional extras

Keyring pin, SUPER+SHIFT+V, and a menu entry live in [`extras/`](extras/README.md).
They patch user config, so they are **not** part of `omarchy plugin add`.

## Layout

```
manifest.json     plugin contract (id: io.github.vibe.protonvpn)
Panel.qml         bar-widget entry (same pattern as omarchy.network)
Service.qml       CLI / nmcli / settings
WorldMap.qml      offline city map
Traffic.qml       tunnel sparkline
servers.py        cities from ~/.cache/Proton/VPN/serverlist.json
apps.py           split-tunnel app picker
port.py           NAT-PMP renew on 10.2.0.1
extras/           optional keyring + keybind (not auto-run)
```

```bash
python3 -m unittest discover -s tests -v
omarchy plugin validate .
```

## Credits

Panel, map, protections, and CLI glue were adapted from
[OmaProton VPN](https://github.com/grichard99/omaproton-vpn) (MIT).
World outline: [Natural Earth](https://www.naturalearthdata.com/) (public
domain). Proton mark: [Simple Icons](https://simpleicons.org) (CC0).
Not affiliated with Proton AG.

## License

[MIT](LICENSE)
