import abc
import sys
import re
import cmd2
import binascii

from unigdb.color import Color
from unigdb.color import message
import unigdb.config

__commands__ = []


def register_command(cls):
    """Decorator for registering new PWNGEF (sub-)command to GDB."""
    sys.modules[__name__].__commands__.append(cls)
    return cls


def register_priority_command(cls):
    """Decorator for registering new command with priority, meaning that it must
    loaded before the other generic commands."""
    sys.modules[__name__].__commands__.insert(0, cls)
    return cls


class GenericCommand:
    """This is an abstract class for invoking commands, should not be instantiated."""
    __metaclass__ = abc.ABCMeta

    _aliases_ = []

    def __init__(self):
        syntax = 'Usage: %s\n\n' % self._cmdline_
        self.__doc__ = syntax + Color.yellowify(self.__doc__.replace(" " * 4, "")) + '\n'

    @abc.abstractmethod
    def help_xxx(self):
        print(self.__doc__)

    @abc.abstractproperty
    def _cmdline_(self):
        pass

    def __get_setting_name(self, name):
        def __sanitize_class_name(clsname):
            if " " not in clsname:
                return clsname
            return "-".join(clsname.split())

        class_name = __sanitize_class_name(self.__class__._cmdline_)
        return "{:s}.{:s}".format(class_name, name)

    @property
    def settings(self):
        """Return the list of settings for this command."""
        return unigdb.config.get_command(self._cmdline_)

    def get_setting(self, name):
        key = self.__get_setting_name(name)
        setting = unigdb.config.get(key)
        return setting

    def has_setting(self, name):
        key = self.__get_setting_name(name)
        return unigdb.config.has(key)

    def add_setting(self, name, value, description=""):
        name = '%s.%s' % (self._cmdline_, name)
        return unigdb.config.set(name, value, description)

    def del_setting(self, name):
        key = self.__get_setting_name(name)
        return unigdb.config.delete(key)


def parse_arguments(arg_line):
    # for reg in re.findall(r'[$@][a-z0-9]+', arg_line):
    #     arg_line.replace(reg, unigdb.regs.get_register(reg), 1)
    args = re.findall(r'[\"\'].*?[\"\']|[^ ]+', arg_line)
    # replace quotes
    args = list(map(lambda x: re.sub(r'[\"\']', '', x), args))
    result = []
    for item in args:
        if '\\x' in item:
            item = binascii.unhexlify(item.replace('\\x', ''))
            result.append(item)
        else:
            result.append(item)
    return result
