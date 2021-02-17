import socket, struct

class ServerExit(Exception):
    pass

class SocketWrapper:
    def __init__(self, sock: socket.socket):
        self._sock = sock
    def send(self, data: bytes) -> None:
        head = struct.pack('>I', len(data))
        self._sock.send(head+data)
    def recv(self) -> bytes:
        head = self._sock.recv(4)
        if not head:
            raise ServerExit
        return self._sock.recv(struct.unpack('>I', head)[0])
    def connect(self, addr) -> None:
        self._sock.connect(addr)
    def accept(self):
        return self._sock.accept()
    def close(self) -> None:
        self._sock.close()