from security import SecurityManager, RSA_SIGNATURE_SIZE, InvalidSignature
from network import SocketWrapper, ServerExit
from executor import ExecutionResult
import socket

class ShellClient:
    def __init__(self, host: str, port: str):
        self._sock = SocketWrapper(socket.socket())
        self._manager = SecurityManager()
        self._addr = (host, port)
        self._mode = ''
    def address(self):
        return self._addr
    def connect(self):
        self._sock.connect(self._addr)
        self._sock.send(self._manager.export())
        self._manager.load(self._sock.recv())
        self._mode = 'signature'
    def execute(self, code: str) -> ExecutionResult:
        self._send(code.encode())
        if code.startswith('#:'): # meta command
            self.metacommand(code[2:])
        data = self._recv()
        result = ExecutionResult.unpack(data)
        return result
    def metacommand(self, cmd: str):
        cmd = cmd.strip().lower()
        if cmd == 'mode.encrypt':
            self._mode = 'encrypt'
        elif cmd == 'mode.signature':
            self._mode = 'signature'
    def close(self) -> None:
        self._sock.close()
    def _send(self, data: bytes) -> None:
        if self._mode == 'encrypt':
            data = self._manager.encrypt(data)
        elif self._mode == 'signature':
            data = self._manager.sign(data)+data
        self._sock.send(data)
    def _recv(self) -> bytes:
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