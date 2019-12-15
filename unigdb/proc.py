import functools
import sys

from unigdb.color import message

module = sys.modules[__name__]
alive = False
init = False


def OnlyWhenRunning(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        if module.alive:
            return func(*a, **kw)

    return wrapper


def OnlyWhenInit(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        if module.init:
            return func(*a, **kw)
        else:
            message.error('{!} Error => Unicorn engine not initialized')

    return wrapper
