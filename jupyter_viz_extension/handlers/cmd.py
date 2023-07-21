import asyncio


async def run(programm: str, *args: list[str], **kwargs):
    command = " ".join([programm, *args])
    
    proccess = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs
    )

    stdout, stderr = await proccess.communicate()

    print(f'{command!r} exited with {proccess.returncode}')
    if stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    
    return proccess.returncode


async def output(programm: str, *args: list[str], **kwargs):
    command = " ".join([programm, *args])
    
    proccess = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        **kwargs
    )
    
    stdout, _ = await proccess.communicate()

    return stdout.decode()
