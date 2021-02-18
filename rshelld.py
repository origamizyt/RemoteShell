from server import ShellServer
from config import default_config
import sys

config = default_config()

try:
    port = sys.argv[1]
except IndexError:
    port = config.get('server.port') or input('Enter port: ')

port = int(port)
s = ShellServer(port)
print('Server running on 0.0.0.0:%i' % port)
try:
    s.serve()
except KeyboardInterrupt:
    pass