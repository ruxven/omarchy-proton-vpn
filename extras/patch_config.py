#!/usr/bin/env python3
"""Patch Omarchy menu.jsonc and Hyprland bindings.lua for Proton VPN."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PLUGIN_ID = "io.github.vibe.protonvpn"
MENU_BEGIN = "  // proton-vpn:begin"
MENU_END = "  // proton-vpn:end"
BIND_BEGIN = "-- proton-vpn:begin"
BIND_END = "-- proton-vpn:end"

MENU_BLOCK = f"""{MENU_BEGIN}
  "trigger.vpn": {{
    "icon": "󰒃",
    "label": "Proton VPN",
    "aliases": ["vpn", "proton"],
    "description": "Sign in and connect Proton VPN",
  }},
  "trigger.vpn.panel": {{
    "icon": "󰦝",
    "label": "Open panel",
    "action": "omarchy-shell {PLUGIN_ID} toggle",
  }},
{MENU_END}"""

BIND_BLOCK = f"""{BIND_BEGIN}
o.bind(
  "SUPER + SHIFT + V",
  "Proton VPN",
  "omarchy-shell {PLUGIN_ID} toggle"
)
{BIND_END}"""

VPN_OBJECT = re.compile(
    r'(?:,\s*)?"trigger\.vpn(?:\.[^"]+)?"\s*:\s*\{(?:[^{}]|\{[^{}]*\})*\}\s*,?',
    re.MULTILINE,
)


def replace_marked_block(text: str, begin: str, end: str, block: str) -> str:
    """Replace an existing marked block, or return the original text."""
    pattern = re.compile(
        re.escape(begin) + r".*?" + re.escape(end),
        flags=re.DOTALL,
    )
    if not pattern.search(text):
        return text
    return pattern.sub(block, text, count=1)


def strip_vpn_entries(text: str) -> str:
    """Remove marked Proton VPN blocks and leftover trigger.vpn* keys."""
    text = replace_marked_block(text, MENU_BEGIN, MENU_END, "")
    previous = None
    while previous != text:
        previous = text
        text = VPN_OBJECT.sub("", text, count=1)
    return re.sub(r",\s*,", ",", text)


def insert_before_last_brace(text: str, block: str) -> str:
    """Insert a JSONC object block before the file's closing brace."""
    idx = text.rstrip().rfind("}")
    if idx < 0:
        raise ValueError("menu file has no closing brace")
    prefix = text[:idx].rstrip()
    if prefix and not prefix.endswith(",") and not prefix.endswith("{"):
        prefix += ","
    return prefix + "\n\n" + block + "\n" + text[idx:]


def patch_menu(path: Path, remove: bool = False) -> None:
    """Insert, update, or strip Proton VPN menu entries."""
    text = strip_vpn_entries(path.read_text(encoding="utf-8"))
    if not remove:
        text = insert_before_last_brace(text, MENU_BLOCK)
    path.write_text(text, encoding="utf-8")


def patch_bindings(path: Path, remove: bool = False) -> None:
    """Insert, update, or strip the Proton VPN Hyprland bind."""
    text = path.read_text(encoding="utf-8")
    if remove:
        text = replace_marked_block(text, BIND_BEGIN, BIND_END, "")
        text = re.sub(
            r"\no\.bind\(\s*\"SUPER \+ SHIFT \+ V\",.*?^\s*\)\s*",
            "\n",
            text,
            count=1,
            flags=re.DOTALL | re.MULTILINE,
        )
        path.write_text(text, encoding="utf-8")
        return

    if BIND_BEGIN in text:
        text = replace_marked_block(text, BIND_BEGIN, BIND_END, BIND_BLOCK)
    elif "omarchy-shell" in text and "protonvpn" in text:
        text = re.sub(
            r"o\.bind\(\s*\"SUPER \+ SHIFT \+ V\",.*?^\s*\)",
            BIND_BLOCK,
            text,
            count=1,
            flags=re.DOTALL | re.MULTILINE,
        )
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + BIND_BLOCK + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=["menu", "bindings"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    if args.target == "menu":
        patch_menu(args.path, remove=args.remove)
    else:
        patch_bindings(args.path, remove=args.remove)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
