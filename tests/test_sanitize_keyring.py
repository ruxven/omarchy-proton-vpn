#!/usr/bin/env python3
"""Tests for keyring persistence."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Mock secretstorage before importing
sys.modules["secretstorage"] = MagicMock()
sys.modules["secretstorage.exceptions"] = MagicMock()

import sanitize_keyring

class TestKeyring(unittest.TestCase):
    @patch("sanitize_keyring.get_keyring_collection")
    def test_persist_session_success(self, mock_get_collection):
        mock_get_collection.return_value = MagicMock()
        self.assertTrue(sanitize_keyring.persist_session())

    @patch("sanitize_keyring.get_keyring_collection")
    def test_persist_session_failure(self, mock_get_collection):
        mock_get_collection.return_value = None
        self.assertFalse(sanitize_keyring.persist_session())

if __name__ == "__main__":
    unittest.main()
