import cmd
import re
import binascii


def default_prompt(x):
    return '(gdbu) '


class CoreShell(cmd.Cmd):
    intro = ''
    prompt = default_prompt

    def __init__(self):
        self.register_command('quit', aliases=['q'], do_xxx=self.do_quit)
        super(CoreShell, self).__init__()

    def register_command(self, name, aliases=[], do_xxx=None, help_xxx=None, complete_xxx=None):
        for cmd_name in aliases + [name]:
            setattr(self, 'do_%s' % cmd_name, do_xxx)
            if help_xxx is not None:
                setattr(self, 'help_%s' % cmd_name, help_xxx)
            if complete_xxx is not None:
                setattr(self, 'complete_%s' % cmd_name, complete_xxx)

    def parse_args(self, arg_line, **kwargs):
        arg = re.findall('[\"\'].*?[\"\']|[^ ]+', arg_line)
        if len(arg) != len(kwargs):
            return None
        result = {}
        for k, v in zip(kwargs, arg):
            if kwargs[k] == str:
                result[k] = v
            elif kwargs[k] == int:
                # result[k] = ugdb.parse_and_eval(v)
                result[k] = v
            elif kwargs[k] == bytes:
                if '\\x' in v:
                    result[k] = binascii.unhexlify(v.replace('\\x', ''))
                else:
                    result[k] = binascii.unhexlify(v)
        return result

    def do_quit(self, arg):
        return True

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.
        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        try:
                            line = input(self.prompt())
                        except EOFError:
                            line = 'quit'
                        except KeyboardInterrupt:
                            line = 'Quit'
                    else:
                        self.stdout.write(self.prompt())
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass
