#!/usr/bin/env python3
"""Tests for menu.jsonc and bindings.lua patching."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "extras"))

from patch_config import PLUGIN_ID, patch_bindings, patch_menu  # noqa: E402


class MenuPatchTests(unittest.TestCase):
    def test_inserts_into_empty_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "menu.jsonc"
            path.write_text("{\n}\n", encoding="utf-8")
            patch_menu(path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("proton-vpn:begin", text)
            self.assertIn('"trigger.vpn"', text)
            self.assertIn(PLUGIN_ID, text)
            self.assertNotIn("signin.sh", text)

    def test_replaces_legacy_vibe_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "menu.jsonc"
            path.write_text(
                '{\n  "trigger.vpn": {"label": "old"},\n'
                '  "trigger.vpn.signin": {"action": "vibe.protonvpn"},\n}\n',
                encoding="utf-8",
            )
            patch_menu(path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("omarchy-shell vibe.protonvpn", text)
            self.assertNotIn("local.protonvpn", text)
            self.assertIn(f"omarchy-shell {PLUGIN_ID} toggle", text)
            self.assertEqual(text.count("proton-vpn:begin"), 1)

    def test_strips_unmarked_leftovers_then_inserts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "menu.jsonc"
            path.write_text(
                '{\n  "trigger.vpn.panel": {"action": "vibe.protonvpn"},\n'
                "  // proton-vpn:begin\n"
                '  "trigger.vpn": {"label": "old"},\n'
                "  // proton-vpn:end\n}\n",
                encoding="utf-8",
            )
            patch_menu(path)
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("trigger.vpn.panel"), 1)
            self.assertNotIn("omarchy-shell vibe.protonvpn", text)
            self.assertNotIn("local.protonvpn", text)
            self.assertIn(PLUGIN_ID, text)

    def test_remove_strips_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "menu.jsonc"
            path.write_text("{\n}\n", encoding="utf-8")
            patch_menu(path)
            patch_menu(path, remove=True)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("trigger.vpn", text)
            self.assertNotIn("proton-vpn:begin", text)


class BindPatchTests(unittest.TestCase):
    def test_appends_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bindings.lua"
            path.write_text("-- comments only\n", encoding="utf-8")
            patch_bindings(path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("SUPER + SHIFT + V", text)
            self.assertIn(PLUGIN_ID, text)

    def test_replaces_vibe_bind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bindings.lua"
            path.write_text(
                'o.bind(\n  "SUPER + SHIFT + V",\n  "Proton VPN",\n'
                '  "omarchy-shell vibe.protonvpn toggle"\n)\n',
                encoding="utf-8",
            )
            patch_bindings(path)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("omarchy-shell vibe.protonvpn", text)
            self.assertNotIn("local.protonvpn", text)
            self.assertIn(PLUGIN_ID, text)
            self.assertIn("proton-vpn:begin", text)


if __name__ == "__main__":
    unittest.main()
