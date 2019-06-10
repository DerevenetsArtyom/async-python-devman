import json
import logging


def sanitize(message):
    return message.replace('\n', '').replace('\r', '')


async def submit_message(reader, writer, message):
    message = '{}\n\n'.format(sanitize(message))
    writer.write(message.encode())
    await writer.drain()
    logging.info('Sent message: {}'.format(sanitize(message)))

    data = await reader.readline()
    logging.info('Received: {}'.format(data.decode()))


async def authorise(reader, writer, token):
    message = token + '\n'
    writer.write(message.encode())
    await writer.drain()

    data = await reader.readline()

    response = json.loads(data.decode())
    if not response:
        logging.info("Invalid token: {}".format(token))
        return False

    data = await reader.readline()
    logging.info('Received: {}'.format(data.decode()))
    return True
