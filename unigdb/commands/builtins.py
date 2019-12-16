from unicorn import *
import os
import cmd2
import argparse

import unigdb.arch
import unigdb.proc
import unigdb.memory
import unigdb.events
import unigdb.commands
from unigdb.color import message, Color
from unigdb.commands import GenericCommand
from unigdb.commands.breakpoint import setBreakpoint
from unigdb.gdbu import parse_and_eval


@unigdb.commands.register_command
class RunCommand(GenericCommand):
    """Start debugged code."""

    _cmdline_ = "run"

    def __init__(self, cls):
        super(RunCommand, self).__init__(cls)

    def do_run(self, arg):
        reg_pc = unigdb.regs.get_register('$pc')
        unigdb.arch.UC.hook_add(UC_HOOK_CODE, self.cls.hook_code)
        unigdb.arch.UC.hook_add(UC_HOOK_BLOCK, self.cls.hook_block)
        unigdb.arch.UC.hook_add(UC_HOOK_INTR, self.cls.hook_intr)
        # emulate machine code in infinite time
        try:
            setBreakpoint(reg_pc, temporary=True)
            unigdb.proc.alive = True
            unigdb.arch.UC.emu_start(begin=reg_pc, until=reg_pc + 0x10000)
        except UcError as e:
            message.error('{!} Error => %s' % e)
            return None


@unigdb.commands.register_command
class LoadCommand(GenericCommand):
    """Dynamically load FILE into the enviroment for access from UniGDB."""

    _cmdline_ = "load"

    def __init__(self, cls):
        super(LoadCommand, self).__init__(cls)

    load_parser = cmd2.Cmd2ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    load_parser.add_argument('file', metavar='FILE', completer_method=cmd2.Cmd.path_complete, help='Path to file for load in memory')
    load_parser.add_argument('offset', metavar='OFFSET', help='Address in mapped spaces for insert file data')

    @cmd2.with_argparser(load_parser)
    def do_load(self, args: argparse.Namespace):
        args.offset = parse_and_eval(args.offset)
        if not os.path.exists(args.file):
            message.error('File not found: %s' % args.file)
        data = open(args.file, 'rb').read()
        unigdb.memory.write(args.offset, data)


@unigdb.commands.register_command
class ContinueCommand(GenericCommand):
    """Continue program being debugged, after signal or breakpoint."""

    _cmdline_ = "continue"
    _aliases_ = ["c", ]

    def __init__(self, cls):
        super(ContinueCommand, self).__init__(cls)

    con_parser = argparse.ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    con_parser.add_argument('n', metavar='N', nargs=argparse.OPTIONAL, help='Step N times')

    @cmd2.with_argparser(con_parser)
    def do_continue(self, args: argparse.Namespace):
        pc = int(unigdb.arch.CURRENT_ARCH.pc)
        unigdb.proc.alive = True
        unigdb.arch.UC.emu_start(begin=pc, until=pc + 10000)
