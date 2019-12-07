import os
import json

from schema import WindowBoundsSchema, BusSchema


def load_routes(directory_path="routes"):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, "r", encoding="utf8") as file:
                yield json.load(file)


def generate_bus_id(emulator_id, route_id, bus_index):
    if emulator_id:
        return f"{emulator_id}-{route_id}-{bus_index}"
    return f"{route_id}-{bus_index}"


def validate_bus_message(message):
    schema = BusSchema()
    return schema.validate(data=message)


def validate_client_message(message):
    schema = WindowBoundsSchema()
    return schema.validate(data=message)


def validate_message(json_message, source):
    result = {"data": json_message, 'errors': None}

    try:
        message = json.loads(json_message)
    except json.JSONDecodeError:
        result['errors'] = ['Requires valid JSON']
        return result

    result['data'] = message.get('data', message)

    validating_functions = {
        'bus': validate_bus_message,
        'browser': validate_client_message,
    }
    validating_function = validating_functions.get(source)

    if not validating_function:
        result['errors'] = ['Data source is not correct']
    else:
        result['errors'] = validating_function(message)
    return result
