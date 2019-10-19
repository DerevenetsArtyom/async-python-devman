import os
import json


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
