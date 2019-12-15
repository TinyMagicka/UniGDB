"""
Reading, writing, and describing memory.
"""
import os
import struct
import re

# import unigdb.events
# import unigdb.proc
import unigdb.typeinfo
import unigdb.arch
from unigdb.color import message

PAGE_SIZE = 0x1000
PAGE_MASK = ~(PAGE_SIZE - 1)
MMAP_MIN_ADDR = 0x8000


def number_matcher(value):
    return re.match(r'^\d+$|^0x[0-9A-Fa-f]+$', value)


def unpack(fmt, data):
    e = '<' if unigdb.arch.endian == 'little' else '>'
    return struct.unpack(e + fmt, data)[0]


def pack(fmt, data):
    e = '<' if unigdb.arch.endian == 'little' else '>'
    return struct.pack(e + fmt, data)


def read(addr, count):
    """read(addr, count, partial=False) -> bytearray

    Read memory from the program being debugged.

    Arguments:
        addr(int): Address to read
        count(int): Number of bytes to read
    Returns:
        :class:`bytearray`: The memory at the specified address,
        or ``None``.
    """
    result = b''
    count = max(int(count), 0)

    result = unigdb.arch.UC.mem_read(addr, count)
    return bytearray(result)


def readtype(gdb_type, addr):
    """readtype(gdb_type, addr) -> int

    Reads an integer-type (e.g. ``uint64``) and returns a Python
    native integer representation of the same.

    Arguments:
        gdb_type(dict): GDB type to read
        addr(int): Address at which the value to be read resides

    Returns:
        :class:`int`
    """
    return unpack(gdb_type['fmt'], read(addr, gdb_type['size']))


def write(addr, data):
    """write(addr, data)

    Writes data into the memory of the process being debugged.

    Arguments:
        addr(int): Address to write
        data(str,bytes,bytearray): Data to write
    """
    if isinstance(data, str):
        data = data.encode()
    try:
        unigdb.arch.UC.mem_write(addr, data)
    except AttributeError:
        message.error('{!} Error => Unicorn engine not initialized')


def write_int(addr, data):
    if isinstance(data, int):
        value = data
    elif number_matcher(data):
        value = eval(data)
    else:
        message.error('{!} Error => Invalid number: %s' % data)
        return None
    write(addr, pack('I', value))


def write_short(addr, data):
    if isinstance(data, int):
        value = data
    elif number_matcher(data):
        value = eval(data)
    else:
        message.error('{!} Error => Invalid number: %s' % data)
        return None
    write(addr, pack('H', value))


def write_byte(addr, data):
    if isinstance(data, int):
        value = data
    elif number_matcher(data):
        value = eval(data)
    else:
        message.error('{!} Error => Invalid number: %s' % data)
        return None
    write(addr, pack('B', value))


def peek(address):
    """peek(address) -> str

    Read one byte from the specified address.

    Arguments:
        address(int): Address to read

    Returns:
        :class:`str`: A single byte of data, or ``None`` if the
        address cannot be read.
    """
    try:
        return read(address, 1)
    except:
        pass
    return None


def poke(address):
    """poke(address)

    Checks whether an address is writable.

    Arguments:
        address(int): Address to check

    Returns:
        :class:`bool`: Whether the address is writable.
    """
    c = peek(address)
    if c is None:
        return False
    try:
        write(address, c)
    except:
        return False
    return True


def string(addr, max=4096):
    """Reads a null-terminated string from memory.

    Arguments:
        addr(int): Address to read from
        max(int): Maximum string length (default 4096)

    Returns:
        An empty bytearray, or a NULL-terminated bytearray.
    """
    data = bytearray(read(addr, max, partial=True))

    if b'\x00' in data:
        return data.split(b'\x00')[0]

    return bytearray()


def byte(addr):
    """byte(addr) -> int

    Read one byte at the specified address
    """
    return readtype(unigdb.typeinfo.uchar, addr)


def uchar(addr):
    """uchar(addr) -> int

    Read one ``unsigned char`` at the specified address.
    """
    return readtype(unigdb.typeinfo.uchar, addr)


def ushort(addr):
    """ushort(addr) -> int

    Read one ``unisgned short`` at the specified address.
    """
    return readtype(unigdb.typeinfo.ushort, addr)


def uint(addr):
    """uint(addr) -> int

    Read one ``unsigned int`` at the specified address.
    """
    return readtype(unigdb.typeinfo.uint, addr)


def u8(addr):
    """u8(addr) -> int

    Read one ``uint8_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.uint8, addr)


def u16(addr):
    """u16(addr) -> int

    Read one ``uint16_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.uint16, addr)


def u32(addr):
    """u32(addr) -> int

    Read one ``uint32_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.uint32, addr)


def u64(addr):
    """u64(addr) -> int

    Read one ``uint64_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.uint64, addr)


def u(addr, size=None):
    """u(addr, size=None) -> int

    Read one ``unsigned`` integer from the specified address,
    with the bit-width specified by ``size``, which defaults
    to the pointer width.
    """
    if size is None:
        size = unigdb.arch.ptrsize * 8
    return {
        8: u8,
        16: u16,
        32: u32,
        64: u64
    }[size](addr)


def s8(addr):
    """s8(addr) -> int

    Read one ``int8_t`` from the specified address
    """
    return readtype(unigdb.typeinfo.int8, addr)


def s16(addr):
    """s16(addr) -> int

    Read one ``int16_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.int16, addr)


def s32(addr):
    """s32(addr) -> int

    Read one ``int32_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.int32, addr)


def s64(addr):
    """s64(addr) -> int

    Read one ``int64_t`` from the specified address.
    """
    return readtype(unigdb.typeinfo.int64, addr)


def round_down(address, align):
    """round_down(address, align) -> int

    Round down ``address`` to the nearest increment of ``align``.
    """
    return address & ~(align - 1)


def round_up(address, align):
    """round_up(address, align) -> int

    Round up ``address`` to the nearest increment of ``align``.
    """
    return (address + (align - 1)) & (~(align - 1))


align_down = round_down
align_up = round_up


def page_align(address):
    """page_align(address) -> int

    Round down ``address`` to the nearest page boundary.
    """
    return round_down(address, PAGE_SIZE)


def page_size_align(address):
    return round_up(address, PAGE_SIZE)


def page_offset(address):
    return (address & (PAGE_SIZE - 1))


assert round_down(0xdeadbeef, 0x1000) == 0xdeadb000
assert round_up(0xdeadbeef, 0x1000) == 0xdeadc000


def find_upper_boundary(addr, max_pages=1024):
    """find_upper_boundary(addr, max_pages=1024) -> int

    Brute-force search the upper boundary of a memory mapping,
    by reading the first byte of each page, until an unmapped
    page is found.
    """
    addr = unigdb.memory.page_align(int(addr))
    try:
        for i in range(max_pages):
            unigdb.memory.read(addr, 1)
            # import sys
            # sys.stdout.write(hex(addr) + '\n')
            addr += unigdb.memory.PAGE_SIZE
            if addr > unigdb.arch.ptrmask:
                break
    except gdb.MemoryError:
        pass
    return addr


def find_lower_boundary(addr, max_pages=1024):
    """find_lower_boundary(addr, max_pages=1024) -> int

    Brute-force search the lower boundary of a memory mapping,
    by reading the first byte of each page, until an unmapped
    page is found.
    """
    addr = unigdb.memory.page_align(int(addr))
    try:
        for i in range(max_pages):
            unigdb.memory.read(addr, 1)
            addr -= unigdb.memory.PAGE_SIZE
            if addr < 0:
                break
    except gdb.MemoryError:
        addr += unigdb.memory.PAGE_SIZE
    return addr


class Page(object):
    """
    Represents the address space and page permissions of at least
    one page of memory.
    """
    vaddr = 0  # : Starting virtual address
    memsz = 0  # : Size of the address space, in bytes
    flags = 0  # : Flags set by the ELF file, see PF_X, PF_R, PF_W
    offset = 0  # : Offset into the original ELF file that the data is loaded from
    objfile = ''  # : Path to the ELF on disk

    def __init__(self, start, size, flags, offset, objfile=''):
        self.vaddr = start
        self.memsz = size
        self.flags = flags
        self.offset = offset
        self.objfile = objfile

        # if self.rwx:
        # self.flags = self.flags ^ 1

    @property
    def start(self):
        """
        Mapping start address.
        """
        return self.vaddr

    @property
    def end(self):
        """
        Address beyond mapping. So the last effective address is self.end-1
        It is the same as displayed in /proc/<pid>/maps
        """
        return self.vaddr + self.memsz

    @property
    def is_stack(self):
        return self.objfile == '[stack]'

    @property
    def is_memory_mapped_file(self):
        return len(self.objfile) > 0 and self.objfile[0] != '['

    @property
    def read(self):
        return bool(self.flags & 4)

    @property
    def write(self):
        return bool(self.flags & 2)

    @property
    def execute(self):
        return bool(self.flags & 1)

    @property
    def rw(self):
        return self.read and self.write

    @property
    def rwx(self):
        return self.read and self.write and self.execute

    @property
    def permstr(self):
        flags = self.flags
        return ''.join(['r' if flags & os.R_OK else '-',
                        'w' if flags & os.W_OK else '-',
                        'x' if flags & os.X_OK else '-',
                        'p'])

    def __str__(self):
        width = 2 + 2 * unigdb.typeinfo.ptrsize
        fmt_string = "%#{}x %#{}x %s %8x %-6x %s"
        fmt_string = fmt_string.format(width, width)
        return fmt_string % (self.vaddr,
                             self.vaddr + self.memsz,
                             self.permstr,
                             self.memsz,
                             self.offset,
                             self.objfile or '')

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.__str__())

    def __contains__(self, addr):
        return self.start <= addr < self.end

    def __eq__(self, other):
        return self.vaddr == getattr(other, 'vaddr', other)

    def __lt__(self, other):
        return self.vaddr < getattr(other, 'vaddr', other)

    def __hash__(self):
        return hash((self.vaddr, self.memsz, self.flags, self.offset, self.objfile))


# @unigdb.events.start
def update_min_addr():
    global MMAP_MIN_ADDR
    if unigdb.qemu.is_qemu_kernel():
        MMAP_MIN_ADDR = 0
