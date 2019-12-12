import abc
import sys

# import gdb
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

    def __init__(self, name):
        syntax = Color.yellowify("\nSyntax: ") + self._syntax_
        example = Color.yellowify("\nExample: ") + self._example_ if self._example_ else ""
        self.__doc__ = self.__doc__.replace(" " * 4, "") + syntax + example

    @abc.abstractmethod
    def do_xxx(self):
        pass

    def help_xxx(self):
        message.hint(self.__doc__)

    def complete_xxx(self):
        pass

    @abc.abstractproperty
    def _cmdline_(self):
        pass

    @abc.abstractproperty
    def _syntax_(self):
        pass

    @abc.abstractproperty
    def _example_(self):
        return ""

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


def parse_arguments(args):
    result = []
    for item in args:
        if item.isdigit():
            result.append(int(item))
        if item.lower().startswith('0x'):
            result.append(int(item, 16))
        else:
            result.append(item)
    return result
