import os
import json
import base64
import logging
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

logger = logging.getLogger("BlueGhost.Messaging")

class CryptographicMessaging:
    """Handles AES-256 session key generation, message payload encryption, and decryption."""

    def __init__(self, session_key=None):
        # Generate 256-bit (32 bytes) ephemeral session key if not provided
        self.session_key = session_key or get_random_bytes(32)

    def get_encoded_key(self):
        """Return base64 encoded temporary session key."""
        return base64.b64encode(self.session_key).decode('utf-8')

    def encrypt_payload(self, raw_data_dict):
        """
        Encrypt a dictionary payload using AES-256-CBC with PKCS7 padding.
        Returns base64 encoded JSON envelope with IV and ciphertext.
        """
        try:
            json_str = json.dumps(raw_data_dict)
            data_bytes = json_str.encode('utf-8')
            
            iv = get_random_bytes(16)
            cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
            padded_data = pad(data_bytes, AES.block_size)
            ciphertext = cipher.encrypt(padded_data)

            envelope = {
                "iv": base64.b64encode(iv).decode('utf-8'),
                "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
                "encrypted": True
            }
            return json.dumps(envelope)
        except Exception as e:
            logger.error(f"Payload encryption error: {e}")
            raise e

    def decrypt_payload(self, encrypted_json_str):
        """
        Decrypt base64 JSON envelope using AES-256-CBC and unpad payload.
        """
        try:
            envelope = json.loads(encrypted_json_str)
            if not envelope.get("encrypted"):
                return envelope

            iv = base64.b64decode(envelope["iv"])
            ciphertext = base64.b64decode(envelope["ciphertext"])

            cipher = AES.new(self.session_key, AES.MODE_CBC, iv)
            padded_bytes = cipher.decrypt(ciphertext)
            data_bytes = unpad(padded_bytes, AES.block_size)

            return json.loads(data_bytes.decode('utf-8'))
        except Exception as e:
            logger.error(f"Payload decryption error: {e}")
            raise e

    def rotate_session_key(self):
        """Generate a fresh temporary session key (no permanent key storage)."""
        self.session_key = get_random_bytes(32)
        return self.get_encoded_key()
