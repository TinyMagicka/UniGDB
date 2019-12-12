import os

import unigdb.memory
import unigdb.commands
from unigdb.color import message
from unigdb.commands import GenericCommand


@unigdb.commands.register_command
class LoadCommand(GenericCommand):
    """Dynamically load FILE into the enviroment for access from UniGDB.
    An optional load OFFSET may also be given as a literal address.
    When OFFSET is provided, FILE must also be provided.  FILE can be provided
    on its own."""

    _cmdline_ = "load"
    _syntax_ = "{:s} [FILE] [OFFSET]".format(_cmdline_)

    def __init__(self):
        super(LoadCommand, self).__init__()

    def do_xxx(self, arg):
        argv = unigdb.commands.parse_arguments(arg)
        if len(argv) != 2:
            self.help_xxx()
            return None
        if not os.path.exists(argv[0]):
            message.error('File not found: %s' % argv[0])
        offset = eval(argv[1])
        data = open(argv[0], 'rb').read()
        unigdb.memory.write(data, offset)
