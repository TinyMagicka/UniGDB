#!/usr/bin/python
import sys
from os import path
from argparse import ArgumentParser

directory, file = path.split(__file__)
directory = path.expanduser(directory)
directory = path.abspath(directory)

sys.path.append(directory)

import unigdb
from unigdb.gdbu import CoreShell


def parse_args():
    parser = ArgumentParser(add_help=True)
    parser.add_argument('-ex', metavar='COMMNAND', dest='ex', help='Execute given UniGDB command')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    shell = CoreShell()
    if args.ex:
        shell.onecmd_plus_hooks(args.ex)
    shell.cmdloop()
