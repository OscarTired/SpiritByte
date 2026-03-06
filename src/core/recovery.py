"""
SpiritByte - BIP39 Recovery Module
Handles mnemonic phrase generation, seed recovery, and encryption key
backup/restore for master password recovery. Pure logic, no UI or state.
"""
import base64
import io
from typing import Optional, Tuple

from mnemonic import Mnemonic
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import qrcode
from PIL import Image

_mnemonic = Mnemonic("english")

RECOVERY_KDF_ITERATIONS = 100_000

def generate_recovery_phrase(
    password_hash: str, key_salt: bytes
) -> Tuple[str, bytes]:
    """
    Derive a 16-byte recovery seed from the Argon2 hash + salt,
    then convert it to a 12-word BIP39 mnemonic phrase.
    (16 bytes = 128 bits = 12 BIP39 words.)

    Returns (mnemonic_phrase, recovery_seed).
    The caller must clear recovery_seed from memory after use.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=16,
        salt=key_salt,
        iterations=RECOVERY_KDF_ITERATIONS,
    )
    recovery_seed = kdf.derive(password_hash.encode("utf-8"))
    phrase = _mnemonic.to_mnemonic(recovery_seed)
    return phrase, recovery_seed

def recover_seed_from_phrase(phrase: str) -> Optional[bytes]:
    """
    Validate a BIP39 phrase and extract the original 32-byte entropy.
    Uses to_entropy() for exact round-trip with to_mnemonic().

    Returns recovery_seed (32 bytes) or None if invalid.
    """
    phrase = phrase.strip().lower()
    if not _mnemonic.check(phrase):
        return None
    try:
        recovery_seed = bytes(_mnemonic.to_entropy(phrase))
        return recovery_seed
    except Exception:
        return None

def _derive_recovery_fernet_key(
    recovery_seed: bytes, recovery_salt: bytes
) -> bytes:
    """Derive a Fernet-compatible key from the recovery seed."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),  
        length=32,
        salt=recovery_salt,
        iterations=RECOVERY_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(recovery_seed))

def encrypt_key_for_recovery(
    encryption_key: bytes,
    recovery_seed: bytes,
    recovery_salt: bytes,
) -> str:
    """
    Encrypt the main encryption_key using a Fernet key derived from
    the recovery seed. Returns base64-encoded ciphertext string.
    """
    fernet_key = _derive_recovery_fernet_key(recovery_seed, recovery_salt)
    f = Fernet(fernet_key)
    encrypted = f.encrypt(encryption_key)
    return encrypted.decode("utf-8")

def decrypt_key_from_recovery(
    encrypted_enc_key: str,
    recovery_seed: bytes,
    recovery_salt: bytes,
) -> Optional[bytes]:
    """
    Attempt to decrypt the encryption_key using the recovery seed.
    Returns the encryption_key bytes, or None if the phrase was wrong.
    """
    try:
        fernet_key = _derive_recovery_fernet_key(recovery_seed, recovery_salt)
        f = Fernet(fernet_key)
        return f.decrypt(encrypted_enc_key.encode("utf-8"))
    except (InvalidToken, Exception):
        return None

def generate_qr_bytes(data: str) -> bytes:
    """
    Generate a QR code image from data and return it as raw PNG bytes
    (for use with ft.Image src=bytes in Flet >= 0.80).
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img: Image.Image = qr.make_image(fill_color="white", back_color="#0a0a0a")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read()
