import asyncio


async def run(programm: str, *args: str, logger=None, **kwargs):
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


async def output(programm: str, *args: str, **kwargs):
    command = " ".join([programm, *args])
    
    proccess = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        **kwargs
    )
    
    stdout, _ = await proccess.communicate()

    return stdout.decode()
