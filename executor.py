from typing import Optional, Any, AnyStr
from types import BuiltinFunctionType, FunctionType
from io import StringIO
from config import default_config
import pickle, sys, traceback

config = default_config()
HELPMSG = '\n'.join(config.get('shell.helpmsg'))

def pack_data(data: Any) -> Any:
    if data is None or isinstance(data, (str, int, bytes, bytearray, RequireInput)):
        return data
    elif isinstance(data, (tuple, list)):
        r = []
        for item in data:
            r.append(pack_data(item))
        return r
    elif isinstance(data, dict):
        d = {}
        for k, v in data.items():
            d[pack_data(k)] = pack_data(v)
        return d
    elif isinstance(data, BuiltinFunctionType) and data.__module__ == 'builtins':
        # only keep builtin function from 'builtins' module
        return data
    else:
        return RemoteObjectRef(data)

def pack_error(error: Exception) -> Any:
    return RemoteException(error)

def special_ref(obj: Any) -> Optional[str]:
    if obj.__class__.__name__ in [
        'type', 'function', 'method', 'generator',
        'async_generator', 'coroutine', 'getset_descriptor',
        'method-wrapper', 'module', 'method_descriptor',
        'wrapper_descriptor'
        ]:
        return obj.__name__
    return None

class RemoteException:
    def __init__(self, error: Exception):
        self._traceback = ''.join(traceback.format_exception(error.__class__, error, error.__traceback__))
    def __getstate__(self):
        return { 'traceback': self._traceback }
    def __setstate__(self, state):
        self._traceback = state['traceback']
    def printTraceback(self):
        print(self._traceback.strip())

class RequireInput: pass # notifier

class RemoteObjectRef:
    def __init__(self, obj: Any):
        self._class = obj.__class__.__name__
        self._address = id(obj)
        self._name = special_ref(obj)
    def __repr__(self):
        if self._name is not None:
            return '<remote %s %r>' % (self._class, self._name)
        return '<remote %r object at %s (remote address)>' % (self._class, '0x' + hex(self._address)[2:].upper())
    def __getstate__(self):
        return { 'class': self._class, 'address': self._address, 'name': self._name }
    def __setstate__(self, state):
        self._class = state['class']
        self._address = state['address']
        self._name = state['name']

class ExecutionResult:
    def __init__(self, success: bool=True, data: Any=None, error: Optional[Exception]=None, stdout: str=''):
        if not success and not error:
            raise ValueError("error must be provided when failure.")
        self._success = success
        if error is not None:
            self._error = pack_error(error)
        else:
            self._error = None
        self._stdout = stdout
        self._data = data
    def pack(self) -> bytes:
        return pickle.dumps({
            'success': self._success,
            'error': self._error,
            'stdout': self._stdout,
            'data': pack_data(self._data)
        })
    @staticmethod
    def unpack(data: bytes) -> 'ExecutionResult':
        data = pickle.loads(data)
        result = ExecutionResult.__new__(ExecutionResult)
        result._success = data['success']
        result._error = data['error']
        result._stdout = data['stdout']
        result._data = data['data']
        return result
    def stdout(self) -> str:
        return self._stdout
    def success(self) -> bool:
        return self._success
    def error(self) -> Optional[RemoteException]:
        return self._error
    def data(self) -> Any:
        return self._data

class RuntimeStdin:
    def __init__(self, server: 'server.ShellServer', stdout: 'RuntimeStdout'):
        self._buffer = ''
        self._server = server
        self._stdout = stdout
    def read(self, n: int) -> str:
        if len(self._buffer) < n:
            self._requireInput()
        data, self._buffer = self._buffer[:n], self._buffer[n:]
        return data
    def readline(self) -> str:
        if not self._buffer:
            self._requireInput()
        data, *buffer = self._buffer.split('\n', 1)
        self._buffer = buffer[0] if buffer else ''
        return data
    def _requireInput(self) -> None:
        self.put(self._server.requireInput(self._stdout.get()))
    def put(self, data: str) -> None:
        self._buffer += data
    def noop(self) -> None: pass
    flush = close = noop

class RuntimeStdout:
    def __init__(self):
        self._buffer = ''
    def write(self, data: str) -> None:
        self._buffer += data
    def get(self) -> str:
        data, self._buffer = self._buffer, ''
        return data
    def noop(self) -> None: pass
    flush = close = noop

class Executor:
    def __init__(self, server: 'server.ShellServer'):
        self._scope = {}
        self._stdout = RuntimeStdout()
        self._stdin = RuntimeStdin(server, self._stdout)
        self._server = server
    def prepare(self) -> None:
        sys.stdin = self._stdin
        sys.stdout = self._stdout
    def execute(self, statement: AnyStr) -> ExecutionResult:
        if isinstance(statement, bytes):
            statement = statement.decode()
        if statement.startswith('#:'): # meta command:
            return self.metacommand(statement[2:])
        try:
            return ExecutionResult(True, eval(statement, self._scope), None, self._stdout.get())
        except SyntaxError: pass
        except Exception as e:
            return ExecutionResult(False, None, e, self._stdout.get())
        try:
            exec(statement, self._scope)
            return ExecutionResult(True, None, None, self._stdout.get())
        except Exception as e:
            return ExecutionResult(False, None, e, self._stdout.get())
    def metacommand(self, cmd: AnyStr):
        cmd = cmd.strip().lower()
        if isinstance(cmd, bytes): 
            cmd = cmd.decode()
        if cmd == 'mode.encrypt':
            self._server.switchMode('encrypt')
            return ExecutionResult(True)
        elif cmd == 'mode.signature':
            self._server.switchMode('signature')
            return ExecutionResult(True, None, None, "Warning: Swiching to insecure context.\n")
        elif cmd == 'mode':
            return ExecutionResult(True, None, None, self._server._mode+"\n")
        elif cmd == 'help':
            return ExecutionResult(True, None, None, HELPMSG)
        elif cmd == 'exit':
            self._server.abort() # no return
        return ExecutionResult(True, None, None, "No metacommand named %s\n" % cmd)