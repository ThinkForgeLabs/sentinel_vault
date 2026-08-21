"""
Local at-rest encryption for Sentinel Vault.

This is the module backing the "everything is encrypted locally, even if
the drive is stolen" guarantee — every recording segment, motion clip,
thumbnail, and sensitive DB field (e.g. camera RTSP credentials) is
encrypted with the key material managed here before it ever touches disk.

── Envelope encryption ───────────────────────────────────────────────
Two keys, with different jobs, so "how access to footage is protected"
can change later without re-encrypting anything already recorded:

  1. Key-Encrypting Key (KEK) — protects the data key below. Today the
     KEK itself is a random key generated on first run and stored in a
     locked-down local file (data/keys/master.key, mode 0600). This is
     the zero-setup default. A future "protect with your own passphrase"
     mode would simply swap in a KEK derived from that passphrase
     (Argon2id/PBKDF2) and re-wrap the *same* data key with it — nothing
     already encrypted on disk would need to change.

  2. Data-Encryption Key (DEK) — a random 256-bit key generated once per
     install. This is what actually encrypts every file and field. It is
     never stored in the clear: it's encrypted ("wrapped") by the KEK and
     saved as data/keys/wrapped_dek.bin.

── Cipher ─────────────────────────────────────────────────────────────
AES-256-GCM: authenticated encryption, so tampering with an encrypted
file causes decryption to fail loudly instead of silently returning
corrupted video. Every ciphertext blob is:

    MAGIC (5 bytes) || nonce (12 bytes) || ciphertext+tag

A blob without the MAGIC prefix is treated as legacy/plaintext and
passed through unchanged on decrypt — this keeps the encryption toggle
in Settings safe to flip, and keeps old un-encrypted demo data readable
instead of crashing.
"""

import base64
import contextlib
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("crypto")

MAGIC = b"SVEN1"
NONCE_LEN = 12
KEY_LEN = 32  # 256-bit


class KeyManager:
    """Thread-safe singleton owning the KEK + wrapped DEK for this install.

    Follows the same get_instance() singleton pattern used elsewhere in
    this codebase (see DetectionManager, RecordingManager).
    """

    _instance: Optional["KeyManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._keys_root = Path(settings.keys_root)
        self._dek: Optional[bytes] = None
        self._setup_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "KeyManager":
        return cls()

    def _ensure_dek(self) -> bytes:
        if self._dek is not None:
            return self._dek
        with self._setup_lock:
            if self._dek is not None:
                return self._dek
            self._keys_root.mkdir(parents=True, exist_ok=True)
            self._chmod_quiet(self._keys_root, 0o700)
            kek = self._load_or_create_kek()
            self._dek = self._load_or_create_dek(kek)
            return self._dek

    @staticmethod
    def _chmod_quiet(path: Path, mode: int) -> None:
        try:
            os.chmod(path, mode)
        except OSError:
            # Not fatal (e.g. filesystem doesn't support POSIX perms) —
            # the file/dir is still created, just without the extra
            # permission hardening.
            pass

    def _load_or_create_kek(self) -> bytes:
        path = self._keys_root / "master.key"
        if path.exists():
            raw = base64.b64decode(path.read_text().strip())
            if len(raw) != KEY_LEN:
                raise RuntimeError(f"Corrupt master key at {path} (bad length)")
            return raw

        raw = AESGCM.generate_key(bit_length=256)
        path.write_text(base64.b64encode(raw).decode())
        self._chmod_quiet(path, 0o600)
        logger.info(
            "Generated new local master key (KEK) at %s — keep this file safe; "
            "losing it makes all encrypted recordings permanently unreadable.",
            path,
        )
        return raw

    def _load_or_create_dek(self, kek: bytes) -> bytes:
        path = self._keys_root / "wrapped_dek.bin"
        aead = AESGCM(kek)

        if path.exists():
            blob = path.read_bytes()
            nonce, ciphertext = blob[:NONCE_LEN], blob[NONCE_LEN:]
            return aead.decrypt(nonce, ciphertext, None)

        dek = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(NONCE_LEN)
        wrapped = aead.encrypt(nonce, dek, None)
        path.write_bytes(nonce + wrapped)
        self._chmod_quiet(path, 0o600)
        logger.info("Generated new data-encryption key (wrapped) at %s", path)
        return dek

    @property
    def dek(self) -> bytes:
        return self._ensure_dek()


key_manager = KeyManager.get_instance()


def _encryption_enabled() -> bool:
    return settings.encryption_enabled


def encrypt_bytes(plaintext: bytes) -> bytes:
    """Encrypt arbitrary bytes with the install's data key. Returns the
    plaintext unchanged if encryption is disabled in settings."""
    if not _encryption_enabled():
        return plaintext
    aead = AESGCM(key_manager.dek)
    nonce = os.urandom(NONCE_LEN)
    ciphertext = aead.encrypt(nonce, plaintext, None)
    return MAGIC + nonce + ciphertext


def decrypt_bytes(blob: bytes) -> bytes:
    """Decrypt a blob produced by encrypt_bytes. Blobs without the MAGIC
    prefix are treated as legacy/plaintext and returned unchanged, so
    toggling encryption off or reading old un-encrypted data never
    crashes."""
    if not blob.startswith(MAGIC):
        return blob
    body = blob[len(MAGIC):]
    nonce, ciphertext = body[:NONCE_LEN], body[NONCE_LEN:]
    aead = AESGCM(key_manager.dek)
    return aead.decrypt(nonce, ciphertext, None)


def is_encrypted(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(len(MAGIC)) == MAGIC
    except OSError:
        return False


def encrypt_file_in_place(src: Path, dest: Optional[Path] = None) -> None:
    """Read plaintext from src, write ciphertext to dest (defaults to
    src itself). Used right after a recorder/writer finishes producing a
    plaintext file, before anything else can read it off disk."""
    dest = dest or src
    data = src.read_bytes()
    dest.write_bytes(encrypt_bytes(data))
    if src != dest:
        src.unlink(missing_ok=True)


@contextlib.contextmanager
def decrypted_temp_copy(path: Path, suffix: str = ""):
    """Yield a Path to a short-lived temp file holding the plaintext
    content of `path`. Always cleaned up on exit, even on error. Use this
    whenever an encrypted file needs to be handed to something that
    requires a real file path (ffmpeg, cv2, FileResponse)."""
    data = path.read_bytes()
    plaintext = decrypt_bytes(data)
    fd, tmp_name = tempfile.mkstemp(suffix=suffix)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(plaintext)
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def encrypt_str(value: str) -> str:
    """Encrypt a short string (e.g. an RTSP URL with embedded
    credentials) for storage in a DB text column. Base64-encoded so it
    round-trips safely through any text/JSON column."""
    return base64.b64encode(encrypt_bytes(value.encode("utf-8"))).decode("ascii")


def decrypt_str(value: str) -> str:
    """Decrypt a string produced by encrypt_str. Values that aren't
    valid base64 (e.g. legacy plaintext RTSP URLs like rtsp://host/... —
    the literal ':' isn't a base64 character) are returned unchanged."""
    try:
        blob = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error):
        return value
    if not blob.startswith(MAGIC):
        return value
    return decrypt_bytes(blob).decode("utf-8")
