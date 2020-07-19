import argparse
import cmd2

import unigdb.config
import unigdb.commands
from unigdb.commands import GenericCommand
import unigdb.arch
import unigdb.proc
from unigdb.color import message
from unigdb.color import Color


@unigdb.commands.register_command
class DetailRegistersCommand(GenericCommand):
    """Display full details on one, many or all registers value from current architecture."""

    _cmdline_ = "registers"
    _aliases_ = ["regs", ]

    def __init__(self, cls):
        super(DetailRegistersCommand, self).__init__(cls)

    reg_parser = argparse.ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    reg_parser.add_argument('regs', nargs='*', help='Registers for show')

    @unigdb.proc.OnlyWhenInit
    @cmd2.with_argparser(reg_parser)
    def do_registers(self, args: argparse.Namespace):
        if args.regs:
            regs = [reg for reg in unigdb.arch.CURRENT_ARCH.all_registers if reg in args.regs]
            if not regs:
                message.warn("No matching registers found")
        else:
            regs = unigdb.arch.CURRENT_ARCH.all_registers

        print_registers(registers=regs)


def print_registers(registers, ignored_registers=[], old_registers={}, flags=False):
    '''Print dereferenced registers

    Arguments:
        registers(list): List of printed registers
        ignored_registers(list): List of registers witch didn't printed
        old_registers(list): Old registers, needed for check if registers was changed
        flags(bool): Print flags

    Returns:
        A string representing pointers of each address and reference
        REG_NAME: 0x0804a10 —▸ 0x08061000 —▸ AAAA
    '''
    widest = max(map(len, registers))
    changed_color = unigdb.config.get("theme.registers_value_changed")
    regname_color = unigdb.config.get("theme.registers_register_name")
    line = ''
    # Print registers value
    for reg in registers:
        if reg in ignored_registers:
            continue

        try:
            r = unigdb.regs.get_register(reg)
            # if r.type.code == gdb.TYPE_CODE_VOID:
            #     continue
            new_value_type_flag = False
            new_value = int(r) if r >= 0 else unigdb.arch.ptrmask + int(r) + 1
        except Exception:
            # If this exception is triggered, it means that the current register
            # is corrupted. Just use the register "raw" value (not eval-ed)
            new_value = unigdb.regs.get_register(reg)
            new_value_type_flag = False
        except Exception:
            new_value = 0
            new_value_type_flag = False

        old_value = old_registers.get(reg, 0)
        padreg = reg.ljust(widest, " ")
        value = new_value
        if value == old_value:
            line += "{}: ".format(Color.colorify(padreg, regname_color))
        else:
            line += "{}: ".format(Color.colorify(padreg, changed_color))
        if new_value_type_flag:
            line += "{:s} ".format(str(value))
        else:
            line += unigdb.chain.format(value)
        print(line)
        line = ""
    # Print Flags
    if flags and unigdb.arch.CURRENT_ARCH.flags_table:
        print("Flags: {:s}".format(unigdb.arch.CURRENT_ARCH.flag_register_to_human()))
