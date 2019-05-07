import argparse
import asyncio
import logging
import os

import aiofiles
from aiohttp import web


async def archivate(request):
    archive_hash = request.match_info['archive_hash']
    path_to_photos = f'{PHOTOS_PATH}/{archive_hash}'

    if not os.path.exists(path_to_photos):
        logging.debug('Attempt to request non existing archive')
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
        'Content-Disposition': 'attachment; filename="archive.zip"'
    })

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)

    try:
        while True:
            archive_chunk = await proc.stdout.readline()
            if archive_chunk:
                if DELAY_BETWEEN_SENDING:
                    await asyncio.sleep(DELAY_BETWEEN_SENDING)
                logging.debug('Sending archive chunk ...')
                await response.write(archive_chunk)
            else:
                message = f'[{command!r} exited with {proc.returncode}]'
                logging.debug(message)
                break

    except asyncio.CancelledError:
        logging.debug('Seems like client was disconnected')
        raise
    finally:
        logging.debug('Killing "zip" process')
        proc.kill()
        response.force_close()

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, help='Set directory for photos')
    parser.add_argument('--debug', action='store_true', help='Set debug mode')
    parser.add_argument('--delay', type=float,
                        help='Set delay between sending chunks in seconds')

    args = parser.parse_args()

    if args.debug or os.getenv('DEBUG') == '1':
        logging.basicConfig(level=logging.DEBUG)
    PHOTOS_PATH = args.path or os.getenv('PHOTOS_PATH', 'test_photos')
    DELAY_BETWEEN_SENDING = args.delay or float(
        os.getenv('DELAY_BETWEEN_SENDING', '1')
    )

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
