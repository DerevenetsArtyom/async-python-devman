import argparse
import asyncio
import logging
import os
from functools import partial

import aiofiles
from aiohttp import web


async def archivate(photos_path, delay, request):
    """Asynchronously archive directory on the fly and send it to client"""

    archive_hash = request.match_info["archive_hash"]
    path_to_photos = f"{photos_path}/{archive_hash}"

    if not os.path.exists(path_to_photos):
        logging.debug("Attempt to request non existing archive")
        return web.HTTPNotFound(
            text="Archive does not exist or has been removed"
        )

    command = f"zip -r - {path_to_photos}"

    proc = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    message = f"Started: {command} (pid = {str(proc.pid)})"
    logging.debug(message)

    response = web.StreamResponse(
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": 'attachment; filename="archive.zip"',
        }
    )
    # Send HTTP headers to the client
    await response.prepare(request)

    try:
        while True:
            if delay:
                await asyncio.sleep(delay)
            archive_chunk = await proc.stdout.readline()
            if not archive_chunk:
                message = f"[{command!r} exited with {proc.returncode}]"
                logging.debug(message)
                break

            logging.debug("Sending archive chunk ...")
            await response.write(archive_chunk)

    except asyncio.CancelledError:
        logging.debug("Seems like client was disconnected")
        message = f'Killing "zip" process (pid = {str(proc.pid)})'
        proc.kill()
        logging.debug(message)
        raise
    finally:
        response.force_close()

    return response


async def handle_index_page(request):
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, help="Set directory for photos")
    parser.add_argument("--debug", action="store_true", help="Set debug mode")
    parser.add_argument(
        "--delay",
        type=float,
        help="Set delay between sending chunks in seconds",
    )
    args = parser.parse_args()

    if args.debug or os.getenv("DEBUG") == "1":
        logging.basicConfig(level=logging.DEBUG)

    photos_path = args.path or os.getenv("PHOTOS_PATH", "test_photos")
    delay = args.delay or float(os.getenv("DELAY", "0"))

    app = web.Application()
    app.add_routes(
        [
            web.get("/", handle_index_page),
            web.get(
                "/archive/{archive_hash}/",
                partial(archivate, photos_path, delay),
            ),
        ]
    )
    web.run_app(app)


if __name__ == "__main__":
    main()
