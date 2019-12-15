#!/usr/bin/python
import sys
from os import path

directory, file = path.split(__file__)
directory = path.expanduser(directory)
directory = path.abspath(directory)

sys.path.append(directory)

import unigdb
from unigdb.gdbu import CoreShell


if __name__ == '__main__':
    shell = CoreShell()
    shell.cmdloop()
