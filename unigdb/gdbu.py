import cmd2
import unigdb.commands
import unigdb.prompt


class CoreShell(cmd2.Cmd):
    intro = ''
    prompt = '(gdbu) '

    def __init__(self):
        self.locals_in_py = True
        self.default_category = 'UniGDB Built-in Commands'
        for cmdClass in unigdb.commands.__commands__:
            self.register_cmd_class(cmdClass())

        super(CoreShell, self).__init__(
            persistent_history_file='/tmp/.unigdb_history', shortcuts={},
        )
        self.aliases['q'] = 'quit'
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
            setattr(CoreShell, 'do_%s' % name, cls.do_xxx)
            setattr(CoreShell, 'help_%s' % name, cls.help_xxx)
            setattr(CoreShell, 'complete_%s' % name, cls.complete_xxx)

    def do_quit(self, arg):
        return True
