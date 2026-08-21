"""Unit tests for the local encryption-at-rest core (app/core/crypto.py).

Each test gets its own KeyManager instance backed by an isolated tmp_path
keys_root, instead of sharing the process-wide crypto.key_manager singleton
that other code paths may have already initialized against the real
settings.keys_root.
"""

from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from app.core import crypto
from app.core.crypto import KeyManager


@pytest.fixture
def fresh_key_manager(tmp_path, monkeypatch):
    monkeypatch.setattr(crypto.settings, "keys_root", str(tmp_path / "keys"))
    monkeypatch.setattr(crypto.settings, "encryption_enabled", True)
    KeyManager._instance = None
    km = KeyManager.get_instance()
    monkeypatch.setattr(crypto, "key_manager", km)
    yield km
    KeyManager._instance = None


def test_bytes_roundtrip(fresh_key_manager):
    plaintext = b"hello sentinel vault, this is a test frame payload"
    blob = crypto.encrypt_bytes(plaintext)
    assert blob.startswith(crypto.MAGIC)
    assert blob != plaintext
    assert crypto.decrypt_bytes(blob) == plaintext


def test_string_roundtrip_rtsp_url_with_credentials(fresh_key_manager):
    url = "rtsp://admin:s3cret@192.168.1.50:554/stream1"
    enc = crypto.encrypt_str(url)
    assert enc != url
    assert crypto.decrypt_str(enc) == url


@pytest.mark.parametrize(
    "legacy_url",
    ["usb://0", "rtsp://host/stream", "rtsp://user:pass@host:554/s"],
)
def test_legacy_plaintext_url_passthrough(fresh_key_manager, legacy_url):
    # Legacy/plaintext values (containing ':', which isn't valid base64)
    # must be returned unchanged rather than raising.
    assert crypto.decrypt_str(legacy_url) == legacy_url


def test_tamper_detection_raises_invalid_tag(fresh_key_manager):
    blob = bytearray(crypto.encrypt_bytes(b"sensitive footage bytes"))
    tamper_index = len(crypto.MAGIC) + crypto.NONCE_LEN + 2
    blob[tamper_index] ^= 0xFF
    with pytest.raises(InvalidTag):
        crypto.decrypt_bytes(bytes(blob))


def test_encrypt_file_in_place_and_decrypt_temp_copy(fresh_key_manager, tmp_path):
    f = tmp_path / "segment.mp4"
    original = b"fake mp4 bytes for test"
    f.write_bytes(original)

    crypto.encrypt_file_in_place(f)
    assert crypto.is_encrypted(f)
    assert f.read_bytes() != original

    captured_path = None
    with crypto.decrypted_temp_copy(f) as tmp:
        captured_path = tmp
        assert tmp.read_bytes() == original
    assert not captured_path.exists()  # cleaned up on context exit


def test_is_encrypted_false_for_plaintext_file(fresh_key_manager, tmp_path):
    f = tmp_path / "plain.mp4"
    f.write_bytes(b"not encrypted")
    assert crypto.is_encrypted(f) is False


def test_key_files_created_with_restrictive_permissions(fresh_key_manager):
    _ = fresh_key_manager.dek  # trigger key creation
    keys_root = Path(crypto.settings.keys_root)
    master_key = keys_root / "master.key"
    wrapped_dek = keys_root / "wrapped_dek.bin"
    assert master_key.exists()
    assert wrapped_dek.exists()
    assert oct(master_key.stat().st_mode)[-3:] == "600"
    assert oct(wrapped_dek.stat().st_mode)[-3:] == "600"


def test_dek_persists_across_key_manager_reloads(fresh_key_manager, tmp_path, monkeypatch):
    """Encrypting with one KeyManager instance and decrypting with a fresh
    one pointed at the same keys_root must still work (i.e. the wrapped
    DEK on disk, not just an in-memory key, is what matters)."""
    blob = crypto.encrypt_bytes(b"persisted across reloads")

    KeyManager._instance = None
    reloaded = KeyManager.get_instance()
    monkeypatch.setattr(crypto, "key_manager", reloaded)

    assert crypto.decrypt_bytes(blob) == b"persisted across reloads"


def test_encryption_disabled_is_passthrough(fresh_key_manager, monkeypatch):
    monkeypatch.setattr(crypto.settings, "encryption_enabled", False)
    plaintext = b"plaintext when encryption toggled off"
    blob = crypto.encrypt_bytes(plaintext)
    assert blob == plaintext
    assert not blob.startswith(crypto.MAGIC)
