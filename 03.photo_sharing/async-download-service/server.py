import asyncio
import logging
import os

import aiofiles
from aiohttp import web

INTERVAL_SECS = 1

logging.basicConfig(level=logging.DEBUG)

"""
https://www.programcreek.com/python/example/91858/aiohttp.web.StreamResponse
https://gist.github.com/jbn/fc90e3ddbc5c60c698d07b3df30004c8
"""


async def archivate(request):
    base_dir = 'test_photos'
    archive_hash = request.match_info['archive_hash']

    path_to_photos = f'{base_dir}/{archive_hash}'

    if not os.path.exists(path_to_photos):
        logging.error('Attempt to request non existing archive')
        return web.HTTPNotFound(
            text='Archive does not exist or has been removed')

    command = f'zip -r - {path_to_photos}'

    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    message = f'Started: {command} (pid = {str(proc.pid)})'
    logging.debug(message)

    response = web.StreamResponse(headers={
        # Большинство браузеров не отрисовывают частично загруженный контент,
        # только если это не HTML.
        # Поэтому отправляем клиенту именно HTML, указываем это в Content-Type.
        'Content-Type': 'text/html',
        # TODO: application/zip???

        'Content-Disposition': 'attachment; filename="archive.zip"'
    })

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)

    while True:
        archive_chunk = await proc.stdout.readline()
        if archive_chunk:
            logging.info('Sending archive chunk ...')
            await response.write(archive_chunk)
        else:
            message = f'[{command!r} exited with {proc.returncode}]'
            logging.info(message)
            break

        await asyncio.sleep(INTERVAL_SECS)

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
