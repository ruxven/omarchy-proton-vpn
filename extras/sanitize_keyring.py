#!/usr/bin/env python3
"""Fold multiline gnome-keyring INI values so GKeyFile can parse them.

Proton stores JSON+PEM in the unencrypted keyring. Literal newlines in
those secrets make gnome-keyring reject the whole file, after which Chrome
creates a new encrypted 'Default' keyring and prompts for a password.
"""

from __future__ import annotations

import argparse
import sys
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


def sanitize_keyring_file(path: Path) -> bool:
    """Rewrite an INI keyring in place. Returns True if the file changed."""
    if not path.is_file():
        return False
    original = path.read_text(encoding="utf-8")
    if not original.lstrip().startswith("["):
        return False
    sanitized = sanitize_keyring_text(original)
    if sanitized == original:
        return False
    path.write_text(sanitized, encoding="utf-8")
    path.chmod(0o600)
    return True


def main(argv: list[str] | None = None) -> int:
    """CLI entry: sanitize one keyring file path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    sanitize_keyring_file(args.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
