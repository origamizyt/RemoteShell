'''
Configuration module of this program.

This module contains basic function to access the config.json file using the `JsonConfig` class.

Usage:
>>> config = default_config()
>>> config
<JsonConfig from 'config.json'>
>>> config.get('shell.version')
'1.0.0'
>>> template = config.get('shell.welcome')
>>> print(sub_template(template))
Remote Shell Version 1.0.0 (0.0.0.0:5000)
Python 3.8.5 (tags/v3.8.5:580fbb0, Jul 20 2020, 15:57:54) [MSC v.1924 64 bit (AMD64)]
Enter #: help for metacommand help.
'''

import json, re
from typing import Optional

class JsonConfig(dict):
    'Represents a json format configuration.'
    def __init__(self, file: str):
        self._file = file
        super().__init__(json.load(open(file)))
    def __repr__(self) -> str:
        return '<JsonConfig from {!r}>'.format(self._file)

config = None

def default_config() -> JsonConfig:
    'Gets the default config of this program.'
    global config
    if config is None:
        config = JsonConfig('config.json')
    return config

def sub_template(template: str, config: Optional[JsonConfig]=None, scope: Optional[dict]=None):
    'Substitute #[]# template into global variables and configuration items.'
    if not config: config = default_config()
    if not scope: scope = globals()
    def sub(match):
        field = match.group(1).strip()
        try:
            return str(eval(field, scope))
        except Exception: pass
        if field in config:
            return str(config[field])
        else:
            return ''
    return re.sub(r'#\[(.+?)\]#', sub, template)