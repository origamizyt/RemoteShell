# Remote Shell

Repos: https://www.github.com/origamizyt/RemoteShell

## Installation

Just download the files and install the dependencies:
```
pip install PyCryptodome
```

## Run

Server:
```
$ python rshelld.py <port>
```

Client:
```
$ python rshell.py <host> <port>
```

## Config

Configuration file: `config.json`

- `shell.version`: shell version, do not modify.
- `shell.welcome`: welcome message, can be modified.
use #\[expr\]# to evaluate expressions.
- `shell.encrypt`: whether use encrypt mode or not, can be modified.
- `shell.helpmsg`: help message, do not modify.
- `server.port`: default server port if not provided through sys.argv, can be modified.