import os
import sys
import tempfile
import configparser
import gdb

import unigdb.config
from unigdb.color import Color
from unigdb.color import message
import unigdb.commands
import unigdb.functions

__aliases__ = []


def execute_gdb_script(commands):
    """Execute the parameter `source` as GDB command. This is done by writing `commands` to
    a temporary file, which is then executed via GDB `source` command. The tempfile is then deleted."""
    fd, fname = tempfile.mkstemp(suffix=".gdb", prefix="unigdb_")
    with os.fdopen(fd, "w") as f:
        f.write(commands)
        f.flush()
    if os.access(fname, os.R_OK):
        gdb.execute("source {:s}".format(fname))
        os.unlink(fname)
    return


class SelfCommand(gdb.Command):
    """UNIGDB main command: view all new commands by typing `self`."""

    _cmdline_ = "self"
    _syntax_ = "{:s} (missing|config|save|restore|set|run)".format(_cmdline_)
    _aliases_ = ['unigdb', ]

    def __init__(self):
        super(SelfCommand, self).__init__(SelfCommand._cmdline_,
                                          gdb.COMMAND_SUPPORT,
                                          gdb.COMPLETE_NONE,
                                          True)
        unigdb.config.set("self.follow_child", True, "Automatically set GDB to follow child when forking")
        unigdb.config.set("self.readline_compat", False, "Workaround for readline SOH/ETX issue (SEGV)")
        unigdb.config.set("self.debug", False, "Enable debug mode for UNIGDB")
        unigdb.config.set("self.autosave_breakpoints_file", "", "Automatically save and restore breakpoints")
        unigdb.config.set("self.extra_plugins_dir", "", "Autoload additional UNIGDB commands from external directory")
        unigdb.config.set("self.disable_color", False, "Disable all colors in UNIGDB")
        self.loaded_commands = []
        self.loaded_functions = []
        self.missing_commands = {}
        return None

    def setup(self):
        self.load(initial=True)
        # loading UNIGDB sub-commands
        self.doc = SelfHelpCommand(self.loaded_commands)
        self.cfg = SelfConfigCommand(self.loaded_command_names)
        SelfSaveCommand()
        SelfRestoreCommand()
        SelfMissingCommand()
        SelfSetCommand()
        SelfRunCommand()

        # load the saved settings
        gdb.execute("self restore")

        # restore the autosave/autoreload breakpoints policy (if any)
        self.__reload_auto_breakpoints()

        # load plugins from `extra_plugins_dir`
        if self.__load_extra_plugins() > 0:
            # if here, at least one extra plugin was loaded, so we need to restore
            # the settings once more
            gdb.execute("self restore quiet")
        return None

    def __reload_auto_breakpoints(self):
        bkp_fname = unigdb.config.get("self.autosave_breakpoints_file")
        if bkp_fname:
            # restore if existing
            print(unigdb.config.__config__)
            if os.access(bkp_fname, os.R_OK):
                gdb.execute("source {:s}".format(bkp_fname))

            # add hook for autosave breakpoints on quit command
            source = [
                "define hook-quit",
                " save breakpoints {:s}".format(bkp_fname),
                "end"
            ]
            execute_gdb_script("\n".join(source) + "\n")
        return None

    def __load_extra_plugins(self):
        nb_added = -1
        try:
            nb_inital = len(self.loaded_commands)
            directories = unigdb.config.get("self.extra_plugins_dir")
            if directories:
                for directory in directories.split(";"):
                    directory = os.path.realpath(os.path.expanduser(directory))
                    if os.path.isdir(directory):
                        sys.path.append(directory)
                        for fname in os.listdir(directory):
                            if not fname.endswith(".py"):
                                continue
                            fpath = "{:s}/{:s}".format(directory, fname)
                            if os.path.isfile(fpath):
                                gdb.execute("source {:s}".format(fpath))
            nb_added = len(self.loaded_commands) - nb_inital
            if nb_added > 0:
                message.success("{:s} extra commands added from '{:s}'".format(Color.colorify(nb_added, "bold green"),
                                                                               Color.colorify(directory, "bold blue")))
        except gdb.error as e:
            message.error("failed: {}".format(str(e)))
        return nb_added

    @property
    def loaded_command_names(self):
        return [x[0] for x in self.loaded_commands]

    def invoke(self, args, from_tty):
        self.dont_repeat()
        gdb.execute("self help")
        return None

    def load(self, initial=False):
        """Load all the commands and functions defined by UNIGDB into GDB."""
        nb_missing = 0
        self.commands = [(x._cmdline_, x) for x in unigdb.commands.__commands__]

        # load all of the functions
        for function_class_name in unigdb.functions.__functions__:
            self.loaded_functions.append(function_class_name())

        def is_loaded(x):
            return any(filter(lambda u: x == u[0], self.loaded_commands))

        for cmd, class_name in self.commands:
            if is_loaded(cmd):
                continue

            try:
                self.loaded_commands.append((cmd, class_name, class_name()))

                if hasattr(class_name, "_aliases_"):
                    aliases = getattr(class_name, "_aliases_")
                    for alias in aliases:
                        SelfAlias(alias, cmd)

            except Exception as reason:
                self.missing_commands[cmd] = reason
                nb_missing += 1

        # sort by command name
        self.loaded_commands = sorted(self.loaded_commands, key=lambda x: x[1]._cmdline_)

        if initial:
            print("{:s} for {:s} ready, type `{:s}' to start, `{:s}' to configure".format(
                Color.greenify("UNIGDB"), get_os(),
                Color.colorify("self", "underline yellow"),
                Color.colorify("self config", "underline pink")
            ))

            ver = "{:d}.{:d}".format(sys.version_info.major, sys.version_info.minor)
            nb_cmds = len(self.loaded_commands)
            print("{:s} commands loaded for GDB {:s} using Python engine {:s}".format(
                Color.colorify(nb_cmds, "bold green"),
                Color.colorify(gdb.VERSION, "bold yellow"),
                Color.colorify(ver, "bold red")))

            if nb_missing:
                message.warn("{:s} command{} could not be loaded, run `{:s}` to know why.".format(
                    Color.colorify(nb_missing, "bold red"),
                    "s" if nb_missing > 1 else "",
                    Color.colorify("self missing", "underline pink")
                ))
        return None


class SelfHelpCommand(gdb.Command):
    """UNIGDB help sub-command."""
    _cmdline_ = "self help"
    _syntax_ = _cmdline_

    def __init__(self, commands, *args, **kwargs):
        super(SelfHelpCommand, self).__init__(SelfHelpCommand._cmdline_,
                                              gdb.COMMAND_SUPPORT,
                                              gdb.COMPLETE_NONE,
                                              False)
        self.docs = []
        self.generate_help(commands)
        self.refresh()
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        print(message.titlify("UNIGDB - GDB Extra Features"))
        print(self.__doc__)
        return None

    def generate_help(self, commands):
        """Generate builtin commands documentation."""
        for command in commands:
            self.add_command_to_doc(command)
        return None

    def add_command_to_doc(self, command):
        """Add command to UNIGDB documentation."""
        cmd, class_name, _ = command
        if " " in cmd:
            # do not print subcommands in gef help
            return None
        doc = getattr(class_name, "__doc__", "").lstrip()
        doc = "\n                         ".join(doc.split("\n"))
        aliases = " (alias: {:s})".format(", ".join(class_name._aliases_)) if hasattr(class_name, "_aliases_") else ""
        msg = "{cmd:<25s} -- {help:s}{aliases:s}".format(cmd=cmd, help=Color.greenify(doc), aliases=aliases)
        self.docs.append(msg)
        return None

    def refresh(self):
        """Refresh the documentation."""
        self.__doc__ = "\n".join(sorted(self.docs))
        return None


class SelfConfigCommand(gdb.Command):
    """UNIGDB configuration sub-command
    This command will help set/view UNIGDB settingsfor the current debugging session.
    It is possible to make those changes permanent by running `gef save` (refer
    to this command help), and/or restore previously saved settings by running
    `gef restore` (refer help).
    """
    _cmdline_ = "self config"
    _syntax_ = "{:s} [setting_name] [setting_value]".format(_cmdline_)

    def __init__(self, loaded_commands, *args, **kwargs):
        super(SelfConfigCommand, self).__init__(SelfConfigCommand._cmdline_, gdb.COMMAND_NONE, prefix=False)
        self.loaded_commands = loaded_commands
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        argv = gdb.string_to_argv(args)
        argc = len(argv)

        if not (0 <= argc <= 2):
            message.error("Invalid number of arguments")
            return None

        if argc == 0:
            print(message.titlify("UNIGDB configuration settings"))
            self.print_settings()
            return None

        if argc == 1:
            prefix = argv[0]
            names = list(filter(lambda x: x.startswith(prefix), unigdb.config.__config__.keys()))
            if names:
                if len(names) == 1:
                    print(message.titlify("UNIGDB configuration setting: {:s}".format(names[0])))
                    self.print_setting(names[0], verbose=True)
                else:
                    print(message.titlify("UNIGDB configuration settings matching '{:s}'".format(argv[0])))
                    for name in names:
                        self.print_setting(name)
            return None
        self.set_setting(argc, argv)
        return None

    def print_setting(self, plugin_name, verbose=False):
        res = unigdb.config.get(plugin_name, get_all=True)
        string_color = unigdb.config.get("theme.dereference_string")
        misc_color = unigdb.config.get("theme.dereference_base_address")

        if not res:
            return None

        _value, _desc = res
        _setting = Color.colorify(plugin_name, "green")
        _type = type(_value).__name__
        if isinstance(_value, str):
            _value = '"{:s}"'.format(Color.colorify(_value, string_color))
        else:
            _value = Color.colorify(_value, misc_color)

        print("{:s} ({:s}) = {:s}".format(_setting, _type, _value))

        if verbose:
            print(Color.colorify("\nDescription:", "bold underline"))
            print("\t{:s}".format(_desc))
        return None

    def print_settings(self):
        for x in sorted(unigdb.config.__config__):
            self.print_setting(x)
        return None

    def set_setting(self, argc, argv):
        if "." not in argv[0]:
            message.error("Invalid command format")
            return None

        loaded_commands = [x[0] for x in unigdb.config.__unigdb__.loaded_commands] + ["self"]
        plugin_name = argv[0].split(".", 1)[0]
        if plugin_name not in loaded_commands:
            message.error("Unknown plugin '{:s}'".format(plugin_name))
            return None

        _value, _doc = unigdb.config.get(argv[0], get_all=True)
        if _value is None:
            message.error("Failed to get '{:s}' config setting".format(argv[0],))
            return None

        _type = type(_value)
        if isinstance(_value, bool):
            _newval = True if argv[1] == 'True' else False
        else:
            _newval = _type(argv[1])

        unigdb.config.set(argv[0], _newval, _doc)
        unigdb.events.reset_all_caches()
        return None

    def complete(self, text, word):
        settings = sorted(unigdb.config.__config__)

        if text == "":
            # no prefix: example: `self config TAB`
            return [s for s in settings if word in s]

        if "." not in text:
            # if looking for possible prefix
            return [s for s in settings if s.startswith(text.strip())]

        # finally, look for possible values for given prefix
        return [s.split(".", 1)[1] for s in settings if s.startswith(text.strip())]


class SelfSaveCommand(gdb.Command):
    """UNIGDB save sub-command.
    Saves the current configuration of UNIGDB to disk (by default in file '~/.unigdb.rc')."""
    _cmdline_ = "self save"
    _syntax_ = _cmdline_

    def __init__(self, *args, **kwargs):
        super(SelfSaveCommand, self).__init__(SelfSaveCommand._cmdline_, gdb.COMMAND_SUPPORT,
                                              gdb.COMPLETE_NONE, False)
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        cfg = configparser.RawConfigParser()
        old_sect = None

        # save the configuration
        for key in sorted(unigdb.config.__config__):
            sect, optname = key.split(".", 1)
            value = unigdb.config.get(key)

            if old_sect != sect:
                cfg.add_section(sect)
                old_sect = sect

            cfg.set(sect, optname, value)

        # save the aliases
        cfg.add_section("aliases")
        for alias in __aliases__:
            cfg.set("aliases", alias._alias, alias._command)

        with open(unigdb.config.UNIGDB_RC, "w") as fd:
            cfg.write(fd)

        message.success("Configuration saved to '{:s}'".format(unigdb.config.UNIGDB_RC))
        return None


class SelfRestoreCommand(gdb.Command):
    """UNIGDB restore sub-command.
    Loads settings from file '~/.unigdb.rc' and apply them to the configuration of UNIGDB."""
    _cmdline_ = "self restore"
    _syntax_ = _cmdline_

    def __init__(self, *args, **kwargs):
        super(SelfRestoreCommand, self).__init__(SelfRestoreCommand._cmdline_,
                                                 gdb.COMMAND_SUPPORT,
                                                 gdb.COMPLETE_NONE,
                                                 False)
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        if not os.access(unigdb.config.UNIGDB_RC, os.R_OK):
            return None

        quiet = args.lower() == "quiet"
        cfg = configparser.ConfigParser()
        cfg.read(unigdb.config.UNIGDB_RC)

        for section in cfg.sections():
            if section == "aliases":
                # load the aliases
                for key in cfg.options(section):
                    SelfAlias(key, cfg.get(section, key))
                continue

            # load the other options
            for optname in cfg.options(section):
                try:
                    key = "{:s}.{:s}".format(section, optname)
                    _value, _doc = unigdb.config.get(key, get_all=True)
                    new_value = cfg.get(section, optname)
                    if isinstance(_value, bool):
                        new_value = True if new_value == "True" else False
                    new_value = int(new_value) if new_value.isdigit() or isinstance(_value, int) else new_value
                    unigdb.config.set(key, new_value, _doc)
                except Exception:
                    pass

        if not quiet:
            message.success("Configuration from '{:s}' restored".format(
                Color.colorify(unigdb.config.UNIGDB_RC, "bold blue")
            ))
        return None


class SelfMissingCommand(gdb.Command):
    """UNIGDB missing sub-command
    Display the UNIGDB commands that could not be loaded, along with the reason of why
    they could not be loaded.
    """
    _cmdline_ = "self missing"
    _syntax_ = _cmdline_

    def __init__(self, *args, **kwargs):
        super(SelfMissingCommand, self).__init__(SelfMissingCommand._cmdline_,
                                                 gdb.COMMAND_SUPPORT,
                                                 gdb.COMPLETE_NONE,
                                                 False)
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        config_arrow_right = unigdb.config.get('theme.chain_arrow_right')
        missing_commands = unigdb.config.__unigdb__.missing_commands.keys()
        if not missing_commands:
            message.success("No missing command")
            return None

        for missing_command in missing_commands:
            reason = unigdb.config.__unigdb__.missing_commands[missing_command]
            message.warn("Command `{}` is missing, reason {} {}".format(
                missing_command,
                config_arrow_right,
                reason
            ))
        return None


class SelfSetCommand(gdb.Command):
    """Override GDB set commands with the context from UNIGDB.
    """
    _cmdline_ = "self set"
    _syntax_ = "{:s} [GDB_SET_ARGUMENTS]".format(_cmdline_)

    def __init__(self, *args, **kwargs):
        super(SelfSetCommand, self).__init__(SelfSetCommand._cmdline_,
                                             gdb.COMMAND_SUPPORT,
                                             gdb.COMPLETE_SYMBOL,
                                             False)
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        args = args.split()
        cmd = ["set", args[0], ]
        for p in args[1:]:
            if p.startswith("$_unigdb"):
                c = gdb.parse_and_eval(p)
                cmd.append(c.string())
            else:
                cmd.append(p)

        gdb.execute(" ".join(cmd))
        return None


class SelfRunCommand(gdb.Command):
    """Override GDB run commands with the context from UNIGDB.
    Simple wrapper for GDB run command to use arguments set from `self set args`. """
    _cmdline_ = "self run"
    _syntax_ = "{:s} [GDB_RUN_ARGUMENTS]".format(_cmdline_)

    def __init__(self, *args, **kwargs):
        super(SelfRunCommand, self).__init__(SelfRunCommand._cmdline_,
                                             gdb.COMMAND_SUPPORT,
                                             gdb.COMPLETE_FILENAME,
                                             False)
        return None

    def invoke(self, args, from_tty):
        self.dont_repeat()
        if unigdb.proc.alive:
            gdb.execute("continue")
            return None

        argv = args.split()
        gdb.execute("self set args {:s}".format(" ".join(argv)))
        gdb.execute("run")
        return None


# Initialize commands
unigdb.config.__unigdb__ = SelfCommand()
unigdb.config.__unigdb__.setup()
