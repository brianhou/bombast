import pprint
import random
import string as _string
import sys

_first_char = _string.ascii_uppercase + _string.ascii_lowercase
_charset = _string.ascii_uppercase + _string.ascii_lowercase + _string.digits*5 + '_'*20

def randident(a, b=None):
    length = None
    try:
        length = random.randrange(a, b)
    except:
        pass
    if length is None or b is None:
        length = a
    return random.choice(_first_char) + ''.join(random.choice(_charset) for _ in range(length-1))
random.randident = randident

def debug(*args):
    print(*args, file=sys.stderr)

VERSION = sys.version_info
