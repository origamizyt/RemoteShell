from network import SocketWrapper, ServerExit
from security import SecurityManager, RSA_SIGNATURE_SIZE, InvalidSignature
from executor import Executor, ExecutionResult, RequireInput
from typing import Tuple
import socket

class ShellServer:
    def __init__(self, port: int):
        sock = socket.socket()
        sock.bind(('localhost', port))
        sock.listen(5)
        self._sock = SocketWrapper(sock)
        self._executor = Executor(self)
        self._aborted = False
    def serve(self):
        self._executor.prepare()
        while not self._aborted:
            self._manager = SecurityManager()
            self._mode = ''
            self._handshaken = False
            client, addr = self._sock.accept()
            self._client = SocketWrapper(client)
            self._main()
    def _main(self):
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
    def _handshake(self, data):
        self._manager.load(data)
        self._send(self._manager.export())
        self._mode = 'signature'
    def _send(self, data):
        if self._mode == 'encrypt':
            data = self._manager.encrypt(data)
        elif self._mode == 'signature':
            data = self._manager.sign(data)+data
        self._client.send(data)
    def _recv(self) -> Tuple[bool, bytes]:
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
        self._mode = mode
    def mode(self) -> str:
        return self._mode
    def requireInput(self, prompt: str) -> str:
        self._send(ExecutionResult(True, RequireInput(), None, prompt).pack())
        ret, data = self._recv()
        if not ret: return ''
        return data.decode()
    def abort(self) -> None:
        self._aborted = True
        raise ServerExit