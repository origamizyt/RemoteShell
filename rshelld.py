from server import ShellServer
import sys

try:
    port = sys.argv[1]
except IndexError:
    port = input('Enter port: ')

port = int(port)
s = ShellServer(port)
print('Server running on localhost:%i' % port)
try:
    s.serve()
except KeyboardInterrupt:
    pass