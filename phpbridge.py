import json
import math
import os.path
import subprocess as sp
import sys

from typing import Any, IO, List

php_server_path = os.path.join(os.path.dirname(__file__), 'server.php')


class PHPException(Exception):
    pass


class PHPBridge:
    def __init__(self, input_: IO[str], output: IO[str]) -> None:
        self.input = input_
        self.output = output
        self.const = ConstantGetter(self)
        self.fun = FunctionGetter(self)

    def forward_stderr(self) -> None:
        for line in self.output:
            sys.stderr.write(line)
        raise RuntimeError("Can't communicate with PHP")

    def send(self, command: str, data: Any) -> None:
        try:
            json.dump({'cmd': command, 'data': data}, self.input)
            self.input.write('\n')
            self.input.flush()
        except BrokenPipeError:
            self.forward_stderr()

    def receive(self) -> dict:
        line = self.output.readline()
        try:
            return json.loads(line)
        except json.decoder.JSONDecodeError:
            sys.stderr.write(line)
            self.forward_stderr()
            return None

    def encode(self, data: Any) -> dict:
        if isinstance(data, str):
            return {'type': 'string', 'value': data}
        if isinstance(data, bool):
            return {'type': 'boolean', 'value': data}
        if isinstance(data, int):
            return {'type': 'integer', 'value': data}
        if isinstance(data, float):
            return {'type': 'double', 'value': data}
        if data is None:
            return {'type': 'NULL', 'value': data}

        if isinstance(data, dict) and all(type(key) is str for key in data):
            return {'type': 'array', 'value': {k: self.encode(v)
                                               for k, v in data.items()}}
        if isinstance(data, list):
            return {'type': 'array', 'value': [self.encode(item)
                                               for item in data]}

        raise RuntimeError("Can't encode {!r}".format(data))

    def decode(self, data: dict) -> Any:
        type_ = data['type']
        value = data['value']
        if type_ in {'string', 'integer', 'NULL', 'boolean'}:
            return value
        elif type_ == 'double':
            if value == 'INF':
                return math.inf
            elif value == 'NAN':
                return math.nan
            return value
        elif type_ == 'array':
            if isinstance(value, list):
                return [self.decode(item) for item in value]
            elif isinstance(value, dict):
                return {key: self.decode(value)
                        for key, value in value.items()}
        elif type_ == 'thrownException':
            raise PHPException(value['message'])
        raise RuntimeError("Unknown type {!r}".format(type_))

    def send_command(self, cmd: str, data: Any = None) -> Any:
        self.send(cmd, data)
        return self.decode(self.receive())

    @classmethod
    def start_process(cls, fname: str = php_server_path):
        proc = sp.Popen(['php', fname], stdin=sp.PIPE, stderr=sp.PIPE,
                        universal_newlines=True)
        return cls(proc.stdin, proc.stderr)


class PHPFunction:
    def __init__(self, bridge: PHPBridge, name: str) -> None:
        self.bridge = bridge
        self.name = name

    def __call__(self, *args: Any) -> Any:
        return self.bridge.send_command(
            'callFun',
            {'name': self.name,
             'args': [self.bridge.encode(arg) for arg in args]})

    def __repr__(self) -> str:
        return "<PHP function {}>".format(self.name)


class PHPClass:
    def __init__(self, bridge: PHPBridge, name: str) -> None:
        self.bridge = bridge
        self.name = name

    def __call__(self, *args: Any) -> Any:
        return self.bridge.send_command(
            'createObject',
            {'name': self.name,
             'args': [self.bridge.encode(arg) for arg in args]})

    def __getattr__(self, attr: str) -> Any:
        return self.bridge.send_command(
            'getAttribute', {'object': self.name, 'name': attr})


class Getter:
    def __init__(self, bridge: PHPBridge) -> None:
        self.bridge = bridge

    def __getattr__(self, attr: str) -> Any:
        raise NotImplementedError

    def __getitem__(self, item: str) -> Any:
        return self.__getattr__(item)


class ConstantGetter(Getter):
    def __getattr__(self, attr: str) -> Any:
        return self.bridge.send_command('getConst', attr)

    def __dir__(self) -> List[str]:
        return self.bridge.send_command('listConsts')


class FunctionGetter(Getter):
    def __getattr__(self, attr: str) -> PHPFunction:
        return PHPFunction(self.bridge, attr)

    def __dir__(self) -> List[str]:
        return self.bridge.send_command('listFuns')


php = PHPBridge.start_process()
