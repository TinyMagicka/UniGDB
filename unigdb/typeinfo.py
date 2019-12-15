"""
Common types, and routines for manually loading types from file
via GCC.
"""
import sys
# import pwngef.events

module = sys.modules[__name__]


# @pwngef.events.stop
def update(event):
    module.char = {'size': 1, 'fmt': 'c'}
    module.ulong = {'size': 4, 'fmt': 'L'}
    module.long = {'size': 4, 'fmt': 'l'}
    module.uchar = {'size': 1, 'fmt': 's'}
    module.ushort = {'size': 2, 'fmt': 'H'}
    module.uint = {'size': 4, 'fmt': 'I'}
    # module.void = lookup_types('void', '()')
    module.uint8 = module.uchar
    module.uint16 = module.ushort
    module.uint32 = module.uint
    module.uint64 = {'size': 8, 'fmt': 'Q'}

    module.int8 = module.char
    module.int16 = {'size': 2, 'fmt': 'h'}
    module.int32 = {'size': 4, 'fmt': 'i'}
    module.int64 = {'size': 4, 'fmt': 'l'}

    module.ssize_t = module.long
    module.size_t = module.ulong
    module.ptrsize = 4


# Call it once so we load all of the types
update(None)
