from json import loads, dumps
import os
import logging

logger = logging.getLogger(__name__)

def json_init():
    data = {}
    for json in os.listdir('resource/json'):
        with open(f'resource/json/{json}', 'r', encoding="utf-8") as f:
            data[json.split('.')[0]] = loads(f.read())

    return data
