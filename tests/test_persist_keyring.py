#!/usr/bin/env python3
"""Tests for protonvpn-persist-keyring.sh file pinning."""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "extras" / "protonvpn-persist-keyring.sh"


def run_persist(keyring_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PROTONVPN_KEYRING_DIR"] = str(keyring_dir)
    env["PROTONVPN_KEYRING_QUARANTINE"] = str(keyring_dir.parent / "keyrings.quarantine")
    env["PROTONVPN_KEYRING_SKIP_DAEMON"] = "1"
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


class PersistKeyringTests(unittest.TestCase):
    def test_prep_creates_passwordless_keyring_and_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keyring_dir = Path(tmp) / "keyrings"
            run_persist(keyring_dir, "--prep")
            alias = (keyring_dir / "default").read_text(encoding="utf-8")
            body = (keyring_dir / "Default_keyring.keyring").read_text(encoding="utf-8")
            self.assertEqual(alias, "Default_keyring\n")
            self.assertIn("lock-on-idle=false", body)
            self.assertIn("display-name=Default keyring", body)
            mode = stat.S_IMODE((keyring_dir / "Default_keyring.keyring").stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_prep_quarantines_competing_keyrings_not_the_ini(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keyring_dir = Path(tmp) / "keyrings"
            keyring_dir.mkdir()
            (keyring_dir / "default").write_text("Default\n", encoding="utf-8")
            ini = keyring_dir / "Default_keyring.keyring"
            ini.write_text("[keyring]\ndisplay-name=keep-me\n", encoding="utf-8")
            (keyring_dir / "Default.keyring").write_text("encrypted", encoding="utf-8")
            (keyring_dir / "login.keyring").write_text("login", encoding="utf-8")
            (keyring_dir / "Default_keyring_1.keyring").write_text("one", encoding="utf-8")
            (keyring_dir / "Default_keyring_2.keyring").write_text("two", encoding="utf-8")
            run_persist(keyring_dir, "--prep")
            quarantine = Path(tmp) / "keyrings.quarantine"
            self.assertTrue((quarantine / "Default.keyring").is_file())
            self.assertTrue((quarantine / "login.keyring").is_file())
            self.assertTrue((quarantine / "Default_keyring_1.keyring").is_file())
            self.assertTrue((quarantine / "Default_keyring_2.keyring").is_file())
            self.assertFalse((keyring_dir / "Default.keyring").exists())
            self.assertTrue(ini.is_file())
            self.assertIn("keep-me", ini.read_text(encoding="utf-8"))
            self.assertEqual(
                (keyring_dir / "default").read_text(encoding="utf-8"),
                "Default_keyring\n",
            )

    def test_unknown_flag_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keyring_dir = Path(tmp) / "keyrings"
            env = os.environ.copy()
            env["PROTONVPN_KEYRING_DIR"] = str(keyring_dir)
            env["PROTONVPN_KEYRING_SKIP_DAEMON"] = "1"
            result = subprocess.run(
                ["bash", str(SCRIPT), "--nope"],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)

    def test_prep_folds_multiline_proton_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            keyring_dir = Path(tmp) / "keyrings"
            keyring_dir.mkdir()
            ini = keyring_dir / "Default_keyring.keyring"
            ini.write_text(
                "[keyring]\ndisplay-name=Default keyring\n"
                "lock-on-idle=false\nlock-after=false\n\n"
                "[4]\nsecret={\"k\": \"-----BEGIN PUBLIC KEY-----\n"
                "MCow=\n-----END PUBLIC KEY-----\"}\n",
                encoding="utf-8",
            )
            run_persist(keyring_dir, "--prep")
            body = ini.read_text(encoding="utf-8")
            self.assertIn("\\nMCow=\\n", body)
            self.assertNotIn("\nMCow=", body)


if __name__ == "__main__":
    unittest.main()
