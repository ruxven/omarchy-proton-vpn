#!/usr/bin/env python3
"""Tests for split-tunnel desktop-entry filtering."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps import parse_entry, program_of  # noqa: E402


class ProgramOfTests(unittest.TestCase):
    def test_plain_binary(self) -> None:
        self.assertEqual(program_of("/usr/bin/firefox %u"), "/usr/bin/firefox")

    def test_strips_env(self) -> None:
        self.assertEqual(
            program_of("env FOO=1 /usr/bin/qbittorrent"),
            "/usr/bin/qbittorrent",
        )

    def test_drops_flatpak(self) -> None:
        self.assertIsNone(program_of("flatpak run org.mozilla.firefox"))

    def test_drops_shell(self) -> None:
        self.assertIsNone(program_of("bash -c 'something'"))

    def test_drops_omarchy_launcher(self) -> None:
        self.assertIsNone(program_of("omarchy-launch-webapp https://example.com"))


class ParseEntryTests(unittest.TestCase):
    def test_reads_name_and_exec(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.desktop"
            path.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Firefox\n"
                "Exec=/usr/bin/firefox %u\n",
                encoding="utf-8",
            )
            self.assertEqual(
                parse_entry(str(path)),
                ("Firefox", "/usr/bin/firefox %u"),
            )

    def test_skips_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "app.desktop"
            path.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Hidden\n"
                "Hidden=true\n"
                "Exec=/usr/bin/true\n",
                encoding="utf-8",
            )
            self.assertIsNone(parse_entry(str(path)))

    def test_skips_non_application(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "link.desktop"
            path.write_text(
                "[Desktop Entry]\nType=Link\nName=Site\nURL=https://x\n",
                encoding="utf-8",
            )
            self.assertIsNone(parse_entry(str(path)))


if __name__ == "__main__":
    unittest.main()
