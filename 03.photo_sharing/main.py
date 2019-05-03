import asyncio

"""
Shell command:
    zip -r - * > test.zip
Python code for left side:
    import glob
    import subprocess

    archive = subprocess.call(['zip', '-r', '-'] + glob.glob('*'))
    archive = subprocess.check_output(['zip', '-r', '-'] + glob.glob('*'))
    process = subprocess.Popen(['zip', '-r', '-'] + glob.glob('*'))
"""


async def archivate(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    print('Started:', cmd, '(pid = ' + str(proc.pid) + ')')

    full_archive = bytearray()

    while True:
        archive_chunk = await proc.stdout.readline()
        if archive_chunk:
            full_archive += archive_chunk
        else:
            print(f'[{cmd!r} exited with {proc.returncode}]')
            break

    with open('archive.zip', 'wb') as arc:
        arc.write(full_archive)

command = 'zip -r - async-download-service/'

loop = asyncio.get_event_loop()
loop.run_until_complete(archivate(command))
loop.close()

