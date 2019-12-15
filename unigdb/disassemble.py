import sys
import unigdb.arch
import unigdb.memory


class Instruction:
    """unigdb representation of a CPU instruction."""

    def __init__(self, address, location, mnemo, operands, comment=''):
        self.address = address
        self.location = location
        self.mnemonic = mnemo
        self.operands = operands
        self.comment = ' # %s' % comment if comment else ''

    def __str__(self):
        return "{:#10x} {:16} {:6} {:s}{:s}".format(
            self.address,
            self.location,
            self.mnemonic,
            ", ".join(self.operands),
            self.comment
        )

    def is_valid(self):
        return "(bad)" not in self.mnemonic


# def gdb_disassemble(start_pc, **kwargs):
#     """Disassemble instructions from `start_pc` (Integer). Accepts the following named parameters:
#     - `end_pc` (Integer) only instructions whose start address fall in the interval from start_pc to end_pc are returned.
#     - `count` (Integer) list at most this many disassembled instructions
#     If `end_pc` and `count` are not provided, the function will behave as if `count=1`.
#     Return an iterator of Instruction objects
#     """
#     frame = gdb.selected_frame()
#     arch = frame.architecture()

#     for insn in arch.disassemble(start_pc, **kwargs):
#         address = insn["addr"]
#         asm = insn["asm"].rstrip().split(None, 1)
#         if len(asm) > 1:
#             mnemo, operands = asm
#             operands = operands.split(",")
#         else:
#             mnemo, operands = asm[0], []

#         loc = gdb_get_location_from_symbol(address)
#         location = "<{}+{}>".format(*loc) if loc else ""

#         yield Instruction(address, location, mnemo, operands)


def gdb_get_nth_next_instruction_address(addr, n):
    """Return the address (Integer) of the `n`-th instruction after `addr`."""
    # fixed-length ABI
    if unigdb.arch.CURRENT_ARCH.instruction_length:
        return addr + n * unigdb.arch.CURRENT_ARCH.instruction_length
    # variable-length ABI
    # insn = list(gdb_disassemble(addr, count=n))[-1]
    # return insn.address


def gdb_get_nth_previous_instruction_address(addr, n):
    """Return the address (Integer) of the `n`-th instruction before `addr`."""
    # fixed-length ABI
    if unigdb.arch.CURRENT_ARCH.instruction_length:
        return addr - n * unigdb.arch.CURRENT_ARCH.instruction_length
    # variable-length ABI
    # cur_insn_addr = get_current_instruction(addr).address

    # # we try to find a good set of previous instructions by "guessing" disassembling backwards
    # # the 15 comes from the longest instruction valid size
    # for i in range(15 * n, 0, -1):
    #     try:
    #         insns = list(gdb_disassemble(addr - i, end_pc=cur_insn_addr, count=n + 1))
    #     except Exception:
    #         # this is because we can hit an unmapped page trying to read backward
    #         break
    #     # 1. check that the disassembled instructions list size is correct
    #     if len(insns) != n + 1:  # we expect the current instruction plus the n before it
    #         continue
    #     # 2. check all instructions are valid
    #     for insn in insns:
    #         if not insn.is_valid():
    #             continue
    #     # 3. if cur_insn is at the end of the set
    #     if insns[-1].address == cur_insn_addr:
    #         return insns[0].address

    # return None


def get_instruction_n(addr, n):
    """Return the `n`-th instruction after `addr` as an Instruction object."""
    return list(capstone_disassemble(addr, count=n + 1))[n]


# def gef_get_instruction_at(addr):
#     """Return the full Instruction found at the specified address."""
#     insn = next(gef_disassemble(addr, 1))
#     return insn


def get_current_instruction(addr):
    """Return the current instruction as an Instruction object."""
    return get_instruction_n(addr, 0)


def get_next_instruction(addr):
    """Return the next instruction as an Instruction object."""
    return get_instruction_n(addr, 1)


# def gef_disassemble(addr, nb_insn, nb_prev=0):
#     """Disassemble `nb_insn` instructions after `addr` and `nb_prev` before `addr`.
#     Return an iterator of Instruction objects."""
#     count = nb_insn + 1 if nb_insn & 1 else nb_insn

#     if nb_prev:
#         start_addr = gdb_get_nth_previous_instruction_address(addr, nb_prev)
#         if start_addr:
#             for insn in gdb_disassemble(start_addr, count=nb_prev):
#                 if insn.address == addr:
#                     break
#                 yield insn

#     for insn in gdb_disassemble(addr, count=count):
#         yield insn


def capstone_disassemble(location, count, **kwargs):
    """Disassemble `count` instructions after `addr` and `nb_prev` before
    `addr` using the Capstone-Engine disassembler, if available.
    Return an iterator of Instruction objects."""

    def cs_insn_to_gef_insn(cs_insn):
        sym_info = None
        loc = "<{}+{}>".format(*sym_info) if sym_info else ""
        ops = [] + cs_insn.op_str.split(", ")
        return Instruction(cs_insn.address, loc, cs_insn.mnemonic, ops)

    capstone = sys.modules["capstone"]
    arch = getattr(capstone, 'CS_ARCH_%s' % unigdb.arch.CURRENT_ARCH.arch)
    mode = getattr(capstone, 'CS_MODE_%s' % unigdb.arch.CURRENT_ARCH.mode)
    mode |= getattr(capstone, 'CS_MODE_%s_ENDIAN' % unigdb.arch.endian.upper())
    cs = capstone.Cs(arch, mode)
    cs.detail = True

    page_start = unigdb.memory.page_size_align(location)
    offset = location - page_start
    pc = unigdb.arch.CURRENT_ARCH.pc

    skip = int(kwargs.get("skip", 0))
    nb_prev = int(kwargs.get("nb_prev", 0))
    if nb_prev > 0:
        location = gdb_get_nth_previous_instruction_address(pc, nb_prev)
        count += nb_prev

    code = kwargs.get("code", unigdb.memory.read(location, unigdb.memory.PAGE_SIZE - offset - 1))
    code = bytes(code)

    for insn in cs.disasm(code, location):
        if skip:
            skip -= 1
            continue
        count -= 1
        yield cs_insn_to_gef_insn(insn)
        if count == 0:
            break
    return
