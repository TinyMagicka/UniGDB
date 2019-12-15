import unicorn
import sys

import unigdb.events
import unigdb.typeinfo
import unigdb.regs
import unigdb.proc

current = 'i386'
ptrmask = 0xfffffffff
endian = 'little'
ptrsize = unigdb.typeinfo.ptrsize
fmt = '=I'
native_endian = str(sys.byteorder)
CURRENT_ARCH = None
UC = None


def update(arch, endian):
    m = sys.modules[__name__]
    m.current = arch
    m.ptrsize = unigdb.typeinfo.ptrsize
    m.ptrmask = (1 << 8 * unigdb.typeinfo.ptrsize) - 1

    m.endian = endian

    m.fmt = {
        (4, 'little'): '<I',
        (4, 'big'): '>I',
        (8, 'little'): '<Q',
        (8, 'big'): '>Q',
    }.get((m.ptrsize, m.endian))

    # Work around Python 2.7.6 struct.pack / unicode incompatibility
    # See https://github.com/unigdb/unigdb/pull/336 for more information.
    m.fmt = str(m.fmt)

    # Attempt to detect the qemu-user binary name
    if m.current == 'arm' and m.endian == 'big':
        m.qemu = 'armeb'
    elif m.current == 'mips' and m.endian == 'little':
        m.qemu = 'mipsel'
    else:
        m.qemu = m.current
    set_arch(m.current)


def set_arch(arch=None, default=None):
    """Sets the current architecture."""
    module = sys.modules[__name__]
    if arch:
        try:
            module.CURRENT_ARCH = unigdb.regs.arch_to_regs[arch]()
            uc_arch = getattr(unicorn, 'UC_ARCH_%s' % module.CURRENT_ARCH.arch)
            uc_mode = getattr(unicorn, 'UC_MODE_%s' % module.CURRENT_ARCH.mode)
            if module.endian == 'little':
                uc_mode += unicorn.UC_MODE_LITTLE_ENDIAN
            else:
                uc_mode += unicorn.UC_MODE_BIG_ENDIAN
            module.UC = unicorn.Uc(uc_arch, uc_mode)
            unigdb.proc.init = True
            return module.CURRENT_ARCH
        except KeyError:
            raise OSError("Specified arch {:s} is not supported".format(arch))
    try:
        module.CURRENT_ARCH = unigdb.regs.arch_to_regs[module.current]()
    except KeyError:
        if default:
            try:
                module.CURRENT_ARCH = unigdb.regs.arch_to_regs[default.lower()]()
            except KeyError:
                raise OSError("CPU not supported, neither is default {:s}".format(default))
        else:
            raise OSError("CPU type is currently not supported: {:s}".format(module.current))
    return module.CURRENT_ARCH
