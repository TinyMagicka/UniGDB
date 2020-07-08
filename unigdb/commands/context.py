import sys
import os
import re
import argparse
import cmd2

import unigdb.config
import unigdb.commands
from unigdb.commands import GenericCommand
import unigdb.commands.registers
from unigdb.color import Color
from unigdb.color import message
import unigdb.proc
import unigdb.ui
import unigdb.regs
import unigdb.hexdump
import unigdb.chain
import unigdb.disassemble as disass


context_hidden = unigdb.config.set('context.context_hidden', False, 'Hide context messages')
config_arrow_right = unigdb.config.set('theme.chain_arrow_right', '—▸', 'right arrow of chain formatting')


def clear_screen():
    """
    Clear the screen by moving the cursor to top-left corner and
    clear the content
    """
    sys.stdout.write('\x1b[H\x1b[J')


@unigdb.commands.register_command
class ContextCommand(GenericCommand):
    """Disp+lays a comprehensive and modular summary of runtime context. Unless setting `enable` is
    set to False, this command will be spawned automatically every time GDB hits a breakpoint, a
    watchpoint, or any kind of interrupt. By default, it will show panes that contain the register
    states, the stack, and the disassembly code around $pc."""

    _cmdline_ = "context"
    _aliases_ = ["ctx", ]

    old_registers = {}

    def __init__(self, cls):
        super(ContextCommand, self).__init__(cls)
        self.add_setting("enable", True, "Enable/disable printing the context when breaking")
        self.add_setting("show_stack_raw", False, "Show the stack pane as raw hexdump (no dereference)")
        self.add_setting("show_registers_raw", False, "Show the registers pane with raw values (no dereference)")
        self.add_setting("peek_calls", True, "Peek into calls")
        self.add_setting("peek_ret", True, "Peek at return address")
        self.add_setting("nb_lines_stack", 8, "Number of line in the stack pane")
        self.add_setting("grow_stack_down", False, "Order of stack downward starts at largest down to stack pointer")
        self.add_setting("nb_lines_backtrace", 10, "Number of line in the backtrace pane")
        self.add_setting("nb_lines_threads", -1, "Number of line in the threads pane")
        self.add_setting("nb_lines_code", 6, "Number of instruction after $pc")
        self.add_setting("nb_lines_code_prev", 3, "Number of instruction before $pc")
        self.add_setting("ignore_registers", "", "Space-separated list of registers not to display (e.g. '$cs $ds $gs')")
        self.add_setting("clear_screen", False, "Clear the screen before printing the context")
        self.add_setting("layout", "legend regs code stack args memory", "Change the order/presence of the context sections")
        self.add_setting("redirect", "", "Redirect the context information to another TTY")

        self.layout_mapping = {
            "legend": self.show_legend,
            "regs": self.context_regs,
            "stack": self.context_stack,
            "code": self.context_code,
            "args": self.context_args,
            "memory": self.context_memory,
        }
        return None

    def post_load(self):
        unigdb.events.cont(self.update_registers)
        return None

    def show_legend(self):
        if unigdb.config.get("self.disable_colors") is not True:
            str_color = unigdb.config.get("theme.dereference_string")
            code_addr_color = unigdb.config.get("theme.address_code")
            stack_addr_color = unigdb.config.get("theme.address_stack")
            heap_addr_color = unigdb.config.get("theme.address_heap")
            changed_register_color = unigdb.config.get("theme.registers_value_changed")

            print("[ Legend: {} | {} | {} | {} | {} ]".format(
                Color.colorify("Modified register", changed_register_color),
                Color.colorify("Code", code_addr_color),
                Color.colorify("Heap", heap_addr_color),
                Color.colorify("Stack", stack_addr_color),
                Color.colorify("String", str_color)
            ))
        return None

    context_parser = argparse.ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    context_parser.add_argument('subcommand', nargs='*', default=['legend', 'regs', 'code'])

    @unigdb.proc.OnlyWhenRunning
    @cmd2.with_argparser(context_parser)
    def do_context(self, args: argparse.Namespace):
        if not self.get_setting("enable") or context_hidden:
            return None

        if len(args.subcommand) > 0:
            current_layout = args.subcommand
        else:
            current_layout = self.get_setting("layout").strip().split()

        if not current_layout:
            return None

        self.tty_rows, self.tty_columns = unigdb.ui.get_window_size()

        redirect = self.get_setting("redirect")
        if redirect and os.access(redirect, os.W_OK):
            unigdb.ui.enable_redirect_output(to_file=redirect)

        if self.get_setting("clear_screen") and len(args.subcommand) == 0:
            clear_screen(redirect)

        for section in current_layout:
            if section[0] == "-":
                continue

            try:
                self.layout_mapping[section]()
            except Exception as e:
                # a MemoryError will happen when $pc is corrupted (invalid address)
                message.error(str(e))

        self.context_title("")

        if redirect and os.access(redirect, os.W_OK):
            unigdb.ui.disable_redirect_output()
        return None

    def context_title(self, m):
        line_color = unigdb.config.get("theme.context_title_line")
        msg_color = unigdb.config.get("theme.context_title_message")

        if not m:
            print(Color.colorify(unigdb.config.HORIZONTAL_LINE * self.tty_columns, line_color))
            return None

        trail_len = len(m) + 6
        title = ""
        title += Color.colorify(
            "{:{padd}<{width}} ".format(
                "",
                width=max(self.tty_columns - trail_len, 0),
                padd=unigdb.config.HORIZONTAL_LINE
            ),
            line_color
        )
        title += Color.colorify(m, msg_color)
        title += Color.colorify(" {:{padd}<4}".format("", padd=unigdb.config.HORIZONTAL_LINE),
                                line_color)
        print(title)
        return None

    def context_regs(self):
        self.context_title("registers")
        ignored_registers = set(self.get_setting("ignore_registers").split())

        if self.get_setting("show_registers_raw") is True:
            regs = set(unigdb.arch.CURRENT_ARCH.all_registers)
            printable_registers = " ".join(list(regs - ignored_registers))
            self.cls.onecmd_plus_hooks("registers {}".format(printable_registers))
            return None

        unigdb.commands.registers.print_registers(
            registers=unigdb.arch.CURRENT_ARCH.all_registers,
            old_registers=self.old_registers,
            ignored_registers=ignored_registers,
            flags=unigdb.arch.CURRENT_ARCH.flags_table
        )
        return None

    def context_stack(self):
        self.context_title("stack")

        show_raw = self.get_setting("show_stack_raw")
        nb_lines = self.get_setting("nb_lines_stack")

        try:
            sp = int(unigdb.arch.CURRENT_ARCH.sp)
            if show_raw is True:
                mem = unigdb.memory.read(sp, 0x10 * nb_lines)
                for _, line in enumerate(unigdb.hexdump.hexdump(mem, address=sp)):
                    print(line)
            else:
                for offset in range(nb_lines):
                    print(unigdb.chain.format(sp + (offset * unigdb.arch.ptrsize)))
                # gdb.execute("dereference {:#x} l{:d}".format(sp, nb_lines))
        except Exception:
            message.error("Cannot read memory from $SP (corrupted stack pointer?)")

        return None

    def context_code(self):
        nb_insn = self.get_setting("nb_lines_code")
        nb_insn_prev = self.get_setting("nb_lines_code_prev")
        cur_insn_color = unigdb.config.get("theme.disassemble_current_instruction")
        pc = int(unigdb.arch.CURRENT_ARCH.pc)

        # frame = gdb.selected_frame()
        arch_name = "{}:{}".format(unigdb.arch.CURRENT_ARCH.arch.lower(), unigdb.arch.CURRENT_ARCH.mode)

        self.context_title("code:{}".format(arch_name))

        try:
            instruction_iterator = disass.capstone_disassemble
            # instruction_iterator = disass.ida_disassemble if use_ida else instruction_iterator
            for insn in instruction_iterator(pc, nb_insn, nb_prev=nb_insn_prev):
                line = []
                is_taken = False
                target = None
                text = str(insn)

                if insn.address < pc:
                    line += Color.grayify("   {}".format(text))
                elif insn.address == pc:
                    line += Color.colorify("{:s}{:s}".format(config_arrow_right.rjust(3), text), cur_insn_color)

                    if unigdb.arch.CURRENT_ARCH.is_conditional_branch(insn):
                        is_taken, reason = unigdb.arch.CURRENT_ARCH.is_branch_taken(insn)
                        if is_taken:
                            target = insn.operands[-1].split()[0]
                            reason = "[Reason: {:s}]".format(reason) if reason else ""
                            line += Color.colorify("\tTAKEN {:s}".format(reason), "bold green")
                        else:
                            reason = "[Reason: !({:s})]".format(reason) if reason else ""
                            line += Color.colorify("\tNOT taken {:s}".format(reason), "bold red")
                    elif unigdb.arch.CURRENT_ARCH.is_call(insn) and self.get_setting("peek_calls") is True:
                        target = insn.operands[-1].split()[0]
                    elif unigdb.arch.CURRENT_ARCH.is_ret(insn) and self.get_setting("peek_ret") is True:
                        target = int(unigdb.arch.CURRENT_ARCH.get_ra(insn))
                else:
                    line += "   {}".format(text)

                print("".join(line))
                if target:
                    try:
                        target = int(target, 0)
                    except TypeError:  # Already an int
                        pass
                    except ValueError:
                        # If the operand isn't an address right now we can't parse it
                        continue
                    for i, tinsn in enumerate(instruction_iterator(target, nb_insn)):
                        text = "   {}  {}".format(unigdb.config.DOWN_ARROW if i == 0 else " ", str(tinsn))
                        print(text)
                    break
        # except Exception as e:
            # message.error("Cannot disassemble from $PC: %s" % e)
        except Exception:
            import traceback
            print(traceback.format_exc())
        return None

    def context_args(self):
        insn = disass.get_current_instruction(int(unigdb.arch.CURRENT_ARCH.pc))
        if not unigdb.arch.CURRENT_ARCH.is_call(insn):
            return None

        self.size2type = {
            1: "BYTE",
            2: "WORD",
            4: "DWORD",
            8: "QWORD",
        }

        if insn.operands[-1].startswith(self.size2type[unigdb.arch.CURRENT_ARCH.ptrsize] + " PTR"):
            target = "*" + insn.operands[-1].split()[-1]
        elif "$" + insn.operands[0] in unigdb.arch.CURRENT_ARCH.all_registers:
            target = "*{:#x}".format(int(unigdb.regs.get_register("$" + insn.operands[0])))
        else:
            # is there a symbol?
            ops = " ".join(insn.operands)
            if "<" in ops and ">" in ops:
                # extract it
                target = re.sub(r".*<([^\(> ]*).*", r"\1", ops)
            else:
                # it's an address, just use as is
                target = re.sub(r".*(0x[a-fA-F0-9]*).*", r"\1", ops)

        self.print_guessed_arguments(target)
        return None

    def print_guessed_arguments(self, function_name):
        """When no symbol, read the current basic block and look for "interesting" instructions."""

        def __get_current_block_start_address():
            pc = int(unigdb.arch.CURRENT_ARCH.pc)
            try:
                block_start = gdb.block_for_pc(pc).start
            except RuntimeError:
                # if stripped, let's roll back 5 instructions
                block_start = disass.gdb_get_nth_previous_instruction_address(pc, 5)
            return block_start

        parameter_set = set()
        pc = int(unigdb.arch.CURRENT_ARCH.pc)
        block_start = __get_current_block_start_address()
        instruction_iterator = disass.capstone_disassemble
        function_parameters = unigdb.arch.CURRENT_ARCH.function_parameters
        arg_key_color = unigdb.config.get("theme.registers_register_name")

        insn_count = (pc - block_start) // unigdb.arch.CURRENT_ARCH.instruction_length
        if unigdb.arch.current == 'mips':
            insn_count += 1  # for branch delay slot
        for insn in instruction_iterator(block_start, insn_count):
            if not insn.operands:
                continue
            if unigdb.arch.current == 'i386':
                if insn.mnemonic == "push":
                    parameter_set.add(insn.operands[0])
            else:
                op = "$" + insn.operands[0]
                if op in function_parameters:
                    parameter_set.add(op)
                if unigdb.arch.current == 'x86-64':
                    # also consider extended registers
                    extended_registers = {"$rdi": ["$edi", "$di"],
                                          "$rsi": ["$esi", "$si"],
                                          "$rdx": ["$edx", "$dx"],
                                          "$rcx": ["$ecx", "$cx"],
                                          }
                    for exreg in extended_registers:
                        if op in extended_registers[exreg]:
                            parameter_set.add(exreg)
        # cicle end
        if unigdb.arch.current == 'i386':
            nb_argument = len(parameter_set)
        else:
            nb_argument = 0
            for p in parameter_set:
                nb_argument = max(nb_argument, function_parameters.index(p) + 1)

        args = []
        for i in range(nb_argument):
            _key, _value = unigdb.arch.CURRENT_ARCH.get_ith_parameter(i)
            _value = unigdb.chain.format(int(_value))
            args.append("{} = {}".format(Color.colorify(_key, arg_key_color), _value))

        self.context_title("arguments (guessed)")
        print("{} (".format(function_name))
        if args:
            print("   " + ",\n   ".join(args))
        print(")")
        return None

    def context_memory(self):
        global __watches__
        for address, opt in sorted(__watches__.items()):
            self.context_title("memory:{:#x}".format(address))
            self.cls.onecmd_plus_hooks("hexdump {fmt:s} {address:d} {size:d}".format(
                address=address,
                size=opt[0],
                fmt=opt[1]
            ))

    @classmethod
    def update_registers(cls, event):
        for reg in unigdb.arch.CURRENT_ARCH.all_registers:
            try:
                cls.old_registers[reg] = unigdb.regs.get_register(reg)
            except Exception:
                cls.old_registers[reg] = 0
        return None
