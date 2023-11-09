from functools import reduce
from msgpack import unpackb, packb


def deep_get(dictionary, keys, default=None):
    return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)


def deep_set(dictionary, keys, value):
    d = dictionary
    for key in keys.split(".")[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    d[keys.split(".")[-1]] = value


def deep_unset(dictionary, keys):
    d = dictionary
    for key in keys.split(".")[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    if keys.split(".")[-1] in d:
        del d[keys.split(".")[-1]]

def deep_clone(dictionary):
    return unpackb(packb(dictionary), strict_map_key=False)

