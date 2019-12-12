#!/usr/bin/python
import sys
from os import path

directory, file = path.split(__file__)
directory = path.expanduser(directory)
directory = path.abspath(directory)

sys.path.append(directory)

from unigdb.gdbu import CoreShell
import unigdb


if __name__ == '__main__':
    shell = CoreShell()
    shell.cmdloop()
