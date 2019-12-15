import argparse
import cmd2

import unigdb.commands
from unigdb.commands import GenericCommand
from unigdb.color import Color
from unigdb.color import message


@unigdb.commands.register_priority_command
class GefThemeCommand(GenericCommand):
    """Customize UniGDB appearance."""
    _cmdline_ = "theme"

    def __init__(self, cls):
        super(GefThemeCommand, self).__init__(cls)
        self.add_setting("context_title_line", "gray", "Color of the borders in context window")
        self.add_setting("context_title_message", "cyan", "Color of the title in context window")
        self.add_setting("default_title_line", "gray", "Default color of borders")
        self.add_setting("default_title_message", "cyan", "Default color of title")
        self.add_setting("table_heading", "blue", "Color of the column headings to tables (e.g. vmmap)")
        self.add_setting("disassemble_current_instruction", "green", "Color to use to highlight the current $pc when disassembling")
        self.add_setting("dereference_string", "yellow", "Color of dereferenced string")
        self.add_setting("dereference_code", "gray", "Color of dereferenced code")
        self.add_setting("dereference_base_address", "cyan", "Color of dereferenced address")
        self.add_setting("dereference_register_value", "bold blue", "Color of dereferenced register")
        self.add_setting("registers_register_name", "blue", "Color of the register name in the register window")
        self.add_setting("registers_value_changed", "bold red", "Color of the changed register in the register window")
        self.add_setting("address_stack", "pink", "Color to use when a stack address is found")
        self.add_setting("address_heap", "green", "Color to use when a heap address is found")
        self.add_setting("address_code", "red", "Color to use when a code address is found")
        self.add_setting("source_current_line", "green", "Color to use for the current code line in the source window")
        self.add_setting('chain_arrow_left', '◂—', 'left arrow of chain formatting')
        self.add_setting('chain_arrow_right', '—▸', 'right arrow of chain formatting')
        return None

    theme_parser = argparse.ArgumentParser(description=Color.yellowify(__doc__), add_help=False)
    theme_parser.add_argument('key', nargs=argparse.OPTIONAL, help='Theme param name')
    theme_parser.add_argument('value', nargs=argparse.OPTIONAL, help='Theme param value')

    @cmd2.with_argparser(theme_parser)
    def do_theme(self, args: argparse.Namespace):
        if not args.key:
            for setting in sorted(self.settings):
                value = self.get_setting(setting)
                value = Color.colorify(value, value)
                print("{:40s}: {:s}".format(setting, value))
            return None

        setting = args.key
        if not self.has_setting(setting):
            message.error("Invalid key")
            return None

        if not args.value:
            value = self.get_setting(setting)
            value = Color.colorify(value, value)
            print("{:40s}: {:s}".format(setting, value))
            return None

        val = [x for x in args.value.split() if x in Color.colors]
        self.add_setting(setting, " ".join(val))
        return None
