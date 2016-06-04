from os import listdir
from os.path import isfile, join

def default_handle(bot, message, command):
    return

def default_restart():
    return

class Bot:
    def __init__(self, client):
        self.name = "YoyoBot2"
        self.prefix = "€"
        self.ping_message = "Pong!"
        self.ping_start = 0
        self.pages = 5
        self.client = client
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

#help.register(["command", "subcommand"], "command for doing stuff"
class HelpPage:
    # header is an array of strings
    def __init__(self, header):
        if type(header) is str:
            header = [header]
        self.header = header
        # [ commandname: [descritption, helppage]
        self.commands = {}
        self.commands["__ordering__"] = []

    # command is the command your adding, for example command subcommand
    def register(self, command, params, description, root=[], help=None, silent=False, header=None, header_append=False):
        if header is None:
            header = self.header
        else:
            if type(header) is str:
                header = [header]
            if header_append:
                header = self.header + header
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
        if len(root) > 0:
            for i in range(len(root)):
                if root[i] in help.commands:
                    help = help.commands[root[i]][2]
                else:
                    help = None
                    break
        if help is not None:
            help.commands[command] = [params, description, HelpPage(header), silent]
            help.commands["__ordering__"].append(command)

    def join(self, prefix, lines, suffix):
        result = ""
        for line in lines:
            result = result + prefix + line + suffix
        return result

    def get(self, bot, command=[], command_head=None):
        try:
            if command_head is None:
                if len(command) == 0:
                    command_head = ""
                elif not self.commands[command[0]][3]:
                    command_head = " ".join(command) + " "
            if len(command) == 0:
                lines = self.join(" ", self.header, "\n")
                for command in self.commands["__ordering__"]:
                    info = self.commands[command]
                    if not info[3]:
                        start = "         >>** " + bot.prefix + command_head + command + "** " + " ".join(info[0]) + " - "
                        spacing = " " * len(start)
                        start += info[1][0] + "\n"
                        if len(info[1]) > 1:
                            for i in range(1, len(info[1])):
                                start += self.join(spacing, info[1][i], "\n")
                        lines += start
                lines = lines.replace("%b%", bot.name).replace("%p%", bot.prefix)
                return lines
            elif command[0] in self.commands:
                help_page = self.commands[command[0]][2]
                return help_page.get(bot, command[1:], command_head)
        except (IndexError, KeyError, ValueError):
            pass
        return self.join(" ", self.header, "\n") + "         >> No commands found!"


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