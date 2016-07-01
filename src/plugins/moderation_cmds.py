import market, traceback, discord, safeexec, botlib, random

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
            elif cmd[0] == "disable":
                formatting = bot.prefix + "disable [command] - Don't include the prefix in the command!"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    command = " ".join(cmd[1:])
                    if not command.startswith("disable") and not command.startswith("enable") and not command.startswith("disabled"):
                        if bot.command_exists(command):
                            if not msg.channel.id in bot.market.disables:
                                bot.market.disables[msg.channel.id] = []
                            bot.market.disables[msg.channel.id].append(command)
                            yield from bot.client.send_message(msg.channel, "Disabled `" + command + "` in this channel, use " + bot.prefix + "enable " + command + " to reenable")
                        else:
                            yield from bot.client.send_message(msg.channel, "`" + command + "` is not a valid command, remember you can only disable commands, not binds")
                    else:
                        yield from bot.client.send_message(msg.channel, "You can't disable the disable/enable commands!")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "enable":
                formatting = bot.prefix + "enable [command] - Don't include the prefix in the command!"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    command = " ".join(cmd[1:])
                    if msg.channel.id in bot.market.disables and command in bot.market.disables[msg.channel.id]:
                        bot.market.disables[msg.channel.id].remove(command)
                        yield from bot.client.send_message(msg.channel, "Enabled `" + command + "` in this channel.")
                    else:
                        yield from bot.client.send_message(msg.channel, "'" + command + "' is not disabled! See " + bot.prefix + "disabled for a list of disabled commands in this channel")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "disabled":
                formatting = bot.prefix + "disabled"
                if msg.channel.id in bot.market.disables and len(bot.market.disables[msg.channel.id]) > 0:
                    yield from bot.client.send_message(msg.channel, "The following commands are disabled in this channel: \n`" + "`, `".join(bot.market.disables[msg.channel.id]) + "`")
                else:
                    yield from bot.client.send_message(msg.channel, "No commands are disabled in this channel")
            elif cmd[0] == "bind":
                formatting = bot.prefix + "bind [command] => [command] - don't include the prefix"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    bind_cmd = ""
                    add_to_bind = True
                    result_cmd = ""
                    for word in cmd[1:]:
                        if word == "=>":
                            add_to_bind = False
                        elif add_to_bind:
                            if bind_cmd == "":
                                bind_cmd = word
                            else:
                                bind_cmd += " " + word
                        else:
                            if result_cmd == "":
                                result_cmd = word
                            else:
                                result_cmd += " " + word

                    if not msg.channel.id in bot.market.binds:
                        bot.market.binds[msg.channel.id] = {}

                    if result_cmd.replace(" ", "") == "":
                        if bind_cmd in bot.market.binds[msg.channel.id]:
                            del bot.market.binds[msg.channel.id][bind_cmd]
                            yield from bot.client.send_message(msg.channel, "Removed binding for `" + bind_cmd + "` in this channel")
                        else:
                            yield from bot.client.send_message(msg.channel, "`" + bind_cmd + "` isn't bound to anything!")
                    elif bot.command_exists(result_cmd):
                        bot.market.binds[msg.channel.id][bind_cmd] = result_cmd
                        yield from bot.client.send_message(msg.channel, "Bound `" + bind_cmd + "` to `" + result_cmd + "` in this channel")
                    else:
                        yield from bot.client.send_message(msg.channel, "Command `" + result_cmd + "` doesn't exist!")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "perms":
                formatting = bot.prefix + "perms [command] +|- [permission] - don't include the prefix"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    command = ""
                    add_to_command = True
                    permission = ""
                    add_perm = True
                    for word in cmd[1:]:
                        if add_to_command and word == "+" or word == "-":
                            if word == "-":
                                add_perm = False
                            add_to_command = False
                        elif add_to_command:
                            if command == "":
                                command = word
                            else:
                                command += " " + word
                        else:
                            if permission == "":
                                permission = word
                            else:
                                permission += " " + word
                    print(command + " : " + permission)

                    if not command == "perms":
                        if permission == "":
                            if msg.channel.id in bot.market.perms and command in bot.market.perms[msg.channel.id] and len(bot.market.perms[msg.channel.id][command]) > 0:
                                yield from bot.client.send_message(msg.channel, "Command `" + command + "` currently requires: `" + "`, `".join(bot.market.perms[msg.channel.id][command]) + "`")
                            else:
                                yield from bot.client.send_message(msg.channel, "Command `" + command + "` doesn't currently require any custom permissions")
                        else:
                            if bot.command_exists(command):
                                if not msg.channel.id in bot.market.perms:
                                    bot.market.perms[msg.channel.id] = {}
                                if not command in bot.market.perms[msg.channel.id]:
                                    bot.market.perms[msg.channel.id][command] = []
                                if add_perm:
                                    if not permission in bot.market.perms[msg.channel.id][command]:
                                        spl = permission.split(" ")
                                        perm_key = spl[0]
                                        perm_value = " ".join(spl[1:])
                                        if perm_key == "role":
                                            has_role = False
                                            role_name = perm_value
                                            for role in msg.channel.server.roles:
                                                if role.name == role_name:
                                                    has_role = True
                                                    break
                                            if has_role:
                                                bot.market.perms[msg.channel.id][command].append(permission)
                                                yield from bot.client.send_message(msg.channel, "Command `" + command + "` now requires role `" + role_name + "` to use it in this channel")
                                            else:
                                                yield from bot.client.send_message(msg.channel, "Invalid role name `" + role_name + "`")
                                        elif perm_key == "perm":
                                            permission_name = perm_value.replace(" ", "_").lower()
                                            if bot.valid_permission(permission_name):
                                                bot.market.perms[msg.channel.id][command].append("perm " + permission_name)
                                                yield from bot.client.send_message(msg.channel, "Command `" + command + "` now requires the `" + permission_name + "` permission to use it in this channel")
                                            else:
                                                yield from bot.client.send_message(msg.channel, "Invalid permission, must be one of: `" + "`, `".join(bot.list_valid_permissions()) + "`")
                                        else:
                                            yield from bot.client.send_message(msg.channel, "Invalid permission type, must be either `role` or `perm` (you gave `" + perm_key + "`)")
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Command `" + command + "` already requires permission `" + permission + "`")
                                else:
                                    if permission in bot.market.perms[msg.channel.id][command]:
                                        bot.market.perms[msg.channel.id][command].remove(permission)
                                        if permission.startswith("role "):
                                            yield from bot.client.send_message(msg.channel, "Command `" + command + "` no longer requires role `" + permission[5:] + "` to use it in this channel")
                                        elif permission.startswith("perm "):
                                            yield from bot.client.send_message(msg.channel, "Command `" + command + "` no longer requires permission `" + permission[5:] + "` to use it in this channel")
                                        else:
                                            yield from bot.client.send_message(msg.channel, "Command `" + command + "` no longer requires `" + permission + "`")
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Command `" + command + "` doesn't require permission `" + permission + "`, use `" + bot.prefix + "perms " + command + "` for a list of permissions")
                            else:
                                yield from bot.client.send_message(msg.channel, "Command `" + command + "` doesn't exist!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Can't add permissions to the `perms` command!")
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "automod":
                formatting = bot.prefix + "automod set|remove|list"
                if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                    if cmd[1] == "set":
                        formatting = bot.prefix + "automod set [name] [code]"
                        name = cmd[2]
                        code = " ".join(cmd[3:])
                        while code[0] == "`":
                            code = code[1:]
                        while code[-1] == "`":
                            code = code[:-1]
                        if code.startswith("py"):
                            code = code[2:]

                        result = safeexec.check_safe(code, ["add_offense", "get_messages", "len", "permissions_in", "get_channel", "get_member", "get_member_named", "permissions_for", "range"])
                        if result == 0:
                            func = safeexec.get_exec_function(code, ["message", "history"])
                            spam_names = [x for x in bot.market.spam.keys()]
                            uname = random.choice(spam_names)
                            uname2 = random.choice(spam_names)
                            history = bot.market.spam[uname2]
                            history_msg = msg
                            if len(history.history) > 0:
                                history_msg = random.choice(history.history)
                            elif bot.last_message is not None:
                                history_msg = bot.last_message
                            if safeexec.check_timeout(1, func, history_msg, bot.market.spam[uname]):
                                if not msg.channel.id in bot.market.automod:
                                    bot.market.automod[msg.channel.id] = {}
                                if not msg.channel.id in bot.market.automod_code:
                                    bot.market.automod_code[msg.channel.id] = {}
                                bot.market.automod[msg.channel.id][name] = func
                                bot.market.automod_code[msg.channel.id][name] = code
                                yield from bot.client.send_message(msg.channel, "SUCCESS: Added automod code for this channel")
                            else:
                                yield from bot.client.send_message(msg.channel, "ERROR: Your function took too long to process an example call, please edit it and try again. (must take under 2 seconds)")
                        else:
                            yield from bot.client.send_message(msg.channel, "ERROR: " + safeexec.error_map[result])
                    elif cmd[1] == "remove":
                        formatting = bot.prefix + "automod remove [name]"
                        name = cmd[2]
                        if msg.channel.id in bot.market.automod and name in bot.market.automod[msg.channel.id]:
                            del bot.market.automod[msg.channel.id][name]
                            yield from bot.client.send_message(msg.channel, "Removed automod code under name `" + name + "`")
                        else:
                            yield from bot.client.send_message(msg.channel, "No automod found with the name `" + name + "`")
                    elif cmd[1] == "list":
                        if msg.channel.id in bot.market.automod and len(bot.market.automod[msg.channel.id]) > 0:
                            yield from bot.client.send_message(msg.channel, "Automod code for this channel: `" + "`, `".join([x for x in bot.market.automod[msg.channel.id]]) + "`")
                        else:
                            yield from bot.client.send_message(msg.channel, "There's no automod code for this channel")
                    else:
                        raise IndexError
                else:
                    yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
            elif cmd[0] == "pm":
                if bot.is_me(msg):
                    user = None
                    if len(msg.mentions) > 0:
                        user = msg.mentions[0]
                    elif market.is_number(cmd[1]):
                        for server in bot.client.servers:
                            for member in server.members:
                                if member.id == cmd[1]:
                                    user = member
                    if user is not None:
                        msg = "[ADMIN MESSAGE] " + " ".join(cmd[2:])
                        yield from bot.client.send_message(user, msg)
                    else:
                        yield from bot.client.send_message(msg.channel, "Invalid user, must be an ID or a mention")
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admins can use that command!")
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
    bot.register_command("disable", moder_handle, moder_handle_l)
    bot.register_command("enable", moder_handle, moder_handle_l)
    bot.register_command("disabled", moder_handle, moder_handle_l)
    bot.register_command("bind", moder_handle, moder_handle_l)
    bot.register_command("perms", moder_handle, moder_handle_l)
    bot.register_command("pm", moder_handle, moder_handle_l)
    bot.register_command("automod", moder_handle, moder_handle_l)