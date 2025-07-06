"""
CyberVault Security - AES-256 encryption/decryption, JWT-like tokens, PIN-based MFA
"""
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os, secrets, hashlib

# AES-256 encryption/decryption
class AESCipher:
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, data):
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(data.encode()) + encryptor.finalize()
        return iv + ct

    def decrypt(self, enc):
        iv = enc[:16]
        ct = enc[16:]
        cipher = Cipher(algorithms.AES(self.key), modes.CFB(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        return (decryptor.update(ct) + decryptor.finalize()).decode()

# PIN-based MFA (local)
def verify_pin(input_pin, stored_hash):
    return hashlib.sha256(input_pin.encode()).hexdigest() == stored_hash
