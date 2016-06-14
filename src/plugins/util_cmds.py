import traceback, datetime, time, aiohttp, html2text, urllib
from pws import Bing


def google_search(phrase):
    result = Bing.search(phrase, 1, 0)["results"][0]
    return result["link_text"] + "\n\n" + result["link_info"] + "\n\n" + result["link"]


def wiki_search(bot, phrase):
    with aiohttp.Timeout(5):
        url = "https://en.wikipedia.org/wiki/" + phrase.replace(" ", "_")
        result = yield from bot.client.session.get(url)
        if result.status == 200:
            return result.url
        else:
            search_url = "https://en.wikipedia.org/w/index.php?search=" + phrase.replace(" ", "+") + "&title=Special:Search&go=Go&searchToken=dz7an3rnu00g3p1st0nf06p6c"
            result = yield from bot.client.session.get(search_url)
            text = yield from result.text()
            if ".suggestions" in text and ("mw-search-nonefound" in text or "mw-search-result-heading" not in text):
                return None
            elif ".suggestions" not in text:
                return result.url
            else:
                index = text.find("mw-search-result-heading")
                index_s = text.find("href", index+1) + 6
                index_e = text.find('"', index_s)
                print(str(index_s) + ": % :" + str(index_e))
                return "https://en.wikipedia.org" + text[index_s:index_e]
    return None


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
                else:
                    if msg.channel.id in bot.market.settings["motd"]:
                        yield from bot.client.send_message(msg.channel, bot.market.settings["motd"][msg.channel.id])
                    else:
                        yield from bot.client.send_message(msg.channel, "MOTD hasn't been set!")
            elif cmd[0] == "news":
                formatting = bot.prefix + "news create|delete|sub|subch|read|post"
                if cmd[1] == "create":
                    formatting = bot.prefix + "news create [name]"
                    if len(cmd) > 3:
                        yield from bot.client.send_message(msg.channel, "News station names can only be one word long!")
                    else:
                        name = cmd[2].lower()
                        if name not in bot.market.news:
                            bot.market.news[name] = {
                                "authors": {
                                    msg.author.id: {
                                        "name": msg.author.name,
                                        "creator": True
                                    }
                                },
                                "name": name,
                                "history": [],
                                "user_subs": [],
                                "channel_subs": []
                            }
                            yield from bot.client.send_message(msg.channel, "Created new news station, '" + name + "'")
                        else:
                            yield from bot.client.send_message(msg.channel, name + " is already taken! sorry!")
                elif cmd[1] == "edit":
                    formatting = bot.prefix + "news edit [name] add|remove|creator|join author|post"
                    name = cmd[2].lower()
                    if name in bot.market.news:
                        if msg.author.id in bot.market.news[name]["authors"]:
                            if cmd[3] == "add":
                                formatting = bot.prefix + "news edit [name] add author [user]"
                                if cmd[4] == "author":
                                    if bot.market.news[name]["authors"][msg.author.id]["creator"]:
                                        uid = -1
                                        uname = ""
                                        if len(msg.mentions) > 0:
                                            uid = msg.mentions[0].id
                                            uname = msg.mentions[0].name
                                        else:
                                            uid = str(int(cmd[5]))
                                            uname = uid
                                        if uid > 0:
                                            bot.market.news[name]["authors"][id] = {
                                                "name": uname,
                                                "creator": False
                                            }
                                            yield from bot.client.send_message(msg.channel, "Added " + uname + " as an author.")
                                        else:
                                            yield from bot.client.send_message(msg.channel, "Invalid user, must be a user ID or a mention.")
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Only the creator can add authors!")
                                else:
                                    raise IndexError
                            elif cmd[3] == "remove":
                                formatting = bot.prefix + "news edit [name] remove author|post"
                                if cmd[4] == "author":
                                    formatting = bot.prefix + "news edit [name] remove author [user]"
                                    if bot.market.news[name]["authors"][msg.author.id]["creator"]:
                                        uid = -1
                                        uname = ""
                                        if len(msg.mentions) > 0:
                                            uid = msg.mentions[0].id
                                            uname = msg.mentions[0].name
                                        else:
                                            uid = str(int(cmd[5]))
                                            uname = uid
                                        if uid > 0:
                                            if uid in bot.market.news[name]["authors"]:
                                                del bot.market.news[name]["authors"][uid]
                                                yield from bot.client.send_message(msg.channel, uname + " is no longer an author.")
                                            else:
                                                yield from bot.client.send_message(msg.channel, uname + " already isn't an author!")
                                        else:
                                            yield from bot.client.send_message(msg.channel, "Invalid user, must be a user ID or a mention")
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Only the creator can remove authors!")
                                elif cmd[4] == "post":
                                    formatting = bot.prefix + "news edit [name] remove post [index]"
                                    index = int(cmd[5])
                                    if index < len(bot.market.news[name]["history"]):
                                        del bot.market.news[name]["history"][index]
                                        yield from bot.client.send_message(msg.channel, "Deleted post #" + str(index))
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Invalid history index, must be between 0 and " + str(len(bot.market.news[name]["history"])-1))
                                else:
                                    raise IndexError
                            elif cmd[3] == "join":
                                formatting = bot.prefix + "news edit [name] join [index_1] [index_2]"
                                index1 = int(cmd[4])
                                index2 = int(cmd[5])
                                suffix = ""
                                if len(cmd) > 6:
                                    suffix = " ".join(cmd[6:]).replace("\\n", "\n")
                                if index1 < len(bot.market.news[name]["history"]) and index2 < len(bot.market.news[name]["history"]):
                                    app = suffix + bot.market.news[name]["history"][index2]
                                    bot.market.news[name]["history"][index1] += app
                                    del bot.market.news[name]["history"][index2]
                                    yield from bot.client.send_message(msg.channel, "Added post #" + str(index2) + " to the end of post #" + str(index1) + "")
                                else:
                                    yield from bot.client.send_message(msg.channel, "Invalid history index, must be between 0 and " + str(len(bot.market.news[name]["history"]) - 1))
                                formatting = bot.prefix + "news edit [name] creator [user]"
                            elif cmd[3] == "creator":
                                if bot.market.news[name]["authors"][msg.author.id]["creator"]:
                                    uid = -1
                                    uname = ""
                                    if len(msg.mentions) > 0:
                                        uid = msg.mentions[0].id
                                        uname = msg.mentions[0].name
                                    else:
                                        uid = str(int(cmd[4]))
                                        uname = uid
                                    if uid > 0:
                                        if uid in bot.market.news[name]["authors"]:
                                            bot.market.news[name]["authors"][uid]["creator"] = True
                                            bot.market.news[name]["authors"][msg.author.id]["creator"] = False
                                            yield from bot.client.send_message(msg.channel, "Set " + uname + " as the creator")
                                        else:
                                            yield from bot.client.send_message(msg.channel, "Can only transfer creator privileges to another author!")
                                    else:
                                        yield from bot.client.send_message(msg.channel,
                                                                           "Invalid user, must be a user ID or a mention.")
                                else:
                                    yield from bot.client.send_message(msg.channel, "Only the creator can set a new creator!")
                        else:
                            yield from bot.client.send_message(msg.channel, "Only authors of the news station can edit it!")
                    else:
                        yield from bot.client.send_message(msg.channel, "No news station called " + name)
                elif cmd[1] == "sub":
                    formatting = bot.prefix + "news sub [name]"
                    name = cmd[2]
                    if name in bot.market.news:
                        if not msg.author.id in bot.market.news[name]["user_subs"]:
                            bot.market.news[name]["user_subs"].append(msg.author.id)
                            yield from bot.client.send_message(msg.channel, "Subscribed to " + name + ", to unsubscribe use " + bot.prefix + "news unsub " + name)
                        else:
                            yield from bot.client.send_message(msg.channel, "You're already subscribed to " + name + " use " + bot.prefix + "news unsub " + name + " to unsubscribe.")
                    else:
                        yield from bot.client.send_message(msg.channel, "No news station called " + name)
                elif cmd[1] == "unsub":
                    formatting = bot.prefix + "news unsub [name]"
                    name = cmd[2]
                    if name in bot.market.news:
                        if msg.author.id in bot.market.news[name]["user_subs"]:
                            bot.market.news[name]["user_subs"].remove(msg.author.id)
                            yield from bot.client.send_message(msg.channel,
                                                               "Unsubscribed from " + name + ", to subscribe use " + bot.prefix + "news sub " + name)
                        else:
                            yield from bot.client.send_message(msg.channel,
                                                               "You're not subscribed to " + name + " use " + bot.prefix + "news sub " + name + " to subscribe.")
                    else:
                        yield from bot.client.send_message(msg.channel, "No news station called " + name)
                elif cmd[1] == "subch":
                    formatting = bot.prefix + "news subch [name]"
                    if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                        name = cmd[2]
                        if name in bot.market.news:
                            if not msg.channel.id in bot.market.news[name]["channel_subs"]:
                                bot.market.news[name]["channel_subs"].append(msg.channel.id)
                                yield from bot.client.send_message(msg.channel,
                                                                   "Subscribed this channel to " + name + ", to unsubscribe use " + bot.prefix + "news unsubch " + name)
                            else:
                                yield from bot.client.send_message(msg.channel,
                                                                   "This channel is already subscribed to " + name + " use " + bot.prefix + "news unsubch " + name + " to unsubscribe.")
                        else:
                            yield from bot.client.send_message(msg.channel, "No news station called " + name)
                    else:
                        yield from bot.client.send_message(msg.channel, "You don't have permission to use this command!")
                elif cmd[1] == "unsubch":
                    formatting = bot.prefix + "news unsubch [name]"
                    if bot.is_me(msg) or msg.channel.permissions_for(msg.author).manage_messages:
                        name = cmd[2]
                        if name in bot.market.news:
                            if msg.channel.id in bot.market.news[name]["channel_subs"]:
                                bot.market.news[name]["channel_subs"].remove(msg.channel.id)
                                yield from bot.client.send_message(msg.channel,
                                                                   "Unsubscribed this channel from " + name + ", to subscribe use " + bot.prefix + "news subch " + name)
                            else:
                                yield from bot.client.send_message(msg.channel,
                                                                   "This channel isn't subscribed to " + name + " use " + bot.prefix + "news subch " + name + " to subscribe.")
                        else:
                            yield from bot.client.send_message(msg.channel, "No news station called " + name)
                    else:
                        yield from bot.client.send_message(msg.channel, "You don't have permission to use this command!")
                elif cmd[1] == "read":
                    formatting = bot.prefix + "news read [name] last|[index] [amount]"
                    name = cmd[2]
                    if name in bot.market.news:
                        if len(bot.market.news[name]["history"]) == 0:
                            yield from bot.client.send_message(msg.channel, "There isn't any news on this station yet!")
                        else:
                            start = 0
                            end = 1
                            if len(cmd) > 3:
                                if cmd[3] == "last":
                                    end = int(cmd[4])
                                    if end <= 0 or end > 5:
                                        yield from bot.client.send_message(msg.channel, "Invalid amount, can only show up to 5 pages at once.")
                                        return
                                else:
                                    start = int(cmd[3]) - 1
                                    end = start + 1
                            history = bot.market.news[name]["history"]
                            if 0 <= start < len(history) and 0 <= end <= len(history):
                                if end > start+1:
                                    for index in range(start, end):
                                        yield from bot.client.send_message(msg.channel, "\nPage " + str(index+1) + " of " + str(len(history)) + "\n\n" + history[index] + "\n")
                                else:
                                    yield from bot.client.send_message(msg.channel, history[start])
                            else:
                                yield from bot.client.send_message(msg.channel, "Invalid page number, must be between 1 and " + str(len(history)))
                    else:
                        yield from bot.client.send_message(msg.channel, "No news station called " + name)
                elif cmd[1] == "post":
                    formatting = bot.prefix + "news post [name] [post]"
                    name = cmd[2]
                    if name in bot.market.news:
                        if msg.author.id in bot.market.news[name]["authors"]:
                            post = " ".join(cmd[3:])
                            bot.market.news[name]["history"] = [post] + bot.market.news[name]["history"]
                            usub_post = "New post from " + name + ": (use '%p%news unsub " + name + "' to unsubscribe)\n\n" + post
                            for user in bot.market.news[name]["user_subs"]:
                                for server in bot.client.servers:
                                    mem = server.get_member(user)
                                    if mem is not None:
                                        yield from bot.client.send_message(mem, usub_post.replace("%p%", "m$"))
                                        break
                            for chid in bot.market.news[name]["channel_subs"]:
                                for server in bot.client.servers:
                                    channel = server.get_channel(chid)
                                    if channel is not None:
                                        yield from bot.client.send_message(channel, usub_post.replace("%p%", bot.market.get_prefix(bot, channel, by_channel=True)))
                                        break
                            yield from bot.client.send_message(msg.channel, "Created a new news post!")
                        else:
                            yield from bot.client.send_message(msg.channel, "Only an author can post on a news station!")
                    else:
                        yield from bot.client.send_message(msg.channel, "No news station called " + name)
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
            elif cmd[0] == "search":
                yield from bot.client.send_message(msg.channel, google_search(" ".join(cmd[1:])))
            elif cmd[0] == "wiki":
                result = yield from wiki_search(bot, " ".join(cmd[1:]))
                if result is not None:
                    yield from bot.client.send_message(msg.channel, result)
                else:
                    yield from bot.client.send_message(msg.channel, "Couldn't find any wiki pages even vaguely matching that...")
            elif cmd[0] == "erate":
                if cmd[1] == "bind":
                    formatting = bot.prefix + "erate bind [bind] [currency]"
                    if msg.channel.id not in bot.market.settings["erate"]:
                        bot.market.settings["erate"][msg.channel.id] = {}
                    bot.market.settings["erate"][msg.channel.id][cmd[2].upper()] = cmd[3].upper()
                    yield from bot.client.send_message(msg.channel, cmd[2].upper() + " is now bound to " + cmd[3].upper() + " (for this channel only)")
                else:
                    formatting = bot.prefix + "erate [currency_1] [currency_2]"
                    currency1 = bot.market.get_erate_bind(msg.channel.id, cmd[1].upper())
                    currency2 = bot.market.get_erate_bind(msg.channel.id, cmd[2].upper())
                    if len(currency1) == 3 and len(currency2) == 3:
                        with aiohttp.Timeout(10):
                            response = yield from bot.client.session.get("https://api.kraken.com/0/public/Spread?pair=" + currency1 + currency2)
                            data = yield from response.json()
                            if "error" in data and "result" in data and "last" in data["result"]:
                                if len(data["error"]) == 0:
                                    lookup = data["result"]["last"]
                                    for key in data["result"]:
                                        if key != "last":
                                            for obj in data["result"][key]:
                                                if obj[0] == lookup:
                                                    yield from bot.client.send_message(msg.channel, "1 " + str(currency1) + " is worth around " + str(obj[2]) + " " + str(currency2))
                                                    return
                                    yield from bot.client.send_message(msg.channel, "Failed to find an exchange rate for those currencies, please try again later!")
                                else:
                                    yield from bot.client.send_message(msg.channel, "Encountered error: ```\n" + "\n".join(data["error"]) + "\n```")
                            else:
                                yield from bot.client.send_message(msg.channel, "Uh oh, something went wrong.")
                                print(data)
                    else:
                        yield from bot.client.send_message(msg.channel, "Currencies must be a bind or 3 letters long")
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
    bot.register_command("search", util_handle, util_handle_l)
    bot.register_command("wiki", util_handle, util_handle_l)
    bot.register_command("news", util_handle, util_handle_l)
    bot.register_command("erate", util_handle, util_handle_l)