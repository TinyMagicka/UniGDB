import argparse
import cmd2


import unigdb.arch
from unigdb.color import Color
import unigdb.disassemble as disass
import unigdb.commands
from unigdb.commands import GenericCommand
from unigdb.commands.breakpoint import setBreakpoint


@unigdb.commands.register_command
class NextInstCommand(GenericCommand):
    """Step one instruction, but proceed through subroutine calls."""

    _cmdline_ = 'nexti'
    _aliases_ = ["ni", ]

    def __init__(self, cls):
        super(NextInstCommand, self).__init__(cls)

    next_parser = argparse.ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    next_parser.add_argument('n', type=int, metavar='N', nargs=argparse.OPTIONAL, help='Step N times')

    @cmd2.with_argparser(next_parser)
    def do_nexti(self, args: argparse.Namespace):
        pc = int(unigdb.arch.CURRENT_ARCH.pc)
        insn = disass.get_current_instruction(pc)

        if not args.n:
            step_over = int(disass.get_next_instruction(pc).address) - pc
        else:
            step_over = unigdb.arch.CURRENT_ARCH.instruction_length * args.n

        if unigdb.arch.CURRENT_ARCH.is_call(insn):
            if unigdb.arch.CURRENT_ARCH.arch == 'MIPS':
                step_over = unigdb.arch.CURRENT_ARCH.instruction_length * 2
        setBreakpoint(pc + step_over, temporary=True)
        unigdb.proc.alive = True
        unigdb.arch.UC.emu_start(begin=pc, until=pc + 100)

        # gdb.Breakpoint('*%#x' % (pc + 8), internal=True, temporary=True)
