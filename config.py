import json, re
from typing import Optional

class JsonConfig(dict):
    def __init__(self, file: str):
        self._file = file
        super().__init__(json.load(open(file)))
    def __repr__(self) -> str:
        return '<JsonConfig from {!r}>'.format(self._file)

config = None

def default_config() -> JsonConfig:
    global config
    if config is None:
        config = JsonConfig('config.json')
    return config

def sub_template(template: str, config: Optional[JsonConfig]=None, scope: Optional[dict]=None):
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