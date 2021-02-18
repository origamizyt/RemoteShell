import socket, struct

class ServerExit(Exception):
    'Raises when server exits. Caught by server or application.'

class SocketWrapper:
    'Represents a socket wrapper that sends header using struct module.'
    def __init__(self, sock: socket.socket):
        self._sock = sock
    def send(self, data: bytes) -> None:
        'Sends the data with header of length.'
        head = struct.pack('>I', len(data))
        self._sock.send(head+data)
    def recv(self) -> bytes:
        'Receives the data.'
        head = self._sock.recv(4)
        if not head:
            raise ServerExit
        return self._sock.recv(struct.unpack('>I', head)[0])
    def connect(self, addr) -> None:
        'Direct call to socket.connect.'
        self._sock.connect(addr)
    def accept(self):
        'Direct call to socket.accept.'
        return self._sock.accept()
    def close(self) -> None:
        'Direct call to socket.close.'
        self._sock.close()