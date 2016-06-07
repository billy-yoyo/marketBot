import traceback


def is_tag_banned(bot, msg):
    tagban = bot.market.tags["__tagban__"]
    if msg.channel.id in tagban:
        return msg.author.id in tagban[msg.channel.id]
    return False


def util_handle(bot, msg, cmd):
    formatting = bot.prefix + "help to see help!"
    try:
        cd_result = bot.get_cooldown(msg.author.id, cmd)
        if cd_result > 0:
            yield from bot.client.send_message(msg.channel, "That command is on cooldown, please wait another " + str(int(cd_result)) + " seconds before using it")
        else:
            if cmd[0] == "tag":
                if is_tag_banned(bot, msg) and not bot.is_me(msg):
                    yield from bot.client.send_message(":label: You are banned from using tags in this channel!")
                else:
                    if cmd[1] == "ban":
                        if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                            if len(msg.mentions) > 0:
                                for member in msg.mentions:
                                    if not msg.channel.id in bot.market.tags["__tagban__"]:
                                        bot.market.tags["__tagban__"][msg.channel.id] = []
                                    if not member.id in bot.market.tags["__tagban__"][msg.channel.id]:
                                        bot.market.tags["__tagban__"][msg.channel.id].append(member.id)
                                        yield from bot.client.send_message(msg.channel, ":label: " + member.name + " is no longer allowed to use tags in this channel")
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":label: " + member.name + " is already banned from using tags in this channel")
                            else:
                                yield from bot.client.send_message(msg.channel, ":label: Must mention at least one member!")
                        else:
                            yield from bot.client.send_message(msg.channel, ":label: You don't have permission to use this command!")
                    elif cmd[1] == "unban":
                        if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                            if len(msg.mentions) > 0:
                                for member in msg.mentions:
                                    if not msg.channel.id in bot.market.tags["__tagban__"]:
                                        bot.market.tags["__tagban__"][msg.channel.id] = []
                                    if not member.id in bot.market.tags["__tagban__"][msg.channel.id]:
                                        bot.market.tags["__tagban__"][msg.channel.id].remove(member.id)
                                        yield from bot.client.send_message(msg.channel, ":label: " + member.name + " is now allowed to use tags in this channel")
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":label: " + member.name + " isn't banned from using tags in this channel")
                            else:
                                yield from bot.client.send_message(msg.channel, ":label: Must mention at least one member!")
                        else:
                            yield from bot.client.send_message(msg.channel, ":label: You don't have permission to use this command!")
                    elif cmd[1] == "delete":
                        tagname = " ".join(cmd[2:])
                        if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                            if msg.channel.id in bot.market.tags and tagname in bot.market.tags[msg.channel.id]:
                                del bot.market.tags[msg.channel.id][tagname]
                                yield from bot.client.send_message(msg.channel, ":label: Deleted tag \"" + tagname + "\"")
                            else:
                                yield from bot.client.send_message(msg.channel, ":label: Couldn't find the tag \"" + tagname + "\"")
                        else:
                            yield from bot.client.send_message(msg.channel, ":label: You don't have permission to use this command!")
                    elif cmd[1].startswith('"'):
                        fullmsg = " ".join(cmd[1:])
                        tagname = fullmsg[1:]
                        tagname = tagname[:tagname.index('"')]
                        if tagname == "ban" or tagname == "unban":
                            yield from bot.client.send_message(msg.channel, ":label: Invalid tag name, cannot be a keyword!")
                        else:
                            fullmsg = fullmsg[len(tagname)+2:]
                            if not msg.channel.id in bot.market.tags:
                                bot.market.tags[msg.channel.id] = {}
                            bot.market.tags[msg.channel.id][tagname] = fullmsg
                            yield from bot.client.send_message(msg.channel, ":label: Set the tag for " + tagname)
                    else:
                        tagname = " ".join(cmd[1:])
                        if msg.channel.id in bot.market.tags and tagname in bot.market.tags[msg.channel.id]:
                            yield from bot.client.send_message(msg.channel, "~" + bot.market.tags[msg.channel.id][tagname])
                        else:
                            yield from bot.client.send_message(msg.channel, ":label: Couldn't find the tag \"" + tagname + "\"")
    except (IndexError, ValueError, KeyError):
        yield from bot.client.send_message(msg.channel, formatting)
        traceback.print_exc()
    except Exception:
        yield from bot.client.send_message(msg.channel, "Something went wrong! Please use " + bot.prefix + "ticket error <message> to send an error report to me!")
        traceback.print_exc()


def util_handle_l(cmd):
    return 1


def setup(bot, help_page, filename):
    bot.register_command("tag", util_handle, util_handle_l)
