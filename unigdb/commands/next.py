import argparse

import unigdb.arch
from unigdb.color import Color
import unigdb.disassemble as disass
import unigdb.commands
from unigdb.commands import GenericCommand


class NextInstCommand(GenericCommand):
    """Step one instruction, but proceed through subroutine calls."""

    _cmdline_ = 'nexti'
    _aliases_ = ["ni", ]

    def __init__(self, cls):
        super(NextInstCommand, self).__init__(cls)

    next_parser = argparse.ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    next_parser.add_argument('n', metavar='N', nargs=argparse.OPTIONAL, help='Step N times')

    def do_nexti(self, args: argparse.Namespace):
        pc = int(unigdb.arch.CURRENT_ARCH.pc)
        insn = disass.get_current_instruction(pc)
        if unigdb.arch.CURRENT_ARCH.is_call(insn):
            if unigdb.arch.CURRENT_ARCH.arch == 'MIPS':
                step_over = unigdb.arch.CURRENT_ARCH.instruction_length * 2
            else:
                step_over = int(disass.get_next_instruction(pc).addr) - pc
            unigdb.arch.UC.emu_start(begin=pc, until=pc + step_over)
            unigdb.proc.alive = True

        # gdb.Breakpoint('*%#x' % (pc + 8), internal=True, temporary=True)
