import json
import random
import string
import sys

_first_char = string.ascii_uppercase + string.ascii_lowercase
_charset = (
    string.ascii_uppercase + string.ascii_lowercase + string.digits * 5 + "_" * 20
)


def randident(a, b=None):
    length = None
    try:
        length = random.randrange(a, b)
    except:
        pass
    if length is None or b is None:
        length = a
    return random.choice(_first_char) + "".join(
        random.choice(_charset) for _ in range(length - 1)
    )


def load_config(path, default="bombast.config"):
    if path is None:
        path = default
    try:
        with open(path) as f:
            return json.load(f)
    except IOError as e:
        if path != default:
            raise
    except ValueError as e:
        print("Error:", path, "is an invalid configuration file", file=sys.stderr)
        exit(1)
    return {}


VERSION = sys.version_info
