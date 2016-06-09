import traceback, datetime, time, aiohttp


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
            if cmd[0] == "remindme":
                formatting = bot.prefix + "remindme [message] in [weeks] weeks [days] days [hours] hrs|hours [minutes] mins|minutes [seconds] secs|seconds"
                spl = (" ".join(cmd[1:])).split(" in ")
                delayraw = spl[1].replace(",", "").replace(" and ", " ").split(" ")
                delay = 0
                if len(delayraw) % 2 == 0:
                    for i in range(0, len(delayraw), 2):
                        amt = int(delayraw[i])
                        timetype = delayraw[i+1].lower()
                        if timetype == "hrs" or timetype == "hours" or timetype == "hr" or timetype == "hour":
                            delay += amt * 3600
                        elif timetype == "mins" or timetype == "minutes" or timetype == "min" or timetype == "minute":
                            delay += amt * 60
                        elif timetype == "secs" or timetype == "seconds" or timetype == "sec" or timetype == "second":
                            delay += amt
                        elif timetype == "days" or timetype == "day":
                            delay += amt * 86400
                        elif timetype == "weeks" or timetype == "week":
                            delay += amt * 604800
                    bot.market.add_reminder(msg.author.id, spl[0], delay)
                    yield from bot.client.send_message(msg.channel, "Reminder created.")
                else:
                    yield from bot.client.send_message(msg.channel, "Invalid amount of time, example: 3 hours 10 mins 30 secs")
            elif cmd[0] == "uptime":
                dtstr = ""
                struct = datetime.datetime.fromtimestamp(time.time() - bot.start_time)
                if struct.year > 1970:
                    yrs = struct.year - 1970
                    extra = " " if yrs == 1 else "s "
                    dtstr += "**" + str(yrs) + "** year" + extra
                if struct.month > 1:
                    mths = struct.month - 1
                    extra = " " if mths == 1 else "s "
                    dtstr += "**" + str(mths) + "** month" + extra
                if struct.day > 1:
                    days = struct.day - 1
                    extra = " " if days == 1 else "s "
                    dtstr += "**" + str(days) + "** day" + extra
                if struct.hour > 0:
                    extra = " " if struct.hour == 1 else "s "
                    dtstr += "**" + str(struct.hour) + "** hour" + extra
                if struct.minute > 0:
                    extra = " " if struct.minute == 1 else "s "
                    dtstr += "**" + str(struct.minute) + "** minute" + extra
                if struct.second > 0:
                    extra = "" if struct.second == 1 else "s"
                    dtstr += "**" + str(struct.second) + "** second" + extra
                yield from bot.client.send_message(msg.channel, bot.name + " has been running for " + dtstr)
            elif cmd[0] == "motd":
                if len(cmd) > 1 and cmd[1] == "set":
                    if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                        motd = " ".join(cmd[2:])
                        bot.market.settings["motd"][msg.channel.id] = motd
                        yield from bot.client.send_message(msg.channel, "MOTD set to " + motd)
                    else:
                        yield from bot.client.send_message(msg.channel, "You don't have permission to use this command!")
                if msg.channel.id in bot.market.settings["motd"]:
                    yield from bot.client.send_message(msg.channel, bot.market.settings["motd"][msg.channel.id])
                else:
                    yield from bot.client.send_message(msg.channel, "MOTD hasn't been set!")
            elif cmd[0] == "stats":
                members = 0
                for server in bot.client.servers:
                    members += len(server.members)
                yield from bot.client.send_message(msg.channel, bot.name + " is in **" + str(len(bot.client.servers)) + "** servers, with **" + str(members) + "** members and **" + str(len(bot.market.factories)) + "** registered players!")
            elif cmd[0] == "ud":
                search = "+".join(cmd[1:])
                with aiohttp.Timeout(10):
                    response = yield from bot.client.session.get("http://www.urbandictionary.com/define.php?term=" + search)
                    text = yield from response.text()
                    lines = text.split("\n")
                    result = {
                        "meaning": [],
                        "example": [],
                        "tags": []
                    }
                    related = []
                    next_line = None
                    getting_related = False
                    for line in lines:
                        if getting_related:
                            if next_line is not None:
                                if line == "</li>":
                                    next_line = None
                                elif line.startswith("<a href="):
                                    related.append(line[line.index(">") + 1:-4].replace("<br/>", "").replace("&quot;", '"').replace("&#39;", ""))
                                    if len(related) >= 7:
                                        break
                            elif line == "<li>":
                                next_line = "yes"
                        else:
                            if next_line is not None:
                                if line == "</div>" and next_line != "related":
                                    if next_line == "tags":
                                        next_line = "related"
                                    else:
                                        next_line = None
                                else:
                                    if next_line == "tags":
                                        result["tags"].append(line[line.index(">") + 1:-4].replace("<br/>", "").replace("&quot;", '"').replace("&#39;", ""))
                                    elif next_line == "related":
                                        if line == "Alphabetical List":
                                            getting_related = True
                                            next_line = None
                                    else:
                                        result[next_line].append(line.replace("<br/>", "").replace("&quot;", '"').replace("&#39;", ""))
                            elif line == "<div class='meaning'>":
                                next_line = "meaning"
                            elif line == "<div class='example'>":
                                next_line = "example"
                            elif line == "<div class='tags'>":
                                next_line = "tags"
                    #print(text)
                    print(related)
                    lines = "Top result for \"**" + " ".join(cmd[1:]) + "**\":\n\n"
                    for line in result["meaning"]:
                        lines += "" + line + "\n"
                    lines += "\n"
                    for line in result["example"]:
                        lines += "*" + line + "*\n"
                    #yield from bot.client.send_message(msg.channel, lines)
                    #lines = ""
                    if len(result["tags"]) > 0:
                        lines += "\nTags:** " + "**, **".join(result["tags"]) + " **"
                    lines += "\n\n"
                    lines += "Related words:** " + "**, **".join(related) + " **"
                    yield from bot.client.send_message(msg.channel, lines)

            elif cmd[0] == "tag":
                if is_tag_banned(bot, msg) and not bot.is_me(msg):
                    yield from bot.client.send_message(msg.channel, ":label: You are banned from using tags in this channel!")
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
    bot.register_command("remindme", util_handle, util_handle_l)
    bot.register_command("motd", util_handle, util_handle_l)
    bot.register_command("uptime", util_handle, util_handle_l)
    bot.register_command("ud", util_handle, util_handle_l)
    bot.register_command("stats", util_handle, util_handle_l)