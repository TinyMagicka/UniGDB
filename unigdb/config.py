"""
Dynamic configuration system for unigdb, using GDB's built-in Parameter
mechanism.

All unigdb Parameter types are accessible via property access on this
module, for example:

    >>> unigdb.config.set('example_value', 7, 'an example')
    >>> unigdb.config.get('example_value')
    7
"""
import os
import sys
import tempfile

__config__ = {}
__unigdb__ = None

UNIGDB_RC = os.path.join(os.getenv("HOME"), ".unigdb.rc")
UNIGDB_TEMP_DIR = os.path.join(tempfile.gettempdir(), "unigdb")
HORIZONTAL_LINE = "-"
VERTICAL_LINE = "|"

DOWN_ARROW = "\u21b3"
RIGHT_ARROW = "\u2192"
LEFT_ARROW = "\u2190"


def get(name, get_all=False):
    module = sys.modules[__name__]
    name = name.replace('-', '_')
    setting = module.__config__.get(name, None)
    if not setting or get_all:
        return setting
    return setting[0]


def set(name, default, docstring):
    module = sys.modules[__name__]
    name = name.replace('-', '_')
    docstring = docstring.strip()
    module.__config__[name] = [default, docstring]
    return module.__config__[name][0]


def delete(name):
    module = sys.modules[__name__]
    del module.__config__[name]
    return None


def has(name):
    module = sys.modules[__name__]
    return name in module.__config__


def get_command(name):
    module = sys.modules[__name__]
    return [x.split(".", 1)[1] for x in module.__config__ if x.startswith("{:s}.".format(name))]
