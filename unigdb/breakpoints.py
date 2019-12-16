import unigdb.commands.breakpoint


def setBreakpoint(addr: int, temporary: bool):
    unigdb.commands.breakpoint._breakpoints_[addr] = temporary


def hasBreakpoint(addr: int):
    return unigdb.commands.breakpoint._breakpoints_.get(addr)


def delBreakpoint(addr: int):
    unigdb.commands.breakpoint._breakpoints_.pop(addr)
