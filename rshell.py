from client import ShellClient
from executor import RequireInput
from config import default_config, sub_template
from network import ServerExit
import sys

config = default_config()

try:
    host = sys.argv[1]
except IndexError:
    host = input('Enter host: ')
try:
    port = sys.argv[2]
except IndexError:
    port = input('Enter port: ')

port = int(port)
c = ShellClient(host, port)
c.connect()
welcome = config.get('shell.welcome')
welcome = sub_template(welcome, scope={ 'sys': sys, 'client': c })
print(welcome)
if config.get('shell.encrypt'):
    c.execute('#: mode.encrypt') # execute meta command
else:
    print('Warning: Insecure context. Modify config.json or use the #: mode.encrypt metacommand to encrypt this channel.')
try:
    while True:
        cmd = input('>>> ').strip()
        if not cmd: continue
        if cmd.endswith('\\') or cmd.endswith(':'):
            while True:
                line = input('... ')
                if not line: break
                cmd += '\n' + line
        result = c.execute(cmd)
        print(result.stdout(), end='')
        if result.success():
            data = result.data()
            while isinstance(data, RequireInput):
                line = input()
                result = c.execute(line)
                if result.success():
                    print(result.stdout(), end='')
                    data = result.data()
                else:
                    print('='*10, 'Remote Error Occurred', '='*10, end='\n\n')
                    result.error().printTraceback()
                    break
            else:
                if data:
                    print(repr(data))
        else:
            print('='*10, 'Remote Error Occurred', '='*10, end='\n\n')
            result.error().printTraceback()
except (KeyboardInterrupt, ServerExit):
    pass
finally:
    c.close()