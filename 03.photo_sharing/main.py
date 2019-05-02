import glob
import subprocess

import asyncio

"""
Shell command:
    zip -r - * > test.zip
Python code for left side:
    archive = subprocess.call(['zip', '-r', '-'] + glob.glob('*'))
"""

with open('archive1.zip', 'wb') as arc:
    archive = subprocess.check_output(
        ['zip', '-r', '-'] + glob.glob('async-download-service/')
    )
    arc.write(archive)

# Перепишите архивацию на asyncio
# У модуля subprocess есть асинхронный аналог — asyncio subprocess.
# Он позволяет разбить долгий процесс архивации на части и отправлять
# клиенту архив порциями. Все будут в выигрыше:
# клиент начнет скачивать файл сразу, не дожидаясь завершения архивации,
# а вам не придется хранить в памяти сервера архив целиком.

# Цель
# Скрипт создаст файл c архивом archive.zip, не загружая его в память целиком.
# Программа будет построена на asyncio.

# Проверьте, что архив archive.zip удастся распаковать.

# Что понадобится
# переписать код из туториала asyncio
# удалите всё лишнее, оставьте одну асинхронную функцию archivate
# переписать код архивации
# asyncio subprocess — замена для subprocess
# заменить переменную archive на archive_chunk
# while True

# Советы
# В отладочном коде останется синхронная операция записи в файл,
# и её тоже можно сделать асинхронной с помощью aiofiles.
# Это не обязательно, ведь в конечной программе этого кода не будет.


