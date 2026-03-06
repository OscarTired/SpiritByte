"""
SpiritByte - Security Module
Handles encryption, decryption, and password hashing using Argon2id + Fernet
"""
import os
import json
import base64
from typing import Optional, Tuple
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.recovery import (
    generate_recovery_phrase,
    recover_seed_from_phrase,
    encrypt_key_for_recovery,
    decrypt_key_from_recovery,
)

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

class SecurityManager:
    """Manages all security operations for SpiritByte"""
    
    def __init__(self, app_data_dir: str):
        self.app_data_dir = app_data_dir
        self.master_key_file = os.path.join(app_data_dir, "master.key")
        self.hasher = PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            salt_len=ARGON2_SALT_LEN,
            type=Type.ID  # Argon2id
        )
        self._fernet: Optional[Fernet] = None
    
    def master_exists(self) -> bool:
        """Check if master password has been set"""
        return os.path.exists(self.master_key_file)
    
    def create_master(self, password: str) -> Tuple[Optional[bytes], Optional[str]]:
        """Create a new master password and return (derived_key, recovery_phrase)"""
        if len(password) < 12:
            raise ValueError("Master password must be at least 12 characters")
        
        try:
            password_hash = self.hasher.hash(password)
            
            key_salt = os.urandom(32)
            recovery_salt = os.urandom(32)
            
            encryption_key = self._derive_key(password, key_salt)
            
            phrase, recovery_seed = generate_recovery_phrase(password_hash, key_salt)
            encrypted_enc_key = encrypt_key_for_recovery(
                encryption_key, recovery_seed, recovery_salt
            )
            
            del recovery_seed
            
            data = {
                "hash": password_hash,
                "key_salt": base64.b64encode(key_salt).decode('utf-8'),
                "version": 2,
                "encrypted_enc_key": encrypted_enc_key,
                "recovery_salt": base64.b64encode(recovery_salt).decode('utf-8'),
            }
            
            with open(self.master_key_file, 'w') as f:
                json.dump(data, f)
            
            return encryption_key, phrase
        except Exception as e:
            print(f"Error creating master password: {e}")
            return None, None
    
    def verify_master(self, password: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """Verify master password and return (success, derived_key, recovery_phrase_or_None).
        
        recovery_phrase is only returned when migrating from v1 to v2 so the
        UI can show the phrase to the user once.
        """
        if not self.master_exists():
            return False, None, None
        
        try:
            with open(self.master_key_file, 'r') as f:
                data = json.load(f)
            
            try:
                self.hasher.verify(data["hash"], password)
            except VerifyMismatchError:
                return False, None, None
            
            if self.hasher.check_needs_rehash(data["hash"]):
                new_hash = self.hasher.hash(password)
                data["hash"] = new_hash
                with open(self.master_key_file, 'w') as f:
                    json.dump(data, f)
            
            key_salt = base64.b64decode(data["key_salt"])
            encryption_key = self._derive_key(password, key_salt)
            
            migration_phrase = None
            if data.get("version", 1) < 2:
                migration_phrase = self._migrate_to_v2(data, encryption_key, key_salt)
            
            return True, encryption_key, migration_phrase
            
        except Exception as e:
            print(f"Error verifying master password: {e}")
            return False, None, None
    
    def _migrate_to_v2(
        self, data: dict, encryption_key: bytes, key_salt: bytes
    ) -> str:
        """Upgrade master.key from v1 to v2 by adding recovery fields."""
        recovery_salt = os.urandom(32)
        phrase, recovery_seed = generate_recovery_phrase(data["hash"], key_salt)
        encrypted_enc_key = encrypt_key_for_recovery(
            encryption_key, recovery_seed, recovery_salt
        )
        del recovery_seed
        
        data["version"] = 2
        data["encrypted_enc_key"] = encrypted_enc_key
        data["recovery_salt"] = base64.b64encode(recovery_salt).decode('utf-8')
        
        with open(self.master_key_file, 'w') as f:
            json.dump(data, f)
        
        return phrase
    
    def verify_recovery(self, phrase: str) -> Tuple[bool, Optional[bytes]]:
        """Verify a BIP39 recovery phrase and return the encryption key."""
        if not self.master_exists():
            return False, None
        
        try:
            with open(self.master_key_file, 'r') as f:
                data = json.load(f)
            
            if data.get("version", 1) < 2:
                return False, None
            
            recovery_seed = recover_seed_from_phrase(phrase)
            if recovery_seed is None:
                return False, None
            
            recovery_salt = base64.b64decode(data["recovery_salt"])
            encryption_key = decrypt_key_from_recovery(
                data["encrypted_enc_key"], recovery_seed, recovery_salt
            )
            del recovery_seed
            
            if encryption_key is None:
                return False, None
            
            self._fernet = Fernet(encryption_key)
            return True, encryption_key
            
        except Exception as e:
            print(f"Error verifying recovery phrase: {e}")
            return False, None
    
    def reset_master(self, new_password: str, old_encryption_key: bytes) -> Tuple[Optional[bytes], Optional[str]]:
        """Reset the master password after recovery. Returns (new_key, new_phrase)."""
        if len(new_password) < 12:
            raise ValueError("Master password must be at least 12 characters")
        
        try:
            password_hash = self.hasher.hash(new_password)
            key_salt = os.urandom(32)
            recovery_salt = os.urandom(32)
            
            new_encryption_key = self._derive_key(new_password, key_salt)
            
            phrase, recovery_seed = generate_recovery_phrase(password_hash, key_salt)
            encrypted_enc_key = encrypt_key_for_recovery(
                new_encryption_key, recovery_seed, recovery_salt
            )
            del recovery_seed
            
            data = {
                "hash": password_hash,
                "key_salt": base64.b64encode(key_salt).decode('utf-8'),
                "version": 2,
                "encrypted_enc_key": encrypted_enc_key,
                "recovery_salt": base64.b64encode(recovery_salt).decode('utf-8'),
            }
            
            with open(self.master_key_file, 'w') as f:
                json.dump(data, f)
            
            return new_encryption_key, phrase
        except Exception as e:
            print(f"Error resetting master password: {e}")
            return None, None
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a Fernet-compatible key from password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # High iteration count for security
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self._fernet = Fernet(key)
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string using Fernet"""
        if self._fernet is None:
            raise RuntimeError("Encryption key not initialized")
        return self._fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a Fernet-encrypted string"""
        if self._fernet is None:
            raise RuntimeError("Encryption key not initialized")
        return self._fernet.decrypt(encrypted_data.encode()).decode()
    
    def clear_key(self):
        """Clear the encryption key from memory"""
        self._fernet = None

_security_instance: Optional[SecurityManager] = None

def get_security_manager(app_data_dir: str) -> SecurityManager:
    """Factory function to get or create the singleton SecurityManager."""
    global _security_instance
    if _security_instance is None:
        _security_instance = SecurityManager(app_data_dir)
    return _security_instance
