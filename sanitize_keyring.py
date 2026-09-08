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
import re
import sys
import tempfile
import subprocess
from pathlib import Path

KNOWN_KEYS = (
    "display-name",
    "item-type",
    "ctime",
    "mtime",
    "lock-on-idle",
    "lock-after",
    "secret",
    "key",
    "value",
    "name",
    "type",
)


def is_key_line(line: str) -> bool:
    """Return True if line starts a gnome-keyring INI field."""
    return any(line.startswith(f"{key}=") for key in KNOWN_KEYS)


def sanitize_keyring_text(text: str) -> str:
    """Return INI text with multiline values folded using GKeyFile \\n."""
    lines = text.splitlines()
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not is_key_line(line):
            out.append(line)
            index += 1
            continue
        key, _, value = line.partition("=")
        index += 1
        parts = [value]
        while (
            index < len(lines)
            and lines[index] != ""
            and not is_key_line(lines[index])
            and not lines[index].startswith("[")
        ):
            parts.append(lines[index])
            index += 1
        if len(parts) == 1:
            out.append(f"{key}={value}")
        else:
            out.append(f"{key}={'\\n'.join(parts)}")
    result = "\n".join(out)
    if text.endswith("\n"):
        result += "\n"
    return result


def get_keyring_collection_path(keyring_name: str) -> str | None:
    """Dynamically resolve the D-Bus object path for a keyring collection."""
    try:
        # List all collections to find the matching one
        output = subprocess.check_output(
            ["busctl", "--user", "tree", "org.freedesktop.secrets"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        # Escape the keyring name as it might appear in the D-Bus path (e.g., _ -> _5f)
        escaped_name = keyring_name.replace("_", "_5f")
        pattern = re.compile(rf"/org/freedesktop/secrets/collection/{escaped_name}")
        for line in output.splitlines():
            match = pattern.search(line)
            if match:
                return match.group(0)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None

def sanitize_keyring_file(path: Path) -> bool:
    """Rewrite an INI keyring atomically. Returns True if the file changed."""
    if not path.is_file():
        return False

    # Dynamically find the D-Bus path for the keyring collection being sanitized
    collection_path = get_keyring_collection_path(path.stem)

    if collection_path and not os.environ.get("TESTING"):
        # Check if the keyring is locked
        try:
            res = subprocess.run(
                ["busctl", "--user", "get-property", "org.freedesktop.secrets", 
                 collection_path, 
                 "org.freedesktop.Secret.Collection", "Locked"],
                capture_output=True, text=True, check=True
            )
            if "true" in res.stdout:
                return False # Keyring is locked, do not attempt to sanitize
        except subprocess.CalledProcessError:
            pass # Proceed if we cannot check

    original = path.read_text(encoding="utf-8")
    if not original.lstrip().startswith("["):
        return False
    sanitized = sanitize_keyring_text(original)
    if sanitized == original:
        return False

    # Atomic write using a temporary file
    tmp_path = path.with_suffix(".keyring.tmp")
    tmp_path.write_text(sanitized, encoding="utf-8")
    tmp_path.chmod(0o600)
    os.replace(tmp_path, path)

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
    """Sanitize the active keyring and pin the default alias to it.

    No-ops if the passwordless INI is missing. Does not create keyrings,
    restart gnome-keyring, or move Chrome stores. Returns True if the INI
    or alias file changed.
    """
    ini = get_keyring_path()
    alias = keyring_dir() / "default"
    if not ini.is_file():
        return False
    try:
        head = ini.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    if not head.lstrip().startswith("["):
        return False
    changed = sanitize_keyring_file(ini)
    wanted = f"{ini.stem}\n"
    current = alias.read_text(encoding="utf-8") if alias.is_file() else ""
    if current != wanted:
        alias.write_text(wanted, encoding="utf-8")
        alias.chmod(0o644)
        return True
    return changed


def main(argv: list[str] | None = None) -> int:
    """CLI entry: sanitize one keyring file, or `--persist` the session store."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="sanitize the active keyring and pin the default alias",
    )
    args = parser.parse_args(argv)
    if args.persist:
        if args.path is not None:
            parser.error("--persist does not take a path")
        persist_session()
        return 0
    if args.path is None:
        parser.error("path or --persist is required")
    sanitize_keyring_file(args.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
