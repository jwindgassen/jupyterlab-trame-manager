from dataclasses import dataclass, field
from typing import NamedTuple
from io import FileIO
from subprocess import Popen


__all__ = ["TrameApp", "TrameAppInstance", "ParaViewServer", "UserData"]


@dataclass(kw_only=True)
class ParaViewServer:
    name: str
    account: str
    partition: str
    nodes: int
    time_used: str
    time_limit: str
    state: str
    node_list: str
    connection_address: str

    def dump(self) -> dict:
        return {
            "name": self.name,
            "account": self.account,
            "partition": self.partition,
            "nodes": self.nodes,
            "timeUsed": self.time_used,
            "timeLimit": self.time_limit,
            "state": self.state,
            "connectionAddress": self.connection_address,
        }


@dataclass(kw_only=True)
class TrameAppInstance:
    # User defined
    name: str
    data_directory: str

    # Generated
    uuid: str
    port: int
    base_url: str
    log_dir: str
    auth_key: str
    auth_key_file: str

    logger: FileIO
    process_handle: Popen | None

    def dump(self) -> dict:
        return {
            "name": self.name,
            "dataDirectory": self.data_directory,
            "port": self.port,
            "base_url": self.base_url,
            "log": self.log_dir,
        }


@dataclass(kw_only=True)
class TrameApp:
    name: str
    display_name: str
    path: str
    command: str
    working_directory: str = None
    instances: list[TrameAppInstance] = field(default_factory=list)

    def dump(self) -> dict:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "path": self.path,
            "instances": [instance.dump() for instance in self.instances]
        }


class UserData(NamedTuple):
    user: str
    home: str
    accounts: list[str]
    partitions: list[str]
