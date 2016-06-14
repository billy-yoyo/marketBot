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
            if check not in message.content:
                return True
        for check in self.not_caps_contains:
            if check not in message.content.lower():
                return True
        for check in self.user:
            if message.author.name.lower() == check:
                return True
        for check in self.not_user:
            if message.author.name.lower() != check:
                return True
        return False

current_purgers = {}
def purge_checker(msg):
    if msg.channel.id in current_purgers:
        return current_purgers[msg.channel.id].check(msg)
    return False

def moder_handle(bot, msg, cmd):
    formatting = bot.prefix + "help to see help!"
    try:
        cd_result = bot.get_cooldown(msg.author.id, cmd)
        if cd_result > 0:
            yield from bot.client.send_message(msg.channel, "That command is on cooldown, please wait another " + str(int(cd_result)) + " seconds before using it")
        else:
            if cmd[0] == "purge":
                formatting = bot.prefix + "purge [limit] [params]"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    if len(cmd) > 2 and market.is_number(cmd[1]):
                        try:
                            purger = Purger(" ".join(cmd[2:]))
                            current_purgers[msg.channel.id] = purger
                            yield from bot.client.purge_from(msg.channel, limit=int(cmd[1]), check=purge_checker)
                            #yield from bot.client.send_message(msg.channel, "Purge complete!")
                            del current_purgers[msg.channel.id]
                        except:
                            traceback.print_exc()
                            yield from bot.client.send_message(msg.channel, bot.name + " doesn't have permission to purge!")
                    else:
                        raise IndexError
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "prefix":
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    prefix = " ".join(cmd[1:])
                    bot.market.settings["prefix"][msg.channel.id] = prefix
                    yield from bot.client.send_message(msg.channel, "Changed the bot's prefix to " + prefix + " for this channel")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "modlog":
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    if cmd[1] == "off":
                        if msg.channel.server.id in bot.market["settings"]["modlog"]:
                            del bot.market.settings["modlog"][msg.channel.server.id]
                            yield from bot.client.send_message(msg.channel, "Turned modlog off")
                        else:
                            yield from bot.client.send_message(msg.channel, "Modlog not set for this server!")
                    elif cmd[1] == "on":
                        bot.market.settings[msg.channel.server.id] = msg.channel.id
                        yield from bot.client.send_message(msg.channel, "Set this channel to the mod log channel.")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "ignore":
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    if not msg.channel.id in bot.market.settings["ignore_list"]:
                        bot.market.settings["ignore_list"].append(msg.channel.id)
                        yield from bot.client.send_message(msg.channel, "Channel now being ignored, use " + bot.prefix + "unignore to stop ignoring")
                    else:
                        yield from bot.client.send_message(msg.channel, "Channel already being ignored... How did I get this message?")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "unignore":
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    if msg.channel.id in bot.market.settings["ignore_list"]:
                        bot.market.settings["ignore_list"].remove(msg.channel.id)
                        yield from bot.client.send_message(msg.channel, "Channel is no longer being ignored!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Channel already isn't being ignored!")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "cleanup":
                formatting = bot.prefix + "cleanup stop|[delay] | " + bot.prefix + "cleanup tags stop|[delay]"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    if cmd[1] == "stop":
                        bot.market.settings["cleanup"][msg.channel.id] = -1
                        yield from bot.client.send_message(msg.channel, "Bot messages will now not be removed from this channel")
                    elif cmd[1] == "tags":
                        if cmd[2] == "stop":
                            bot.market.settings["cleanup_tags"][msg.channel.id] = -1
                            yield from bot.client.send_message(msg.channel, "Bot tags will now not be removed from this channel")
                        else:
                            bot.market.settings["cleanup_tags"][msg.channel.id] = int(cmd[2])
                            yield from bot.client.send_message(msg.channel, "Bot tags will now be removed after " + str(int(cmd[2])) + " seconds")
                    else:
                        bot.market.settings["cleanup"][msg.channel.id] = int(cmd[1])
                        yield from bot.client.send_message(msg.channel, "Bot messages will now be removed after " + str(int(cmd[1])) + " seconds")
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
    bot.register_command("prefix", moder_handle, moder_handle_l)
    bot.register_command("ignore", moder_handle, moder_handle_l)
    bot.register_command("unignore", moder_handle, moder_handle_l)
    bot.register_command("cleanup", moder_handle, moder_handle_l)