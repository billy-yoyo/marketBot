import market, time, math, traceback, asyncio
from os import listdir
from os.path import isfile, join

def is_me(msg):
    return msg.author.id == "141964149356888064"

def join_arr(prefix, arr, suffix, start=0, end=-1):
    if end < 0:
        end = end + 1 + len(arr)
    if start < 0:
        start = start + 1 + len(arr)
    result = ""
    for i in range(start, end):
        result += prefix + arr[i] + suffix
    return result

def market_handle(bot, msg, cmd):
    formatting = bot.prefix + "help to see help!"
    try:
        if cmd[0] == "market" or cmd[0] == "arket":
            if cmd[1] == "price":
                formatting = bot.prefix + "market price buying|selling [item|amount] [item] - gets the current market price for buying or selling an item"
                req_type = cmd[2]
                if req_type == "buying" or req_type == "selling":
                    item = cmd[3]
                    if len(cmd) == 4:
                        formatting = bot.prefix + "market price buying|selling [item] - gets the lowest price on the market for that item"
                        price = bot.market.get_market_min_price(item)
                        if req_type == "selling":
                            bot.market.get_offer_min_price(item)
                        if price < 0:
                            if req_type == "selling":
                                yield from bot.client.send_message(msg.channel, ":package: Nobody is currently asking to buy **" + item + "**!")
                            else:
                                yield from bot.client.send_message(msg.channel, ":package: There is no **" + item + "** being sold on the market!")
                        else:
                            toggle_word = "price"
                            if req_type == "selling":
                                toggle_word = "offer"
                            yield from bot.client.send_message(msg.channel, ":package: The minimum " + toggle_word + " for **" + item + "** is currently **$" + str(price) + "**")
                    else:
                        formatting = bot.prefix + "market price buying|selling [amount] [item] - gets the current market price for buying that amount of that item"
                        amount = int(cmd[3])
                        item = cmd[4]
                        price = 0
                        if req_type == "buying":
                            price = bot.market.get_market_price(item, amount)
                        else:
                            price = bot.market.get_offer_price(item, amount)
                        if price < 0:
                            if req_type == "selling":
                                yield from bot.client.send_message(msg.channel, ":package: Could not find market price, not enough people buying **" + item + "**")
                            else:
                                yield from bot.client.send_message(msg.channel, ":package: Could not find market price, there isn't enough **" + item + "** on sale!")
                        else:
                            toggle_word = "cost"
                            if req_type == "selling":
                                toggle_word = "get"
                            yield from bot.client.send_message(msg.channel, ":package: **" + str(amount) + " " + item + "** would " + toggle_word + " you **$" + str(price) + "**")
            elif cmd[1] == "sell":
                formatting = bot.prefix + "market sell [amount] [item] [price]"
                item_name = cmd[3]
                amount = int(cmd[2])
                price = int(cmd[4].replace("$", ""))
                if price < 0:
                    yield from bot.client.send_message(msg.channel, ":package: Cannot sell items for a negative price!")
                else:
                    if bot.market.sell_item(msg.author.id, item_name, amount, price) != -1:
                        yield from bot.client.send_message(msg.channel, ":package: Put **" + str(amount) + " " + item_name + "** for sale at a price of **$" + str(price) + "** per unit, total price: **$" + str(amount*price) + "**")
                    else:
                        yield from bot.client.send_message(msg.channel, ":package: You don't have enough **" + item_name + "**!")
            elif cmd[1] == "buy":
                formatting = bot.prefix + "market buy [amount] [item]"
                item_name = cmd[3]
                amount = int(cmd[2])
                result = bot.market.buy_item(msg.author.id, item_name, amount)
                if result[0] == market.Market.BUY_SUCCESS:
                    yield from bot.client.send_message(msg.channel, ":package: Success! You bough **" + str(amount) + " " + item_name + "** for **$" + str(result[1]) + "**")
                elif result[0] == market.Market.BUY_NO_SUCH_ITEM:
                    yield from bot.client.send_message(msg.channel, ":package: Failed! **" + item_name + "** isn't being sold on the market right now!")
                elif result[0] == market.Market.BUY_NOT_ENOUGH_ITEM:
                    yield from bot.client.send_message(msg.channel, ":package: Failed! There is not enough **" + item_name + "** on the market right now!")
                elif result[0] == market.Market.BUY_NOT_ENOUGH_MONEY:
                    yield from bot.client.send_message(msg.channel, ":package: Failed! You don't have enough money to buy **" + str(amount) + " " + item_name + "** (currently costs **$" + str(result[1]) + "**)")
            elif cmd[1] == "offer":
                formatting = bot.prefix + "market offer [amount] [item] [price]"
                item_name = cmd[3]
                amount = int(cmd[2])
                price = int(cmd[4].replace("$", ""))
                if price < 0:
                    yield from bot.client.send_message(msg.channel, ":package: Cannot ask for items at a negative price!")
                else:
                    if bot.market.offer_price(msg.author.id, item_name, amount, price) != -1:
                        yield from bot.client.send_message(msg.channel, ":package: You put an offer of **" + str(amount) + " " + item_name + "** at **$" + str(price) + "** per unit on the market (charged **$" + str(amount*price) + "** as a maximum investment)")
                    else:
                        yield from bot.client.send_message(msg.channel, ":package: You don't have enough money to ask for **" + str(amount) + " " + item_name + "** (would cost a maximum of **$" + str(amount*price) + "**)")
            elif cmd[1] == "amount":
                formatting = bot.prefix + "market amount selling|buying <item> [price] [exact]"
                item_name = cmd[3]
                price = -1
                exact = False
                extra_msg = ""
                if len(cmd) > 4:
                    price = int(cmd[4].replace("$", ""))
                    extra_msg = "at or below **$" + str(price) + "**"
                    if len(cmd) > 5:
                        exact = (cmd[5].lower() == "true" or cmd[5].lower == "yes" or cmd[5] == 1)
                        if exact:
                            extra_msg = "at exactly **$" + str(price) + "**"
                if cmd[2] == "selling":
                    yield from bot.client.send_message(msg.channel, ":package: There is currently **" + str(bot.market.get_market_amount(item_name, price, exact)) + " " + item_name + "** being sold " + extra_msg)
                elif cmd[2] == "buying":
                    yield from bot.client.send_message(msg.channel, ":package: There is currently **" + str(bot.market.get_offer_amount(item_name, price, exact)) + " " + item_name + "** being bought " + extra_msg)
                else:
                    yield from bot.client.send_message(msg.channel, formatting)
            elif cmd[1] == "my" or cmd[1].startswith("<") or market.is_number(cmd[1]):
                user_id = msg.author.id
                user_msg_name = "Your"
                changed = False
                if cmd[1].startswith("<"):
                    user_id = cmd[1][2:-1]
                    changed = True
                elif cmd[1] != "my":
                    user_id = cmd[1]
                    changed = True
                if (changed and is_me(msg)) or not changed:
                    if changed:
                        if len(msg.mentions) > 0:
                            user_msg_name = msg.mentions[0].name + "'s"
                        else:
                            if bot.lookup_enabled:
                                for server in bot.client.servers:
                                    for member in server.members:
                                        if member.id == user_id:
                                            user_msg_name = member.name + "'s"
                            if user_msg_name == "Your":
                                user_msg_name = user_id + "'s"
                    formatting = bot.prefix + "market my offers|sales [page]|get|remove [id]"
                    if cmd[2] == "offers":
                        formatting = bot.prefix + "market my offers [page]|remove|get [item|id] [page]"
                        if len(cmd) > 3 and cmd[3] == "remove":
                            formatting = bot.prefix + "market my offers remove [id]"
                            offer_id = int(cmd[4])
                            offers = bot.market.get_offer_list(user_id, offer_id)
                            if offer_id < len(offers):
                                offer = offers[offer_id]
                                if bot.market.cancel_offer(offer):
                                    yield from bot.client.send_message(msg.channel, ":package: " + user_msg_name + " offer successfully removed from the market")
                                else:
                                    yield from bot.client.send_message(msg.channel, ":package: " + user_msg_name + " offer was not found on the market!")
                                offers.remove(offer)
                            else:
                                yield from bot.client.send_message(msg.channel, ":package: Invalid offer id (do my offers get [item] to generate an offers list)")
                        else:
                            formatting = bot.prefix + "market my offers [page]|get [item] [page]"
                            page = 0
                            item_name = None
                            offer_list = None
                            if len(cmd) > 3 and cmd[3] == "get":
                                formatting = bot.prefix + "market my offers get [item] [page]"
                                item_name = None
                                if len(cmd) > 4:
                                    item_name = cmd[4]
                                    if len(cmd) > 5:
                                        page = int(cmd[5])
                                offer_list = bot.market.find_offer_list(user_id, item_name)
                            else:
                                formatting = bot.prefix + "market my offers [page]"
                                if len(cmd) > 3:
                                    page = int(cmd[3])
                            if offer_list is None:
                                offer_list = bot.market.get_offer_list(user_id, item_name)
                            lines = ":package: " + user_msg_name + " offers: \n"
                            start = 0
                            end = -1
                            if len(offer_list) > bot.pages:
                                start = page * bot.pages
                                if start >= len(offer_list) or page < 0:
                                    yield from bot.client.send_message(msg.channel, ":package: Invalid page!")
                                    return
                                else:
                                    end = min(len(offer_list), start + bot.pages)
                            lines += join_arr("         **>>**  ", list(reversed(market.Market.stringify("offer", offer_list))), "\n", start=start, end=end)
                            yield from bot.client.send_message(msg.channel, lines)
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[1] == "refresh":
                for item in bot.market.market:
                    if not item.startswith("_"):
                        bot.market.calculate_market_amount(item)
                        bot.market.calculate_market_min_price(item)
                for item in bot.market.offers:
                    if not item.startswith("_"):
                        bot.market.calculate_offer_amount(item)
                        bot.market.calculate_offer_min_price(item)
                yield from bot.client.send_message(msg.channel, ":package: Refreshed market!")
            else:
                raise IndexError
        elif cmd[0] == "restart":
            if is_me(msg):
                yield from bot.client.send_message(msg.channel, ">>> Restarting <<<")
                print("Performing full restart!")
                bot.market.save()
                print("saved state...")
                bot.market.close()
                print("closed market...")
                yield from bot.client.close()
                #bot.call_restart(msg)
            else:
                yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
        elif cmd[0] == "save":
            yield from bot.client.send_message(msg.channel, ">>> Restarting <<<")
            bot.market.save()
        elif cmd[0] == "admin":
            formatting = bot.prefix + "admin <command> - run an admin command"
            if is_me(msg):
                command = " ".join(cmd[1:])
                for mention in msg.mentions:
                    command = command.replace("<@" + mention.id + ">", '"' + mention.id + '"')
                eval(command)
                yield from bot.client.send_message(msg.channel, "Successfully executed command.")
            else:
                yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
        elif cmd[0] == "balance":
            if len(cmd) > 1 and cmd[1] == "history":
                formatting = bot.prefix + "balance history [page]"
                user_id = msg.author.id
                user_msg_name = "Your"
                ok = True
                if len(msg.mentions) > 0:
                    if is_me(msg):
                        user_id = msg.mentions[0].id
                        user_msg_name = msg.mentions[0].name + "'s"
                    else:
                        ok = False
                elif len(cmd) > 3:
                    if is_me(msg):
                        user_id = cmd[3]
                        if bot.lookup_enabled:
                            for server in bot.client.servers:
                                for member in server.members:
                                    if member.id == user_id:
                                        user_msg_name = member.name + "'s"
                        if user_msg_name == "Your":
                            user_msg_name = user_id + "'s"
                    else:
                        ok = False
                if ok:
                    page = 0
                    if len(cmd) > 2:
                        page = int(cmd[2]) - 1
                    history = bot.market.get_transations(user_id)
                    lines = ":atm: " + user_msg_name + " transaction history (page " + str(page+1) + " of " + str(math.ceil(len(history)/bot.pages)) + "): \n"
                    start = 0
                    end = -1
                    if len(history) > bot.pages:
                        start = page * bot.pages
                        if start >= len(history) or page < 0:
                            yield from bot.client.send_message(msg.channel, ":atm: Invalid page!")
                            return
                        else:
                            end = min(len(history), start + bot.pages)
                    lines += join_arr("         **>>**  ", list(reversed(history)), "\n", start=start, end=end)
                    yield from bot.client.send_message(msg.channel, lines)
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            else:
                formatting = bot.prefix + "balance - display your balance"
                user_id = msg.author.id
                user_msg_name = "Your"
                ok = True
                if len(msg.mentions) > 0:
                    if is_me(msg):
                        user_id = msg.mentions[0].id
                        user_msg_name = msg.mentions[0].name + "'s"
                    else:
                        ok = False
                elif len(cmd) > 1:
                    if is_me(msg):
                        user_id = cmd[1]
                        if bot.lookup_enabled:
                            for server in bot.client.servers:
                                for member in server.members:
                                    if member.id == user_id:
                                        user_msg_name = member.name + "'s"
                        if user_msg_name == "Your":
                            user_msg_name = user_id + "'s"
                    else:
                        ok = False
                if ok:
                    yield from bot.client.send_message(msg.channel, ":atm: " + user_msg_name + " balance is **$" + str(bot.market.get_money(user_id)) + "**")
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
        elif cmd[0] == "inv" or cmd[0] == "inventory":
            formatting = "inv [item]"
            user_id = msg.author.id
            user_msg_name = "Your"
            changed = False
            if len(msg.mentions) > 0:
                user_id = msg.mentions[0].id
                user_msg_name = msg.mentions[0].name + "'s"
                changed = True
            elif market.is_number(cmd[-1]):
                user_id = cmd[-1]
                if bot.lookup_enabled:
                    for server in bot.client.servers:
                        for member in server.members:
                            if member.id == user_id:
                                user_msg_name = member.name + "'s"
                if user_msg_name == "Your":
                    user_msg_name = user_id + "'s"
                changed = True
            if (changed and is_me(msg)) or not changed:
                formatting = bot.prefix + "inv [item] - shows the amount of that item you have, or what items you have if no item given"
                if len(cmd) == 1 or cmd[1].startswith("<") or market.is_number(cmd[1]):
                    formatting = bot.prefix + "inv - shows how much of that item you have"
                    yield from bot.client.send_message(msg.channel, ":package: " + user_msg_name + " inventory contains: ** " + "**, **".join(bot.market.get_inventory_items(user_id)) + " **")
                else:
                    formatting = bot.prefix + "inv [item] - shows what items are in your inventory"
                    itemname = " ".join(cmd[1:]).replace(" <@" + user_id + ">", "")
                    yield from bot.client.send_message(msg.channel, ":package: " + user_msg_name + " inventory contains **" + str(bot.market.get_inventory(user_id, itemname)) + " " + itemname + "**")
            else:
                yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
        elif cmd[0] == "backup":
            formatting = "backup load|save|list [backup_name] - commands for backing up the market data"
            if is_me(msg):
                if len(cmd) >= 3 or cmd[1] == "list":
                    if cmd[1] == "load":
                        formatting = bot.prefix + "backup load [backup_name] - load the backup, see " + bot.prefix + "backup list for a list of backups"
                        backup_name = " ".join(cmd[2:])
                        bot.market.load_backup(backup_name)
                        yield from bot.client.send_message(msg.channel, ":floppy_disk: Loaded back up, check console for information.")
                    elif cmd[1] == "save":
                        formatting = bot.prefix + "backup save [backup_name] - save the current data to a backup with that name"
                        backup_name = " ".join(cmd[2:])
                        bot.market.save_backup(backup_name)
                        yield from bot.client.send_message(msg.channel, ":floppy_disk: Backed up, check console for information.")
                    elif cmd[1] == "list":
                        formatting = bot.prefix + "backup list - list all the known backups"
                        onlyfiles = [f for f in listdir("data/") if not isfile(join("data/", f))]
                        yield from bot.client.send_message(msg.channel, ":floppy_disk: Backups: " + ", ".join(onlyfiles))
                else:
                    yield from bot.client.send_message(msg.channel, ":floppy_disk: Please give a backup name!")
            else:
                yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
        elif cmd[0] == "ping":
            formatting = bot.prefix + "ping - shows the bots ping to the server"
            bot.ping_start = time.time()
            yield from bot.client.send_message(msg.channel, bot.ping_message)
        elif cmd[0] == "lookup" or cmd[0] == "lookup_all":
            formatting = bot.prefix + "lookup user|id|name|nick <search>"
            if is_me(msg):
                find_all = False
                find_str = cmd[2]
                if cmd[-1] == "all":
                    find_all = True
                if cmd[1] == "server":
                    if cmd[2] == "name":
                        if find_all:
                            find_str = " ".join(cmd[3:])
                        else:
                            find_str = " ".join(cmd[3:-1])
                    else:
                        find_str = cmd[3]
                else:
                    if cmd[1] == "name" or cmd[1] == "nick" or cmd[1] == "user":
                        if len(msg.mentions) > 0:
                            if cmd[1].lower() == "nick":
                                find_str = msg.mentions[0].nick
                            else:
                                find_str = msg.mentions[0].name
                        else:
                            if find_all:
                                find_str = " ".join(cmd[2:-1])
                            else:
                                find_str = " ".join(cmd[2:])

                result = []
                for server in bot.client.servers:
                    if cmd[1] == "server" and ((cmd[2] == "name" and find_str in server.name) or (cmd[2] == "id" and server.id == find_str)):
                        result.append(" name: " + server.name + "\n id: " + server.id)
                    else:
                        for member in server.members:
                            if (member.id == find_str and cmd[1] == "id") or (member.nick is not None and find_str in member.nick and (cmd[1] == "nick" or cmd[1] == "user")) or (find_str in member.name and (cmd[1] == "name" or cmd[1] == "user")):
                                next_result = " name: " + member.name + " (" + member.id + ")\n found in server: " + server.name + " (" + server.id + ")"
                                if hasattr(member, "nick"):
                                    if member.nick is not None:
                                        next_result = "name: " + member.name + " (" + member.id + ")\n nickname: " + member.nick + "\n found in server: " + server.name + " (" + server.id + ")"
                                result.append(next_result)
                                if not find_all:
                                    break
                if result is not None:
                    if len(result) > 15:
                        if cmd[0] == "lookup":
                            yield from bot.client.send_message(msg.channel, "Too many results, only showing first 15: \n ```" + "\n \n".join(result[:15]) + "```")
                        elif cmd[0] == "lookup_all":
                            for i in range(math.ceil(len(result)/15)):
                                from_id = i*15
                                to_id = min((i+1)*15, len(result))
                                yield from bot.client.send_message(msg.channel, "Lookup results [" + str(from_id) + " to " + str(to_id) + "]: \n ```" + "\n \n".join(result[from_id:to_id]) + "```")
                    else:
                        yield from bot.client.send_message(msg.channel, "Lookup results: \n ```" + "\n \n".join(result) + " ```")
                else:
                    yield from bot.client.send_message(msg.channel, "Lookup failed, couldn't find user with ID " + cmd[1])
            else:
                yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
        elif cmd[0] == "trade":
            if cmd[1] == "offer":
                formatting = bot.prefix + "trade offer [user] {your items} for {their items} :: {items} = $money, 30 itemname, ..."
                user_id = cmd[2]
                user_name = cmd[2]
                if cmd[2].startswith("<") and len(msg.mentions) > 0:
                    user_id = msg.mentions[0].id
                    user_name = msg.mentions[0].name
                if market.is_number(user_id):
                    if user_id == msg.author.id:
                        yield from bot.client.send_message(msg.channel, "Can't send a trade offer to yourself!")
                    else:
                        raw_trades = (" ".join(cmd[3:])).split(" for ")
                        raw_trade_from = raw_trades[0].split(",")
                        trade_from = {}
                        for item in raw_trade_from:
                            item_name = None
                            item_value = 0
                            if item.replace(" ", "").startswith("$"):
                                item_name = "$$$"
                                item_value = int(item.replace(" ", "")[1:])
                            else:
                                spl_item = item.split(" ")
                                spl_item[:] = [x for x in spl_item if x != ""]
                                item_value = int(spl_item[0])
                                item_name = " ".join(spl_item[1:])
                            if item_name is not None:
                                if item_name not in trade_from:
                                    trade_from[item_name] = item_value
                                else:
                                    trade_from[item_name] += item_value
                        raw_trade_to = raw_trades[1].split(",")
                        trade_to = {}
                        for item in raw_trade_to:
                            item_name = None
                            item_value = 0
                            if item.replace(" ", "").startswith("$"):
                                item_name = "$$$"
                                item_value = int(item.replace(" ", "")[1:])
                            else:
                                spl_item = item.split(" ")
                                spl_item[:] = [x for x in spl_item if x != ""]
                                item_value = int(spl_item[0])
                                item_name = " ".join(spl_item[1:])
                            if item_name is not None:
                                if item_name not in trade_to:
                                    trade_to[item_name] = item_value
                                else:
                                    trade_to[item_name] += item_value
                        result = bot.market.create_trade_offer(msg.author.id, msg.author.name, user_id, user_name, trade_from, trade_to)
                        if result == market.Market.TRADE_SUCCESS:
                             yield from bot.client.send_message(msg.channel, "Sent trade offer!")
                        elif result == market.Market.TRADE_ALREADY_EXISTS:
                            yield from bot.client.send_message(msg.channel, "Trade failed as you already have a pending offer to " + user_name)
                        elif result == market.Market.TRADE_FROM_NOT_ENOUGH_ITEM:
                            yield from bot.client.send_message(msg.channel, "Trade failed because you don't have enough of an item to fulfill the trade!")
                        elif result == market.Market.TRADE_FROM_NOT_ENOUGH_MONEY:
                            yield from bot.client.send_message(msg.channel, "Trade failed because you don't have enough money to fulfill the trade!")
                        elif result == market.Market.TRADE_TO_NOT_ENOUGH_ITEM:
                            yield from bot.client.send_message(msg.channel, "Trade failed because " + user_name + " doesn't have enough of an item to fulfill the trade!")
                        elif result == market.Market.TRADE_TO_NOT_ENOUGH_MONEY:
                            yield from bot.client.send_message(msg.channel, "Trade failed because " + user_name + " doesn't have enough money to fulfill the trade!")
                        else:
                            yield from bot.client.send_message(msg.channel, "Trade failed with an unspecified error " + str(result))
                else:
                    yield from bot.client.send_message(msg.channel, "Invalid user, must be a mention or a user ID")
            elif cmd[1] == "my" or cmd[1].startswith("<") or market.is_number(cmd[1]):
                formatting = bot.prefix + "trade my sent|received [user]"
                user_id = msg.author.id
                user_msg_name = "Your"
                changed = False
                if cmd[1].startswith("<"):
                    user_id = cmd[1][2:-1]
                    changed = True
                elif cmd[1] != "my":
                    user_id = cmd[1]
                    changed = True
                if (changed and is_me(msg)) or not changed:
                    if changed:
                        if len(msg.mentions) > 0:
                            user_msg_name = msg.mentions[0].name
                        else:
                            if bot.lookup_enabled:
                                for server in bot.client.servers:
                                    for member in server.members:
                                        if member.id == user_id:
                                            user_msg_name = member.name
                            if user_msg_name == "Your":
                                user_msg_name = user_id
                    if cmd[2] == "sent":
                        formatting = bot.prefix + "trade my sent [user]"
                        if len(cmd) == 3: # list sent offers
                            result = bot.market.get_trades_from(user_id)
                            if len(result) > 0:
                                if user_msg_name == "Your":
                                    yield from bot.client.send_message(msg.channel, "You have sent trade offers to " + ", ".join(result))
                                else:
                                    yield from bot.client.send_message(msg.channel, user_msg_name + " has sent trade offers to " + ", ".join(result))
                            else:
                                if user_msg_name == "Your":
                                    yield from bot.client.send_message(msg.channel, "You haven't sent any trade offers!")
                                else:
                                    yield from bot.client.send_message(msg.channel, user_msg_name + " hasn't sent any trade offers!")
                        else:
                            print("hi")
                            user_id = cmd[3]
                            if user_id.startswith("<") and len(msg.mentions) > 0:
                                user_id = msg.mentions[0].id
                            if market.is_number(user_id):
                                print("test")
                                trade = bot.market.get_trade(msg.author.id, user_id)
                                print("yay?")
                                if trade is not None:
                                    yield from bot.client.send_message(msg.channel, market.Market.stringify("trade", trade))
                                else:
                                    yield from bot.client.send_message(msg.channel, "Couldn't find a trade offer.")
                            else:
                                yield from bot.client.send_message(msg.channel, "Invalid user, use a mention or a user ID")
                    elif cmd[2] == "received" or cmd[2] == "recieved":
                        formatting = bot.prefix + "trade my received [user]"
                        if len(cmd) == 3:
                            result = bot.market.get_trades_to(user_id)
                            if len(result) > 0:
                                if user_msg_name == "Your":
                                    yield from bot.client.send_message(msg.channel, "You have pending trade offers from " + ", ".join(result))
                                else:
                                    yield from bot.client.send_message(msg.channel, user_msg_name + " has pending trade offers from " + ", ".join(result))
                            else:
                                if user_msg_name == "Your":
                                    yield from bot.client.send_message(msg.channel, "You don't have any trade offers!")
                                else:
                                    yield from bot.client.send_message(msg.channel, user_msg_name + " doesn't have any trade offers!")
                        else:
                            user_id = cmd[3]
                            if user_id.startswith("<") and len(msg.mentions) > 0:
                                user_id = msg.mentions[0].id
                            if market.is_number(user_id):
                                trade = bot.market.get_trade(user_id, msg.author.id)
                                if trade is not None:
                                    yield from bot.client.send_message(msg.channel, bot.market.stringify("trade", trade))
                                else:
                                    yield from bot.client.send_message(msg.channel, "Couldn't find a trade offer.")
                            else:
                                yield from bot.client.send_message(msg.channel, "Invalid user, use a mention or a user ID")
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[1] == "accept":
                formatting = bot.prefix + "trade accept [user]"
                user_id = cmd[3]
                if user_id.startswith("<") and len(msg.mentions) > 0:
                    user_id = msg.mentions[0].id
                if market.is_number(user_id):
                    result_raw = bot.market.accept_trade(user_id, msg.author.id)
                    result = result_raw[0]
                    trade = result_raw[1]
                    if result == market.Market.TRADE_SUCCESS:
                        yield from bot.client.send_message(msg.channel, "Accepted trade: \n" + market.Market.stringify("trade", trade))
                    elif result == market.Market.TRADE_DOESNT_EXIST:
                        yield from bot.client.send_message(msg.channel, "You don't have any pending trade offers from " + trade["from_name"])
                    elif result == market.Market.TRADE_TO_NOT_ENOUGH_ITEM:
                        yield from bot.client.send_message(msg.channel, "Trade failed because you don't have enough of an item to fulfill the trade!")
                    elif result == market.Market.TRADE_TO_NOT_ENOUGH_MONEY:
                        yield from bot.client.send_message(msg.channel, "Trade failed because you don't have enough money to fulfill the trade!")
                    elif result == market.Market.TRADE_FROM_NOT_ENOUGH_ITEM:
                        yield from bot.client.send_message(msg.channel, "Trade failed because " + trade["from_name"] + " doesn't have enough of an item to fulfill the trade!")
                    elif result == market.Market.TRADE_FROM_NOT_ENOUGH_MONEY:
                        yield from bot.client.send_message(msg.channel, "Trade failed because " + trade["from_name"] + " doesn't have enough money to fulfill the trade!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Trade failed with an unspecified error " + str(result))
                else:
                    yield from bot.client.send_message(msg.channel, "Invalid user, use a mention or a user ID")
            elif cmd[1] == "decline":
                formatting = bot.prefix + "trade decline [user]"
                user_id = cmd[3]
                if user_id.startswith("<") and len(msg.mentions) > 0:
                    user_id = msg.mentions[0].id
                if market.is_number(user_id):
                    result_raw = bot.market.cancel_trade(user_id, msg.author.id)
                    result = result_raw[0]
                    trade = result_raw[1]
                    if result == market.Market.TRADE_SUCCESS:
                        yield from bot.client.send_message(msg.channel, "Declined trade from " + trade["from_name"] + "\n " + market.Market.stringify("trade", trade))
                    elif result == market.Market.TRADE_DOESNT_EXIST:
                        yield from bot.client.send_message(msg.channel, "You don't have any pending trade offers from " + trade["from_name"])
                    else:
                        yield from bot.client.send_message(msg.channel, "Trade failed with an unspecified error " + str(result))
                else:
                    yield from bot.client.send_message(msg.channel, "Invalid user, use a mention or a user ID")
            elif cmd[1] == "cancel":
                formatting = bot.prefix + "trade cancel [user]"
                user_id = cmd[2]
                if user_id.startswith("<") and len(msg.mentions) > 0:
                    user_id = msg.mentions[0].id
                if market.is_number(user_id):
                    result_raw = bot.market.cancel_trade(msg.author.id, user_id)
                    result = result_raw[0]
                    trade = result_raw[1]
                    if result == market.Market.TRADE_SUCCESS:
                        yield from bot.client.send_message(msg.channel, "Cancelled trade to " + trade["to_name"] + "\n " + market.Market.stringify("trade", trade))
                    elif result == market.Market.TRADE_DOESNT_EXIST:
                        yield from bot.client.send_message(msg.channel, "You haven't sent any trade offers to " + trade["to_name"])
                    else:
                        yield from bot.client.send_message(msg.channel, "Trade failed with an unspecified error " + str(result))
                else:
                    yield from bot.client.send_message(msg.channel, "Invalid user, use a mention or a user ID")
            else:
                raise IndexError
        elif cmd[0] == "info":
            lines = [
                "MarketBot is a cookieclicker-esque bot where you produce items in factories",
                "Upgrading these factories with the items you produce or buy from the discord-wide market",
                "Read up fully on how the game works at our github page: https://github.com/billy-yoyo/marketBot/"
                "   **>> " + bot.prefix + "help** for help with commands, or ",
                "   **>>** " + bot.prefix + "join [invite link]** to invite the bot to your server, if no invite given you'll be DM'd one",
                "Some more info: ```",
                " I'm in " + str(len(bot.client.servers)) + " with " + str(len(bot.market.get_registered_users())) + " registered players",
                " I was created by billyoyo, see " + bot.prefix + "ticket to send me a message",
                " ```"
                " Join the MarketBot server: https://discord.gg/013GE1ZeT5ntIaWCW",

            ]
            yield from bot.client.send_message(msg.channel, "\n".join(lines))
        elif cmd[0] == "join":
            yield from bot.client.send_message(msg.channel, "Coming soon (tm)")
        elif cmd[0] == "ticket":
            yield from bot.client.send_message(msg.channel, "Coming soon (tm)")
        else:
            raise IndexError
    except (IndexError, ValueError):
        yield from bot.client.send_message(msg.channel, formatting)
        traceback.print_exc()
    except Exception:
        yield from bot.client.send_message(msg.channel, "Something went wrong! Please use " + bot.prefix + "ticket error <message> to send an error report to me!")
        traceback.print_exc()


def market_handle_l(cmd):
    return 1

def setup(bot, help_page, filename):
    bot.market = market.Market()
    help_page.register("market", "[stuff]", "does market stuff")
    help_page.register("balance", "", "checks your balance")
    help_page.register("inv", "[item]", "tells you have much of an item you have, if no item given tells you what items you have")
    help_page.register("ping", "", "tells you the bots ping to your server.")
    bot.register_command("market", market_handle, market_handle_l)
    bot.register_command("admin", market_handle, market_handle_l)
    bot.register_command("balance", market_handle, market_handle_l)
    bot.register_command("inv", market_handle, market_handle_l)
    bot.register_command("inventory", market_handle, market_handle_l)
    bot.register_command("backup", market_handle, market_handle_l)
    bot.register_command("ping", market_handle, market_handle_l)
    bot.register_command("restart", market_handle, market_handle_l)
    bot.register_command("save", market_handle, market_handle_l)
    bot.register_command("lookup", market_handle, market_handle_l)
    bot.register_command("lookup_all", market_handle, market_handle_l)
    bot.register_command("trade", market_handle, market_handle_l)
    bot.register_command("info", market_handle, market_handle_l)
    bot.register_command("join", market_handle, market_handle_l)
    bot.register_command("ticket", market_handle, market_handle_l)