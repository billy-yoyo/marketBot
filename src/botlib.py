import traceback
from os import listdir
from os.path import isfile, join

def default_handle(bot, message, command):
    return

def default_restart():
    return

class Bot:
    def __init__(self, client):
        self.name = "ExampleBot"
        self.prefix = "?!"
        self.ping_message = "Pong!"
        self.ping_start = 0
        self.pages = 7
        self.client = client
        self.version = "1.0.0"
        self.help_page = None
        # command: [command_handler, length_handler]
        self.commands = {}
        # bindname: [ root_command, {more_binds} }
        self.binds = {}
        self.pings = []
        self.restarter = default_restart

    def call_restart(self):
        self.restarter()

    def pong(self, msg):
        for func in self.pings:
            yield from func(self, msg)

    def register_command(self, command, command_handler, length_handler):
        self.commands[command] = [command_handler, length_handler]

    def register_ping(self, command):
        self.pings.append(command)

    def handle_bind(self, command, binds, index=0):
        if command[index] in binds:
            bind_arr = binds[command[index]][0]
            command[index] = bind_arr[0]
            if len(bind_arr) == 1 or bind_arr[1] is None:
                return command
            else:
                return self.handle_bind(command, binds[command[index]][1], index+1)
        return command

    # command is the message seperated by " "
    def handle_command(self, role, command):
        if command[0] in self.commands:  # root command exists
            command = self.handle_bind(command, self.binds)
            if role.check_command(command, self.commands[command[0]][1](command)):
                return self.commands[command[0]][0]
        return None

    def run_command(self, message, role):
        if message.content.startswith(self.prefix):
            command = message.content[len(self.prefix):].split(" ")
            handle = self.handle_command(role, command)
            if handle is not None:
                yield from handle(self, message, command)
                return True
        return False


class Role:
    def __init__(self, all=False, whitelist=[], blacklist=[]):
        self.whitelist = whitelist
        self.blacklist = blacklist
        self.all = all

    # command_name = "+" / "-" / "~" for whitelist, blacklist, clear respectively
    # all = "+" / "-" for all = true or false
    # ~ = "+" or "-" to clear whitelist or blacklist
    def edit(self, **kwargs):
        for key, value in kwargs.iteritems():
            if key == "all":
                if value == "+":
                    self.all = True
                elif value == "-" or value == "~":
                    self.all = False
            elif key == "~":
                if value == "+":
                    self.whitelist = []
                elif value == "-":
                    self.blacklist = []
            else:
                if value == "+":
                    if key not in self.whitelist:
                        self.whitelist.append(key)
                    if key in self.blacklist:
                        self.blacklist.remove(key)
                elif value == "-":
                    if key not in self.blacklist:
                        self.blacklist.append(key)
                    if key in self.whitelist:
                        self.whitelist.remove(key)
                elif value == "~":
                    if key in self.blacklist:
                        self.blacklist.remove(key)
                    if key in self.whitelist:
                        self.whitelist.remove(key)


    def check_command(self, command, length):
        if self.all:
            result = True
            for i in range(length):
                check = " ".join(command[:i+1])
                if check in self.blacklist:
                    result = False
                elif check in self.whitelist:
                    result = True
            return result
        else:
            result = False
            for i in range(length):
                check = " ".join(command[:i+1])
                if check in self.whitelist:
                    result = True
                elif check in self.blacklist:
                    result = False
            return result

class HelpPage:
    # header is an array of strings or a single string, shown at the beginning of the help page.
    def __init__(self, header):
        if type(header) is str:
            header = [header]
        # shown at the start of the help page
        self.header = header
        # { commandname: [params, descritption, helppage, hidden] }
        self.commands = {}
        # used to determine the order in which the commands were registered so it can reliably print them in the corrent order
        self.commands["__ordering__"] = []
        # number showing how many commands are registered with this help page (or any of it's child pages)
        self.registered_commands = 0

    # registers a command to the help page;
    #    command is the command as a string that you're registering
    #    params are the parameters of the command, this can be a string seperated by " ", a string without " " or a list of strings
    #    description is the description of the commands, this can be a single string or a list of strings
    #    root is optional; It is the "root" command as a string seperated by " ", a string without " " or a list os strings
    #                      If root is not given there is no root and it will show up at the default help page
    #    hidden is optional; It determines if this command will be hidden from the help pages
    #                        If hidden is not given it defaults to False
    #    header is optional; It is the text that shows at the beginning of the help page (as a string or a list of strings)
    #                        If no header is given it uses the default help page's
    #    header_append is optional; It determines if the header given will override the default header or add to it
    #                               If header_append is not given it defaults to False
    #
    def register(self, command, params, description, root=[], hidden=False, header=None, header_append=False):
        self.registered_commands += 1
        if type(params) is str:
            if " " in params:
                params = params.split(" ")
            else:
                params = [params]
        if type(description) is str:
            description = [description]
        if type(root) is str:
            if " " in root:
                root = root.split(" ")
            else:
                root = [root]
        help = self
        roots_done = []
        if len(root) > 0:
            for i in range(len(root)):
                roots_done.append(root[i])
                raw_root = " ".join(roots_done)
                if raw_root in help.commands:
                    help = help.commands[raw_root][2]
                else:
                    help = None
                    break
        if help is not None:
            if header is None:
                header = self.header
            else:
                if type(header) is str:
                    header = [header]
                if header_append:
                    header = help.header + header
            help.commands[command] = [params, description, HelpPage(header), hidden]
            help.commands["__ordering__"].append(command)

    # simple join helper-function
    def _join(self, prefix, lines, suffix):
        result = ""
        for line in lines:
            result = result + prefix + line + suffix
        return result

    # returns the lines of help for the given command
    #       prefix is the prefix for the bots commands
    #       command is the command passed to the the help function split by " " (ignoring the help, so if you do !help page1 command would equal ["page1"])
    #       command_head is an internal parameter, it determines what gets put in front of the command.
    def get(self, bot, command=[], command_head=None):
        try:
            if command_head is None:
                if len(command) == 0:
                    command_head = ""
                elif not self.commands[command[0]][3]:
                    command_head = " ".join(command) + " "
            if len(command) == 0:
                lines = self._join(" ", self.header, "\n")
                for command in self.commands["__ordering__"]:
                    info = self.commands[command]
                    if not info[3]:
                        start = "         >>** " + bot.prefix + command + "** " + " ".join(info[0]) + " - "
                        spacing = " " * len(start)
                        start += info[1][0] + "\n"
                        if len(info[1]) > 1:
                            start += self._join(spacing, info[1][1:], "\n")
                        lines += start
                lines = lines.replace("%b%", bot.name).replace("%p%", bot.prefix)
                return lines
            elif command[0] in self.commands:

                help_page = self.commands[command[0]][2]
                if len(command) > 1:
                    command[1] = command[0] + " " + command[1]
                return help_page.get(bot, command[1:], command_head)
        except (IndexError, KeyError, ValueError):
            pass
        # If no help page could be found, return a message saying so.
        return self._join(" ", self.header, "\n") + "         >> No commands found!"


def load_plugins(bot, help_page):
    onlyfiles = [f for f in listdir("plugins/") if isfile(join("plugins/", f))]
    loaded = 0
    for filename in onlyfiles:
        fname = filename[:-3]
        if "__init__" not in filename and ".py" in filename:
            print("importing " + filename + "...")
            try:
                test = __import__("plugins."+fname, fromlist=["plugins"])
                test.setup(bot, help_page, fname)
                loaded += 1
            except():
                print("ERROR: Failed to import " + filename)
    print("Done, loaded " + str(loaded) + " plugins!")
