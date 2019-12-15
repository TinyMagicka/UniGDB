import cmd2
import argparse

import unigdb.commands
import unigdb.prompt
import unigdb.regs


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
        self.settable.update({'arch': 'Target architecrute'})

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
        for name in [cls._cmdline_] + cls._aliases_:
            setattr(CoreShell, 'do_%s' % name, getattr(cls, 'do_%s' % name))
            setattr(CoreShell, 'help_%s' % name, cls.help_xxx)
            if hasattr(cls, 'complete_%s' % name):
                setattr(CoreShell, 'complete_%s' % name, getattr(cls, 'complete_%s' % name))

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
    set_parser.add_argument('type', nargs=argparse.OPTIONAL, help='type of value')
    set_parser.add_argument('param', help='parameter to set or view',
                            choices_method=cmd2.Cmd._get_settable_completion_items, descriptive_header='Description')
    set_parser.add_argument('value', nargs='+', help='the new value for settable')

    @cmd2.with_argparser(set_parser)
    def do_set(self, args: argparse.Namespace) -> None:
        """Set a settable parameter or show current settings of parameters"""
        param = cmd2.utils.norm_fold(args.param.strip())
        # Check if param points to just one settable
        print(args)
        if param not in self.settable:
            hits = [p for p in self.settable if p.startswith(param)]
            self.pwarning('Ambiguous set command "{}": {}'.format(param, ', '.join(hits)))

        if args.type is None:
            args.type = '{int}'

        if param == 'reg':
            reg, value = args.value
            unigdb.regs.set_register(reg, int(value))
        elif param.startswith('$'):
            value = int(args.value[0])
            unigdb.regs.set_register(param, value)
        elif param.startswith('0x'):
            try:
                address = int(param, 16)
            except ValueError:
                self.perror('Invalid number: %s' % param)
                return None
            if args.type == '{int}':
                unigdb.arch.UC.mem_write()
