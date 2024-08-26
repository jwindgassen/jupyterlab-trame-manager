from ..configuration import Configuration, UserData, ParaViewServer


class DesktopConfiguration(Configuration):
    async def get_running_servers(self) -> list[ParaViewServer]:
        return [
            ParaViewServer(
                name="Local Server",
                account="",
                partition="",
                nodes=1,
                time_used="00:00",
                time_limit="00:00",
                state="RUNNING",
                connection_address="localhost:11111"
            )
        ]

    async def launch_paraview(self, options) -> tuple[int, str]:
        raise RuntimeError("Can't launch ParaView on Desktop")

    async def get_user_data(self) -> UserData:
        return UserData(user="Local User", accounts=[], partitions=[])
