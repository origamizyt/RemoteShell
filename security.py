'''
This module provides API for security and cryptography implemtations.

The only public interface is SecurityManager.

Usage:
>>> s1 = SecurityManager()
>>> s2 = SecurityManager()
>>> s1.load(s2.export())
>>> s2.loadHex(s1.exportHex())
>>> s2.verify(b'data', s1.sign(b'data'))
True
>>> s1.decrypt(s2.encrypt(b'data'))
b'data'
'''

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA384
from Crypto.Signature import pkcs1_15
from typing import Tuple
from config import default_config
import os

__all__ = ['SecurityManager', 'SecurityError', 'InvalidSignature', 'InvalidPadding', 'MissingRemoteKey']

config = default_config()
RSA_KEY_SIZE = config.get('security.rsaKeySize', 1024)
RSA_CIPHER_SIZE = RSA_SIGNATURE_SIZE = RSA_KEY_SIZE // 8
AES_KEY_SIZE = config.get('security.aesKeySize', 16)

def random_key_iv(size: int = AES_KEY_SIZE) -> Tuple[bytes, bytes]:
    'Generates a pair of random key and initial vector.'
    return os.urandom(size), os.urandom(AES.block_size)

def hashof(data: bytes) -> SHA384.SHA384Hash:
    'Computes the SHA384 digest of the message.'
    return SHA384.new(data)

def pad(data: bytes, size: int = AES.block_size) -> bytes:
    'Pads the data using PKCS-5 standard.'
    need = size - len(data) % size
    return data + bytes((need,) * need)

def unpad(data: bytes) -> bytes:
    'Unpads the data using PKCS-5 standard.'
    plen = data[-1]
    data, padding = data[:-plen], data[-plen:]
    if padding != bytes((plen,) * plen):
        raise InvalidPadding(padding)
    return data

def encrypt(data: bytes) -> Tuple[bytes, bytes]:
    'Encrypts the data using ephemeral keys.'
    key, iv = random_key_iv()
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return key, iv+cipher.encrypt(pad(data))

def decrypt(key: bytes, data: bytes) -> bytes:
    'Extracts and decrypts data.'
    iv, data = data[:AES.block_size], data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data))

class SecurityError(Exception):
    'General base class for security errors.'

class MissingRemoteKey(SecurityError):
    'A RSA remote key is missing.'
    def __init__(self):
        super().__init__('no specified remote key.')

class InvalidPadding(SecurityError):
    'Invalid PKCS-5 padding.'
    def __init__(self, padding: bytes):
        super().__init__(padding)

class InvalidSignature(SecurityError):
    def __init__(self):
        super().__init__('signature is invalid.')

class SecurityManager:
    'Represents a security manager. A security manager exposes public functions for signing and encryption.'
    def __init__(self):
        self._privateKey = RSA.generate(1024)
        self._publicKey = self._privateKey.publickey()
        self._remoteKey = None
    def _check_remoteKey(self) -> None:
        'Checks whether the remote key is valid.'
        if not self._remoteKey:
            raise MissingRemoteKey
    def sign(self, data: bytes) -> bytes:
        'Signs the data with local private key.'
        signer = pkcs1_15.new(self._privateKey)
        return signer.sign(hashof(data))
    def verify(self, data: bytes, signature: bytes) -> bool:
        'Verifies the data with remote public key.'
        self._check_remoteKey()
        signer = pkcs1_15.new(self._remoteKey)
        try:
            signer.verify(hashof(data), signature)
            return True
        except ValueError:
            return False
    def load(self, remote_key: bytes) -> None:
        'Loads a DER encoded key string as remote public key.'
        self._remoteKey = RSA.import_key(remote_key)
    def loadHex(self, remote_key: str) -> None:
        'Loads a DER encoded hex string as remote public key.'
        self.load(bytes.fromhex(remote_key))
    def export(self) -> bytes:
        'Exports a DER encoded local public key string.'
        return self._publicKey.export_key('DER')
    def exportHex(self) -> str:
        'Exports a DER encoded local public key hex string.'
        return self.export().hex()
    def encrypt(self, data: bytes) -> bytes:
        'Encrypts the data using ephemeral keys.'
        self._check_remoteKey()
        ephemeral, data = encrypt(data)
        cipher = PKCS1_OAEP.new(self._remoteKey)
        ephemeral = cipher.encrypt(ephemeral)
        return ephemeral+data
    def decrypt(self, data: bytes) -> bytes:
        'Extracts a and decrypts the data.'
        ephemeral, data = data[:RSA_CIPHER_SIZE], data[RSA_CIPHER_SIZE:]
        cipher = PKCS1_OAEP.new(self._privateKey)
        ephemeral = cipher.decrypt(ephemeral)
        return decrypt(ephemeral, data)