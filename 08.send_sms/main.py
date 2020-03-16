import asks
import trio
import os

from dotenv import load_dotenv

from exceptions import SmscApiError


async def request_smsc(method, login, password, payload, message=None):
    """Send request to SMSC.ru service.

    Args:
        method (str): API method. E.g. 'send' or 'status'.
        login (str): Login for account on SMSC.
        password (str): Password for account on SMSC.
        payload (dict): Additional request params, override default ones.
        message (str): Message to send.
    Returns:
        dict: Response from SMSC API.
    Raises:
        SmscApiError: If SMSC API response status is not 200 or it has `"ERROR" in response.

    Examples:
        >>> request_smsc("send", "my_login", "my_password", {"phones": "+79123456789"})
        {"cnt": 1, "id": 24}
        >>> request_smsc("status", "my_login", "my_password", {"phone": "+79123456789", "id": "24"})
        {'status': 1, 'last_date': '28.12.2019 19:20:22', 'last_timestamp': 1577550022}
    """

    if not payload:
        raise SmscApiError("Payload is not passed")

    key_is_present = False
    for key in payload:
        if key == "phones" or key == "phone":
            key_is_present = True
    if not key_is_present:
        raise SmscApiError("Payload should contain 'phone' or 'phones' keys")

    common_url = f"https://smsc.ru/sys/{method}.php?login={login}&psw={password}"
    if message is None:
        message = "Внимание,%20вечером%20будет%20шторм!"

    # TODO: move code inside conditions to separate functions
    if method == "send":
        payload_str = "".join([f"{key}={value}" for key, value in payload.items()])
        formatting = 3
        cost = 3
        charset = "utf-8"

        # TODO: use 'params' dict instead of manually formatted string
        url = f"{common_url}&{payload_str}&mes={message}&charset={charset}&fmt={formatting}&cost={cost}"
        response = await asks.get(url)
        # {"id": 63, "cnt": 1, "cost": "3.8", "balance": "286.55"}
        # {'id': 67, 'cnt': 1, 'cost': '3.8', 'balance': '282.75'}

        result = response.json()

    elif method == "status":
        phone_str = f"phone={payload['phone']}"
        id_str = f"id={payload['id']}"
        formatting = 3

        url = f"{common_url}&{phone_str}&{id_str}&fmt={formatting}"
        response = await asks.get(url)
        # {'status': 1, 'last_date': '11.03.2020 20:35:30', 'last_timestamp': 1583948130}

        result = response.json()
    else:
        raise SmscApiError("Unsupported method")

    if "error" in result:
        # {'error': 'invalid number', 'error_code': 7, 'id': 64}
        # {"error": "duplicate request, wait a minute", "error_code": 9}
        # {'error': 'parameters error', 'error_code': 1}
        raise SmscApiError(f"An error occurred during request: '{result['error']}' with code {result['error_code']}")

    return result


async def main():
    load_dotenv()

    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    phone = os.getenv("PHONE")

    await request_smsc("send", login, password, {"phones": phone})
    await request_smsc("status", login, password, {"phone": phone, "id": 67})


if __name__ == "__main__":
    trio.run(main)
