import market, traceback

class Purger:
    def __init__(self, const):
        self.all = False
        self.contains = []
        self.not_contains = []
        self.caps_contains = []
        self.not_caps_contains = []
        self.user = []
        self.not_user = []
        if const == "%all%":
            self.all = True
        else:
            while "%" in const:
                index = const.find("%")
                const = const[index+1:]
                index = const.find("%")
                check_type = const[:index]
                const = const[index+1:]
                index = const.find("%")
                check = const[:index]
                const = const[index+1:]
                index = const.find("%")
                const = const[index+1:]
                if check_type.lower() == "c":
                    self.contains.append(check)
                elif check_type.lower() == "nc":
                    self.not_contains.append(check)
                elif check_type.lower() == "ic":
                    self.caps_contains.append(check.lower())
                elif check_type.lower() == "inc":
                    self.not_caps_contains.append(check.lower())
                elif check_type.lower() == "u":
                    self.user.append(check.lower())
                elif check_type.lower() == "nu":
                    self.not_user.append(check.lower())


    def check(self, message):
        if self.all:
            return True
        for check in self.contains:
            if check in message.content:
                return True
        for check in self.caps_contains:
            if check.lower() in message.content.lower():
                return True
        for check in self.not_contains:
            if check in message.content:
                return False
        for check in self.not_caps_contains:
            if check in message.content.lower():
                return False
        for check in self.user:
            if message.author.name.lower() == check:
                return True
        for check in self.not_user:
            if message.author.name.lower() == check:
                return False
        return True

current_purgers = {}
def purge_checker(msg):
    if msg.channel in current_purgers:
        return current_purgers[msg.channel].check(msg)
    return False

def moder_handle(bot, msg, cmd):
    formatting = bot.prefix + "help to see help!"
    try:
        if cmd[0] == "purge":
            formatting = bot.prefix + "purge [limit] [params]"
            if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                if len(cmd) > 2 and market.is_number(cmd[1]):
                    try:
                        purger = Purger(" ".join(cmd[2:]))
                        current_purgers[msg.channel.id] = purger
                        yield from bot.client.purge_from(msg.channel, limit=int(cmd[1]), check=purge_checker)
                        yield from bot.client.send_message(msg.channel, "Purge complete!")
                        del current_purgers[msg.channel.id]
                    except:
                        yield from bot.client.send_message(msg.channel, bot.name + " doesn't have permission to purge!")
                else:
                    raise IndexError
            else:
                yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")

    except (IndexError, ValueError, KeyError):
        yield from bot.client.send_message(msg.channel, formatting)
        traceback.print_exc()
    except Exception:
        yield from bot.client.send_message(msg.channel, "Something went wrong! Please use " + bot.prefix + "ticket error <message> to send an error report to me!")
        traceback.print_exc()

def moder_handle_l(cmd):
    return 1

def setup(bot, help_page, filename):
    bot.register_command("purge", moder_handle, moder_handle_l)