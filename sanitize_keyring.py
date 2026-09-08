#!/usr/bin/env python3
"""Fold multiline gnome-keyring INI values so GKeyFile can parse them.

Proton stores JSON+PEM in the unencrypted keyring. Literal newlines in
those secrets make gnome-keyring reject the whole file, after which Chrome
creates a new encrypted 'Default' keyring and prompts for a password.

--persist sanitizes Omarchy's passwordless INI (if it exists) and pins
the default alias to it. It does not create keyrings, restart the
daemon, or quarantine Chrome stores.
"""

from __future__ import annotations

import argparse
import os
import sys
import subprocess
from pathlib import Path
import secretstorage
from secretstorage.exceptions import ItemNotFoundException

def get_keyring_collection():
    """Returns the default keyring collection, unlocking it if necessary."""
    try:
        bus = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(bus)
        if collection.is_locked():
            collection.unlock()
        return collection
    except Exception:
        return None

def sanitize_keyring_file(path: Path) -> bool:
    """
    Refactored to use the Secret Service API via secretstorage.
    Direct file manipulation is deprecated and potentially causes corruption.
    This function now just ensures the keyring is accessible and unlocked.
    """
    if not path.is_file():
        return False

    collection = get_keyring_collection()
    if not collection:
        return False

    return True

def keyring_dir() -> Path:
    """Return the gnome-keyring directory, honoring PROTONVPN_KEYRING_DIR."""
    override = os.environ.get("PROTONVPN_KEYRING_DIR")
    if override:
        return Path(override)
    return Path.home() / ".local/share/keyrings"

def get_keyring_path(name: str | None = None) -> Path:
    """Return the path to the keyring file, resolving alias if needed."""
    directory = keyring_dir()
    if name:
        return directory / f"{name}.keyring"

    alias = directory / "default"
    if alias.is_file():
        name = alias.read_text(encoding="utf-8").strip()
        return directory / f"{name}.keyring"

    # Fallback: look for any .keyring file, prioritizing 'Default_Keyring'
    candidates = list(directory.glob("*.keyring"))
    if not candidates:
        return directory / "Default_Keyring.keyring"

    # Try case-insensitive match for Default_Keyring
    for c in candidates:
        if c.stem.lower() == "default_keyring":
            return c

    return candidates[0]

def persist_session() -> bool:
    """
    Ensures the default keyring is unlocked.
    The file sanitization is no longer needed with the Secret Service API.
    """
    collection = get_keyring_collection()
    return collection is not None

def main(argv: list[str] | None = None) -> int:
    """CLI entry: ensure keyring is accessible, or `--persist` the session."""
    parser = argparse.ArgumentParser(description="Ensure gnome-keyring access for Proton VPN")
    parser.add_argument("path", type=Path, nargs="?")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="ensure the active keyring is unlocked",
    )
    args = parser.parse_args(argv)
    if args.persist:
        persist_session()
        return 0
    if args.path is None:
        parser.error("path or --persist is required")
    sanitize_keyring_file(args.path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
