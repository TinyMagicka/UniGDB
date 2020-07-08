# import unigdb.arch
import unigdb.color
import unigdb.commands
import unigdb.commands.context
import unigdb.commands.breakpoint
import unigdb.commands.hexdump
import unigdb.commands.builtins
import unigdb.commands.nexti
# import unigdb.commands.pattern
# import unigdb.commands.pcustom
import unigdb.commands.registers
import unigdb.commands.theme
# import unigdb.commands.self
import unigdb.disassemble
# import unigdb.exception
# import unigdb.functions
# import unigdb.handlers
import unigdb.memory
import unigdb.proc
import unigdb.prompt
import unigdb.regs
import unigdb.typeinfo
import unigdb.ui
import unigdb.gdbu
import capstone


__version__ = '0.1.2'
version = __version__


__all__ = [
    'arch',
    'chain',
    'color',
    'events',
    'commands',
    'hexdump',
    # 'ida',
    'memoize',
    'memory',
    'proc',
    'regs',
    'typeinfo',
    'ui',
]


# pre_commands = [
#     'set confirm off',
#     'set verbose off',
#     'set pagination off',
#     'set height 0',
#     'set history filename /tmp/.gdb_history'
#     'set history expansion on',
#     'set history save on',
#     'set follow-fork-mode child',
#     'set backtrace past-main on',
#     'set step-mode on',
#     'set print pretty on',
#     'set width %i' % unigdb.ui.get_window_size()[1],
#     'handle SIGALRM nostop print nopass',
#     'handle SIGBUS  stop   print nopass',
#     'handle SIGPIPE nostop print nopass',
#     'handle SIGSEGV stop   print nopass',
# ]

# for line in pre_commands:
#     gdb.execute(line.strip())


# handle resize event to align width and completion
# signal.signal(signal.SIGWINCH, lambda signum, frame: gdb.execute("set width %i" % unigdb.ui.get_window_size()[1]))

# More info: https://sourceware.org/bugzilla/show_bug.cgi?id=21946
# As stated on GDB's bugzilla that makes remote target search slower.
# After GDB gets the fix, we should disable this only for bugged GDB versions.
# if 1:
#     gdb.execute('set remote search-memory-packet off')


# unigdb.events.cont(unigdb.handlers.continue_handler)
# unigdb.events.stop(unigdb.handlers.hook_stop_handler)
# unigdb.events.new_objfile(unigdb.handlers.new_objfile_handler)
# unigdb.events.exit(unigdb.handlers.exit_handler)

# if gdb.progspaces()[0].filename is not None:
#     unigdb.arch.update()
