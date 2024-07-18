import asyncio


async def run(programm: str, *args: str, logger=None, **kwargs) -> int:
    """
    Run a command asyncronously in a subprocess

    @param programm: The command to run
    @param args: Arguments to the programm
    @param logger: A optional logger to log stdout and stderr into
    @param kwargs: Additional Arguments passed to asyncio.create_subprocess_shell
    @return: The exit-code of the command
    """
    command = " ".join([programm, *args])
    
    proccess = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs
    )

    stdout, stderr = await proccess.communicate()

    if logger:
        logger.info(f"{command!r} exited with {proccess.returncode}")
        if stdout:
            logger.info(f"[stdout]\n{stdout.decode()}")
        if stderr:
            logger.info(f"[stderr]\n{stderr.decode()}")
    
    return proccess.returncode


async def output(programm: str, *args: str, logger=None, **kwargs) -> tuple[int, str]:
    """
    Run a command asyncronously in a subprocess and collect stdout and stderr

    @param programm: The command to run
    @param args: Arguments to the programm
    @param logger: A optional logger to log stdout and stderr into
    @param kwargs: Additional Arguments passed to asyncio.create_subprocess_shell
    @return: A tuple with exit-code of the command and a string containing the output of the command
    """
    command = " ".join([programm, *args])
    
    proccess = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        **kwargs
    )
    
    stdout, _ = await proccess.communicate()

    if logger:
        logger.info(f"{command!r} exited with {proccess.returncode}")
        if stdout:
            logger.info(f"[stdout]\n{stdout.decode()}")

    return proccess.returncode, stdout.decode()
