from unicorn import *
import os
import cmd2
import argparse

import unigdb.arch
import unigdb.memory
import unigdb.events
import unigdb.commands
from unigdb.color import message, Color
from unigdb.commands import GenericCommand


@unigdb.commands.register_command
class RunCommand(GenericCommand):
    """Start debugged code."""

    _cmdline_ = "run"

    def __init__(self, cls):
        super(RunCommand, self).__init__()
        self.statement_parser = cls.statement_parser
        self.cls = cls

    def do_run(self, arg):
        reg_pc = unigdb.regs.get_register('$pc')
        unigdb.arch.UC.hook_add(UC_HOOK_CODE, unigdb.events.hook_code)
        unigdb.arch.UC.hook_add(UC_HOOK_BLOCK, unigdb.events.hook_block)
        unigdb.arch.UC.hook_add(UC_HOOK_INTR, unigdb.events.hook_intr)
        # unigdb.arch.UC.mem_map()
        # emulate machine code in infinite time
        try:
            unigdb.arch.UC.emu_start(begin=reg_pc, until=reg_pc + 0x10000)
            unigdb.arch.alive = True
        except UcError as e:
            message.error('{!} Error => %s' % e)
            return None


@unigdb.commands.register_command
class LoadCommand(GenericCommand):
    """Dynamically load FILE into the enviroment for access from UniGDB."""

    _cmdline_ = "load"

    def __init__(self, cls):
        super(LoadCommand, self).__init__()
        self.statement_parser = cls.statement_parser
        self.cls = cls

    load_parser = cmd2.Cmd2ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    load_parser.add_argument('file', metavar='FILE', completer_method=cmd2.Cmd.path_complete, help='Path to file for load in memory')
    load_parser.add_argument('offset', metavar='OFFSET', type=int, help='Address in mapped spaces for insert file data')

    @cmd2.with_argparser(load_parser)
    def do_load(self, args: argparse.Namespace):
        if not os.path.exists(args.file):
            message.error('File not found: %s' % args.file)
        data = open(args.file, 'rb').read()
        unigdb.memory.write(args.offset, data)
