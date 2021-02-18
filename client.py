'''
This module provides implementation of shell client.

The only public interface is ShellClient.

Usage:
>>> c = ShellClient('0.0.0.0', 5000)
>>> c.connect()
>>> c.execute('print("Hello, world!")').stdout()
'Hello, world!\n'
>>> c.execute('#: mode.encrypt') # metacommand
>>> c.close()
'''

from security import SecurityManager, RSA_SIGNATURE_SIZE, InvalidSignature
from network import SocketWrapper, ServerExit
from executor import ExecutionResult
from typing import Tuple
import socket

__all__ = ['ShellClient']

class ShellClient:
    'Represents the client of the shell.'
    def __init__(self, host: str, port: int):
        self._sock = SocketWrapper(socket.socket())
        self._manager = SecurityManager()
        self._addr = (host, port)
        self._mode = ''
    def address(self) -> Tuple[str, int]:
        'Gets the address of this client.'
        return self._addr
    def connect(self) -> None:
        'Connects to the server and perform RSA exchange.'
        self._sock.connect(self._addr)
        self._sock.send(self._manager.export())
        self._manager.load(self._sock.recv())
        self._mode = 'signature'
    def execute(self, code: str) -> ExecutionResult:
        'Execute a line of code.'
        self._send(code.encode())
        if code.startswith('#:'): # meta command
            self.metacommand(code[2:])
        data = self._recv()
        result = ExecutionResult.unpack(data)
        return result
    def metacommand(self, cmd: str) -> None:
        'Execute a metacommand.'
        cmd = cmd.strip().lower()
        if cmd == 'mode.encrypt':
            self._mode = 'encrypt'
        elif cmd == 'mode.signature':
            self._mode = 'signature'
    def close(self) -> None:
        'Closes the client.'
        self._sock.close()
    def _send(self, data: bytes) -> None:
        'Send the specific data. Internal use only.'
        if self._mode == 'encrypt':
            data = self._manager.encrypt(data)
        elif self._mode == 'signature':
            data = self._manager.sign(data)+data
        self._sock.send(data)
    def _recv(self) -> bytes:
        'Receives the data. Internal use only.'
        data = self._sock.recv()
        if self._mode == 'encrypt':
            data = self._manager.decrypt(data)
            return data
        elif self._mode == 'signature':
            signature, data = data[:RSA_SIGNATURE_SIZE], data[RSA_SIGNATURE_SIZE:]
            if not self._manager.verify(data, signature):
                return ExecutionResult(False, None, InvalidSignature(), '').pack()
            return data
        return data