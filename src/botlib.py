import time, discord, random, datetime
from os import listdir
from os.path import isfile, join
from copy import copy

def default_handle(bot, message, command):
    return

def default_restart():
    return

statuses = [
    "with your emotions",
    "the game",
    "with a yoyo",
    "hello world!",
    "with the market",
    "with my code",
    "hide and seek",
    "with fire",
    "the field",
    "the victim",
    "the long con",
    "it cool"
]


class UserHistory:
    MESSAGE_CAP = 10
    def __init__(self, userid, username, offenses=[]):
        self.id = userid
        self.name = username
        self.history = []
        self.offenses = []

        self.banned = False

        self.next_offense = ""

    def flush(self):
        if self.next_offense != "":
            self.offenses.append(self.next_offense)
            self.next_offense = ""

    def add_offense(self, offense):
        self.next_offense = offense

    def add_message(self, message):
        if len(self.history) >= self.MESSAGE_CAP:
            self.history = [message] + self.history[:-1]
        else:
            self.history = [message] + self.history

    def get_messages(self, seconds):
        time_stamp = datetime.datetime.now()
        msgs = []
        for msg in self.history:
            elap = (time_stamp - msg.timestamp).total_seconds()
            if elap > seconds:
                break
            msgs.append(msg)
        return msgs


def locals_test():
    print(locals())

def clear_globals(*save):
    globs = copy(globals())
    for key in globs:
        if key not in save:
            del globals()[key]
    return globs


class Bot:
    def __init__(self, client):
        self.name = "ExampleBot"
        self.default_prefix = "m$"
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
        self.pings = []
        self.restarter = default_restart
        self.admin_list = []
        self.cmd_cds = {}
        self.imgs = {}
        self.start_time = time.time()
        self.setup = False
        self.next_status_change = 0
        self.commands_used = 0
        self.last_message = None

        self.automod_id_map = {
            "delete": 0,
            "edit": 1,
            "kick": 2,
            "ban": 3,
            "role": 4,
            "message": 5
        }

        self.last_disable = ""

    def handle_automod(self, message):
        if not message.author.id in self.market.spam:
            self.market.spam[message.author.id] = UserHistory(message.author.id, message.author.name)
        self.market.spam[message.author.id].add_message(message)

        timestamp = datetime.datetime.now()
        for userid in self.market.automod_code["bans"]:
            if self.market.automod_code["bans"][userid] < timestamp:
                yield from self.client.unban(message.channel.server, discord.User(id=userid))

        deleted = False
        if message.channel.id in self.market.automod and message.author.id in self.market.spam:
            for name in self.market.automod[message.channel.id]:
                func = self.market.automod[message.channel.id][name]
                history = self.market.spam[message.author.id]
                old_globals = clear_globals("clear_globals", "copy", "clear_locals", "locals_test")

                results = []
                try:
                    results = func(message, history)
                except:
                    import traceback
                    traceback.print_exc()

                clear_globals("clear_globals", "copy", "clear_locals")

                globals().update(old_globals)
                #locals().update(old_locals)

                if type(results) != list:
                    results = [results]
                if len(results) < 5:
                    for result in results:
                        try:
                            if type(result) is dict:
                                id = result.pop("id", -1)
                                if type(id) is str: id = self.automod_id_map[id.lower()]
                                if id == 0: # delete
                                    yield from self.client.delete_message(message)
                                    deleted = True
                                elif id == 1: # edit
                                    text = result.pop("text", "")
                                    if text != "":
                                        yield from self.client.edit_message(message, text)
                                elif id == 2: # kick
                                    yield from self.client.kick(message.author)
                                elif id == 3: # ban
                                    length = result.pop("time", -1)
                                    message_days = result.pop("days", 1)
                                    history.banned = True
                                    yield from self.client.ban(message.author, message_days)
                                    if length > 0:
                                        self.market.automod_code["bans"][message.author.id] = length
                                elif id == 4: # role
                                    name = result.pop("role", "")
                                    if name != "":
                                        for role in message.channel.server.roles:
                                            if role.name == name:
                                                self.client.add_roles(message.author, role)
                                                break
                                elif id == 5: # message
                                    text = result.pop("text", "")
                                    if text != "":
                                        yield from self.client.send_message(message.channel, text)

                            self.market.spam[message.author.id].flush()
                        except:
                            pass
        return deleted


    def update_status(self, user):
        ctime = time.time()
        if self.next_status_change <= ctime:
            #print("status changed to: " + user)
            self.next_status_change = ctime + 120
            game = discord.Game()
            game.name = statuses[random.randint(0, len(statuses)-1)]
            #print("status changed to: " + game.name)
            yield from self.client.change_status(game=game)

    def get_cooldown(self, user, command):
        if type(command) is list:
            command = " ".join(command)
        if user in self.cmd_cds:
            cds = self.cmd_cds[user]
            for cmdcd in self.cds:
                if command.startswith(cmdcd):
                    return self.cds[cmdcd] - time.time()
        return 0

    def check_disable(self, channel, command):
        if self.setup:
            if channel in self.market.disables:
                check = command[0]
                if check in self.market.disables[channel]:
                    self.last_disable = check
                    return True
                for word in command[1:8]:
                    check += " " + word
                    if check in self.market.disables[channel]:
                        self.last_disable = check
                        return True
        return False

    def cooldown(self, user, command, amount):
        if not self.is_me(user, byid=True):
            if not user in self.cmd_cds:
                self.cmd_cds[user] = {}
            self.cmds[user][command] = time.time() + amount

    def is_me(self, msg, byid=False):
        if byid:
            return msg in self.admin_list
        else:
            return msg.author.id in self.admin_list

    def call_restart(self):
        self.restarter()

    def pong(self, msg):
        for func in self.pings:
            yield from func(self, msg)

    def register_command(self, command, command_handler, length_handler):
        self.commands[command] = [command_handler, length_handler]

    def register_ping(self, command):
        self.pings.append(command)

    def handle_bind(self, ch, command, binds, index=0):
        if self.setup:
            if ch in binds:
                bcmd = command
                check = command[0]
                if check in binds[ch]:
                    bcmd = (binds[ch][check] + " " + " ".join(command[1:])).split(" ")
                for i, word in enumerate(command[1:8]):
                    check += " " + word
                    if check in binds[ch]:
                        new_cmd = binds[ch][check]
                        if len(command[i+1:]) > 0:
                            new_cmd += " " + " ".join(command[i:])
                        bcmd = new_cmd.split(" ")
                return bcmd
        return command

    def command_exists(self, command):
        if type(command) is str:
            command = command.split(" ")
        return command[0] in self.commands

    # command is the message seperated by " "
    def handle_command(self, role, command):
        if command[0] in self.commands:  # root command exists
            if role.check_command(command, self.commands[command[0]][1](command)):
                return self.commands[command[0]][0]
        return None

    def mention_to_command(self, message):
        text = message.content.replace("<@" + message.channel.server.me.id + ">", "")
        cmds = text.split(" ")
        while "" in cmds: cmds.remove("")
        return cmds

    def check_permission(self, command, member, channel):
        if channel.id in self.market.perms:
            for i in range(1, min(len(command)+1, 7)):
                check = " ".join(command[:i])
                if check in self.market.perms[channel.id]:
                    permissions = channel.permissions_for(member)
                    for perm in self.market.perms[channel.id][check]:
                        spl = perm.split(" ")
                        key = spl[0]
                        value = " ".join(spl[1:])
                        if key == "role":
                            has_role = False
                            for role in member.roles:
                                if role.name == value:
                                    has_role = True
                                    break
                            if not has_role:
                                return False
                        elif key == "perm":
                            if not getattr(permissions, value, True):
                                return False
                        else:
                            print("PERMISSIONS ERROR: unknown permissions key '" + key + "'")
        return True

    def valid_permission(self, perm):
        permissions = discord.Permissions()
        return type(getattr(permissions, perm, None)) is bool

    def list_valid_permissions(self):
        permissions = discord.Permissions()
        return [x for x in dir(permissions) if type(getattr(permissions, x, None)) is bool]

    def run_command(self, message, role):
        if not message.channel.id in self.market.settings["ignore_list"] or message.content == self.prefix + "unignore":
            if message.content.startswith(self.prefix) or (not message.channel.is_private and message.channel.server.me in message.mentions) or message.channel.is_private:
                comamnd = None
                if message.content.startswith(self.prefix):
                    command = message.content[len(self.prefix):].split(" ")
                elif message.channel.is_private:
                    command = message.content.split(" ")
                else:
                    command = self.mention_to_command(message)
                if command is not None:
                    command = self.handle_bind(message.channel.id, command, self.market.binds)
                    handle = self.handle_command(role, command)
                    if handle is not None:
                        if not self.check_disable(message.channel.id, command):
                            if self.check_permission(command, message.author, message.channel):
                                self.commands_used += 1
                                yield from handle(self, message, command)
                                return True
                            else:
                                yield from self.client.send_message(message.channel, "You don't have permission to use that command!")
                        else:
                            yield from self.client.send_message(message.channel, "Command `" + self.last_disable + "` disabled in this channel! See " + self.prefix + "disabled for a list of disabled commands.")
                            return False
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
