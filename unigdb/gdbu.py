import cmd2
import argparse
import re
import binascii

import unigdb.commands
import unigdb.prompt
import unigdb.regs
import unigdb.proc
from unigdb.commands.breakpoint import hasBreakpoint, delBreakpoint


class CoreShell(cmd2.Cmd):
    intro = ''
    prompt = '(gdbu) '
    print_table_count = 5

    def __init__(self):
        self.locals_in_py = True
        self.default_category = 'UniGDB Built-in Commands'
        super(CoreShell, self).__init__(
            persistent_history_file='/tmp/.unigdb_history', shortcuts={},
        )
        # load modules
        for cmdClass in unigdb.commands.__commands__:
            self.register_cmd_class(cmdClass(self))

        self.aliases['q'] = 'quit'
        # Set enviroment variables
        self.mapping_size = 2 * 1024 * 1024 * 1024
        self.mapping = 0x100000
        self.settable.update({'arch': 'Target architecrute'})
        self.settable.update({'mapping': 'Memory start map address'})
        self.settable.update({'mapping_size': 'Memory mapping size in bytes'})

        # remove unneeded commands
        del cmd2.Cmd.do_shortcuts
        del cmd2.Cmd.do_macro
        del cmd2.Cmd._macro_create
        del cmd2.Cmd._macro_delete
        del cmd2.Cmd._macro_list
        del cmd2.Cmd.do_edit
        del cmd2.Cmd.do_run_pyscript
        self.async_update_prompt(unigdb.prompt.set_prompt())

    def register_cmd_class(self, cls):
        name = cls._cmdline_
        setattr(CoreShell, 'do_%s' % name, getattr(cls, 'do_%s' % name))
        setattr(CoreShell, 'help_%s' % name, cls.help_xxx)
        if hasattr(cls, 'complete_%s' % name):
            setattr(CoreShell, 'complete_%s' % name, getattr(cls, 'complete_%s' % name))
        # Set aliases
        for item in cls._aliases_:
            self.aliases[item] = name

    def do_quit(self, arg):
        return True

    @property
    def arch(self) -> str:
        """Read-only property needed to support do_set when it reads arch"""
        return unigdb.arch.current + 'el' if unigdb.arch.endian == 'little' else 'eb'

    @arch.setter
    def arch(self, new_val: str) -> str:
        """Setter property needed to support do_set when it updates arch"""
        new_val = new_val.lower()
        arches = ['armel', 'armeb', 'mipsel', 'mipseb']
        if new_val in arches:
            endian = 'little' if new_val.endswith('el') else 'big'
            unigdb.arch.update(new_val[:-2], endian)
        else:
            self.perror('Invalid value: {}'.format(new_val))
            txt = ''
            for i in range(len(arches)):
                txt += arches[i]
                if i != 0 and i % self.print_table_count == 0:
                    txt += '\n'
                else:
                    txt += ', '
            txt = txt.strip(', ')
            self.perror('Valid values: {}'.format(txt))

    set_parser = cmd2.Cmd2ArgumentParser(add_help=False)
    set_parser.add_argument('param', help='parameter to set or view',
                            choices_method=cmd2.Cmd._get_settable_completion_items)
    set_parser.add_argument('value', nargs='+', help='the new value for settable')

    @cmd2.with_argparser(set_parser)
    def do_set(self, args: argparse.Namespace) -> None:
        """Set a settable parameter or show current settings of parameters"""
        param = cmd2.utils.norm_fold(args.param.strip())

        # Set register value
        if param.startswith('$'):
            value = parse_and_eval(args.value[0])
            return unigdb.regs.set_register(param, value)

        # Parse set memory value
        matches = re.match(r'(\{[a-z]+\})?([^a-z].*)', param)
        if matches:
            var_type = matches.group(1)
            address = matches.group(2)
            address = parse_and_eval(address)
            value = args.value[0]
            if var_type == '{str}':
                return unigdb.memory.write(address, value)
            elif var_type == '{hex}':
                return unigdb.memory.write(address, binascii.unhexlify(value))
            value = parse_and_eval(value)
            if var_type == '{int}':
                return unigdb.memory.write_int(address, value)
            elif var_type == '{byte}':
                return unigdb.memory.write_byte(address, value)
            elif var_type == '{word}':
                return unigdb.memory.write_short(address, value)
            else:
                self.perror('Unknown type: %s' % var_type)
            return None

        # Check if param points to just one settable
        if param not in self.settable:
            hits = [p for p in self.settable if p.startswith(param)]
            if hits:
                self.pwarning('Ambiguous set command "{}": {}'.format(param, ', '.join(hits)))
            return None
        else:
            orig_value = getattr(self, param)
            if unigdb.memory.number_matcher(args.value[0]):
                value = int(args.value[0]) if args.value[0].isdigit() else int(args.value[0], 16)
            else:
                value = args.value[0]
            setattr(self, param, cmd2.utils.cast(orig_value, value))

    show_parser = cmd2.Cmd2ArgumentParser(add_help=False)
    show_parser.add_argument('-a', '--all', action='store_true', help='display read-only settings as well')
    show_parser.add_argument('-l', '--long', action='store_true', help='describe function of parameter')
    show_parser.add_argument('param', help='parameter to set or view', nargs=argparse.OPTIONAL,
                             choices_method=cmd2.Cmd._get_settable_completion_items)

    @cmd2.with_argparser(show_parser)
    def do_show(self, args: argparse.Namespace) -> None:
        if not args.param:
            return self._show(args)
        param = cmd2.utils.norm_fold(args.param.strip())
        return self._show(args, param)

    def do_map(self, args):
        unigdb.arch.UC.mem_map(self.mapping, self.mapping_size)

    def hook_code(self, uc, address, size, user_data):
        has_break = hasBreakpoint(address)
        if has_break is not None:
            uc.emu_stop()
            self.onecmd_plus_hooks('ctx ' + unigdb.config.get('context.layout'))
            if has_break is True:
                delBreakpoint(address)

    def hook_block(self, uc, address, size, user_data):
        pass

    def hook_intr(self, uc, except_idx, user_data):
        pass


def parse_and_eval(expression):
    expr = expression.lower()
    # Parse brackets
    # print('start', expr)
    brackets = re.findall(r'\(.*\)', expr[1:-1] if expr[0] == '(' and expr[-1] == ')' else expr)
    for b in brackets:
        result = parse_and_eval(b)
        expr = expr.replace(b, str(result), 1)
    # print('bra', expr)
    # Parse registers
    regs = re.findall(r'\$[\w]+', expr)
    for r in regs:
        reg_value = unigdb.regs.get_register(r)
        # reg_value = arr.get(r)
        if reg_value:
            expr = expr.replace(r, str(reg_value), 1)
        else:
            break
    # print('reg', expr)
    # Parse pointers
    pointers = re.findall(r'\*0x[\da-f]+|\*\d+', expr)
    for p in pointers:
        addr = int(p[1:]) if p[1:].isdigit() else int(p[1:], 16)
        pointer_value = unigdb.memory.uint(addr)
        # pointer_value = arr.get(addr)
        expr = expr.replace(p, str(pointer_value), 1)
    # print('poi', expr)
    try:
        return eval(expr)
    except Exception:
        return expression
