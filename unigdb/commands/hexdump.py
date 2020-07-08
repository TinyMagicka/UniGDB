import cmd2
import argparse

import unigdb.commands
from unigdb.color import Color
from unigdb.commands import GenericCommand
from unigdb.gdbu import parse_and_eval


@unigdb.commands.register_command
class HexDumpCommand(GenericCommand):
    '''Hexdumps data at the specified address (or at $sp)'''
    _cmdline_ = "hexdump"
    _syntax_ = "{:s} [address|reg] [count]".format(_cmdline_)

    def __init__(self, cls):
        super(HexDumpCommand, self).__init__(cls)
        self.add_setting("hexdump_width", 16, "line width of hexdump command")
        self.add_setting('hexdump_bytes', 64, 'number of bytes printed by hexdump command')
        self.add_setting('hexdump_colorize_ascii', True, 'whether to colorize the hexdump command ascii section')
        self.add_setting('hexdump_ascii_block_separator', '│', 'block separator char of the hexdump command')

    hexdump_parser = cmd2.Cmd2ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    hexdump_parser.add_argument('address', nargs=argparse.OPTIONAL, help='Address for dump')
    hexdump_parser.add_argument('count', nargs=argparse.OPTIONAL, help='Count bytes of read')

    @cmd2.with_argparser(hexdump_parser)
    def do_hexdump(self, args: argparse.Namespace):
        width = self.get_setting('hexdump_width')
        count = parse_and_eval(args.count) if args.count else self.get_setting('hexdump_bytes')
        if not args.address:
            address = int(unigdb.arch.CURRENT_ARCH.sp)
        else:
            address = parse_and_eval(args.address)

        data = unigdb.memory.read(address, count)
        for _, line in enumerate(unigdb.hexdump.hexdump(data, address=address, width=width)):
            print(line)
        return None
