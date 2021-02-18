'''
This module provides implementation of shell server.

The only public interface is ShellServer.

Usage:
>>> s = ShellServer(5000) # use 0.0.0.0:5000
>>> s.serve()
'''

from network import SocketWrapper, ServerExit
from security import SecurityManager, RSA_SIGNATURE_SIZE, InvalidSignature
from executor import Executor, ExecutionResult, RequireInput
from typing import Tuple
import socket

__all__ = ['ShellServer']

class ShellServer:
    def __init__(self, port: int):
        sock = socket.socket()
        sock.bind(('localhost', port))
        sock.listen(5)
        self._sock = SocketWrapper(sock)
        self._executor = Executor(self)
        self._aborted = False
    def serve(self) -> None:
        'Launches the server.'
        self._executor.prepare()
        while not self._aborted:
            self._manager = SecurityManager()
            self._mode = ''
            self._handshaken = False
            client, addr = self._sock.accept()
            self._client = SocketWrapper(client)
            self._main()
    def _main(self) -> None:
        'Main loop of the server. Internal use only.'
        try:
            while True:
                ret, data = self._recv()
                if not ret: continue
                if self._handshaken:
                    result = self._executor.execute(data)
                    self._send(result.pack())
                else:
                    self._handshake(data)
                    self._handshaken = True
        except (SystemExit, ServerExit):
            self._client.close()
    def _handshake(self, data) -> None:
        'Perform RSA handshake with client. Internal use only.'
        self._manager.load(data)
        self._send(self._manager.export())
        self._mode = 'signature'
    def _send(self, data) -> None:
        'Sends the data. Internal use only.'
        if self._mode == 'encrypt':
            data = self._manager.encrypt(data)
        elif self._mode == 'signature':
            data = self._manager.sign(data)+data
        self._client.send(data)
    def _recv(self) -> Tuple[bool, bytes]:
        'Receives the data. Internal use only.'
        data = self._client.recv()
        if self._mode == 'encrypt':
            data = self._manager.decrypt(data)
            return True, data
        elif self._mode == 'signature':
            signature, data = data[:RSA_SIGNATURE_SIZE], data[RSA_SIGNATURE_SIZE:]
            if not self._manager.verify(data, signature):
                self._send(ExecutionResult(False, None, InvalidSignature(), '').pack())
                return False, b''
            return True, data
        return True, data
    def switchMode(self, mode: str) -> None:
        'Switches the security mode.'
        self._mode = mode
    def mode(self) -> str:
        'Gets the security mode.'
        return self._mode
    def requireInput(self, prompt: str) -> str:
        "Requests input from client's stdin."
        self._send(ExecutionResult(True, RequireInput(), None, prompt).pack())
        ret, data = self._recv()
        if not ret: return ''
        return data.decode()
    def abort(self) -> None:
        'Aborts the server.'
        self._aborted = True
        raise ServerExit