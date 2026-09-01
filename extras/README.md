# Optional extras

Not part of the Omarchy plugin. `omarchy plugin add` never runs these.

Use them only if you want:

- Proton to stay signed in across Omarchy reboots (Chrome/Cursor otherwise
  steal the gnome-keyring default alias)
- **SUPER+SHIFT+V** and an Omarchy menu entry

```bash
./extras/install-session.sh
./extras/uninstall-session.sh
```

The plugin itself is added and removed with:

```bash
omarchy plugin add <git-url> --enable
omarchy plugin remove io.github.vibe.protonvpn
```
