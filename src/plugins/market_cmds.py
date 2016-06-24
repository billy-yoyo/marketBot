import market, time, math, traceback, datetime, asyncio, discord
from os import listdir
from os.path import isfile, join




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
        cd_result = bot.get_cooldown(msg.author.id, cmd)
        if cd_result > 0:
            yield from bot.client.send_message(msg.channel, "That command is on cooldown, please wait another " + str(int(cd_result)) + " seconds before using it")
        else:
            if cmd[0] == "market" or cmd[0] == "arket":
                if cmd[1] == "price":
                    formatting = bot.prefix + "market price buying|selling [item|amount] [item] - gets the current market price for buying or selling an item"
                    req_type = cmd[2]
                    if req_type == "buying" or req_type == "selling":
                        item = cmd[3]
                        if len(cmd) == 4:
                            formatting = bot.prefix + "market price buying|selling [item] - gets the lowest|highest price on the market for that item"
                            price = bot.market.get_market_min_price(item)
                            if req_type == "selling":
                                bot.market.get_offer_min_price(item)
                            if price < 0:
                                if req_type == "selling":
                                    yield from bot.client.send_message(msg.channel, ":package: Nobody is currently asking to buy **" + item + "**!")
                                else:
                                    yield from bot.client.send_message(msg.channel, ":package: There is no **" + item + "** being sold on the market!")
                            else:
                                toggle_word = "minimum price"
                                if req_type == "selling":
                                    toggle_word = "maximum offer"
                                yield from bot.client.send_message(msg.channel, ":package: The " + toggle_word + " for **" + item + "** is currently **$" + str(price) + "**")
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
                        if cmd[2] == "buying":
                            extra_msg = "at or above **$" + str(price) + "**"
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
                    if (changed and bot.is_me(msg)) or not changed:
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
                        elif cmd[2] == "sales":
                            formatting = bot.prefix + "market my sales [page]|remove|get [item|id] [page]"
                            if len(cmd) > 3 and cmd[3] == "remove":
                                formatting = bot.prefix + "market my sales remove [id]"
                                sale_id = int(cmd[4])
                                sales = bot.market.get_offer_list(user_id, sale_id)
                                if sale_id < len(sales):
                                    sale = sales[sale_id]
                                    if bot.market.cancel_sale(sale):
                                        yield from bot.client.send_message(msg.channel, ":package: " + user_msg_name + " sale successfully removed from the market")
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":package: " + user_msg_name + " sale was not found on the market!")
                                    sales.remove(sale)
                                else:
                                    yield from bot.client.send_message(msg.channel, ":package: Invalid offer id (do my offers get [item] to generate an offers list)")
                            else:
                                formatting = bot.prefix + "market my sales [page]|get [item] [page]"
                                page = 0
                                item_name = None
                                sale_list = None
                                if len(cmd) > 3 and cmd[3] == "get":
                                    formatting = bot.prefix + "market my sales get [item] [page]"
                                    item_name = None
                                    if len(cmd) > 4:
                                        item_name = cmd[4]
                                        if len(cmd) > 5:
                                            page = int(cmd[5])
                                    sale_list = bot.market.find_market_list(user_id, item_name)
                                else:
                                    formatting = bot.prefix + "market my sales [page]"
                                    if len(cmd) > 3:
                                        page = int(cmd[3])
                                if sale_list is None:
                                    sale_list = bot.market.get_market_list(user_id, item_name)
                                lines = ":package: " + user_msg_name + " offers: \n"
                                start = 0
                                end = -1
                                if len(sale_list) > bot.pages:
                                    start = page * bot.pages
                                    if start >= len(sale_list) or page < 0:
                                        yield from bot.client.send_message(msg.channel, ":package: Invalid page!")
                                        return
                                    else:
                                        end = min(len(sale_list), start + bot.pages)
                                lines += join_arr("         **>>**  ", list(reversed(market.Market.stringify("sale", sale_list))), "\n", start=start, end=end)
                                yield from bot.client.send_message(msg.channel, lines)
                    else:
                        yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
                elif cmd[1] == "refresh":
                    item = None
                    if len(cmd) > 2:
                        item = cmd[2]
                    if bot.market.refresh(item):
                        yield from bot.client.send_message(msg.channel, ":package: Refreshed market!")
                    else:
                        yield from bot.client.send_message(msg.channel, ":package: Market was refreshed too recently! Please wait until refreshing again")
                else:
                    raise IndexError
            elif cmd[0] == "restart":
                if bot.is_me(msg):
                    yield from bot.client.send_message(msg.channel, "Disfunctional. Do not use.")
                    #yield from bot.client.send_message(msg.channel, ">>> Restarting <<<")
                    #print("Performing full restart!")
                    #bot.market.save()
                    #print("saved state...")
                    #bot.market.close()
                    #print("closed market...")
                    #yield from bot.client.close()
                    #bot.call_restart(msg)
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[0] == "save":
                yield from bot.client.send_message(msg.channel, ">>> Saving <<<")
                bot.market.save()
            elif cmd[0] == "avatar":
                formatting = bot.prefix + "avatar <filename> - set the avatar"
                if bot.is_me(msg):
                    try:
                        f = open("card_img/"+cmd[1], "rb")
                        yield from bot.client.edit_profile(avatar=f.read())
                        f.close()
                        yield from bot.client.send_message(msg.channel, "Avatar changed.")
                    except:
                        traceback.print_exc()
                        yield from bot.client.send_message(msg.channel, "Failed to change avatar.")
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[0] == "admin":
                formatting = bot.prefix + "admin <command> - run an admin command"
                if bot.is_me(msg):
                    commands = " ".join(cmd[1:])
                    for mention in msg.mentions:
                        commands = commands.replace("<@" + mention.id + ">", '"' + mention.id + '"')
                    try:
                        for command in commands.split(";;"):
                            if command.startswith("yield from"):
                                yield from eval(command[10:])
                            else:
                                eval(command)
                        yield from bot.client.send_message(msg.channel, "Successfully executed command.")
                    except:
                        print("[ADMIN COMMAND ERROR]")
                        traceback.print_exc()
                        print("[ADMIN COMMAND ERROR]")
                        yield from bot.client.send_message(msg.channel, "Failed.")
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[0] == "balance":
                if len(cmd) > 1 and cmd[1] == "history":
                    formatting = bot.prefix + "balance history [page]"
                    user_id = msg.author.id
                    user_msg_name = "Your"
                    ok = True
                    if len(msg.mentions) > 0:
                        if bot.is_me(msg):
                            user_id = msg.mentions[0].id
                            user_msg_name = msg.mentions[0].name + "'s"
                        else:
                            ok = False
                    elif len(cmd) > 3:
                        if bot.is_me(msg):
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
                        if bot.is_me(msg):
                            user_id = msg.mentions[0].id
                            user_msg_name = msg.mentions[0].name + "'s"
                        else:
                            ok = False
                    elif len(cmd) > 1:
                        if bot.is_me(msg):
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
                if (changed and bot.is_me(msg)) or not changed:
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
                formatting = "backup load|save|list|delete|info [backup_name] - commands for backing up the market data"
                if bot.is_me(msg):
                    if len(cmd) >= 3 or cmd[1] == "list":
                        if cmd[1] == "load":
                            formatting = bot.prefix + "backup load [backup_name] - load the backup, see " + bot.prefix + "backup list for a list of backups"
                            backup_name = " ".join(cmd[2:])
                            if bot.market.load_backup(backup_name):
                                yield from bot.client.send_message(msg.channel, ":floppy_disk: Loaded back up, check console for information.")
                            else:
                                yield from bot.client.send_message(msg.channel, ":floppy_disk: Couldn't find a backup named " + backup_name)
                        elif cmd[1] == "save":
                            formatting = bot.prefix + "backup save [backup_name] - save the current data to a backup with that name"
                            backup_name = " ".join(cmd[2:])
                            bot.market.save_backup(bot, backup_name)
                            yield from bot.client.send_message(msg.channel, ":floppy_disk: Backed up, check console for information.")
                        elif cmd[1] == "info":
                            formatting = bot.prefix + "backup info [backup_name] - displays that backup's meta data"
                        elif cmd[1] == "delete":
                            formatting = bot.prefix + "backup delete [backup_name] - delete that backup"
                            backup_name = " ".join(cmd[2:])
                            if backup_name.startswith("."):
                                yield from bot.client.send_message(msg.channel, ":floppy_disk: Invincible backup, cannot delete!")
                            else:
                                if bot.market.delete_backup(backup_name):
                                    yield from bot.client.send_message(msg.channel, ":floppy_disk: Deleted backup " + backup_name)
                                else:
                                    yield from bot.client.send_message(msg.channel, ":floppy_disk: Couldn't find backup named " + backup_name)
                        elif cmd[1] == "list":
                            formatting = bot.prefix + "backup list - list all the known backups"
                            onlyfiles = [f for f in listdir("data/") if not isfile(join("data/", f))]
                            yield from bot.client.send_message(msg.channel, ":floppy_disk: Backups: " + ", ".join(onlyfiles))
                    else:
                        yield from bot.client.send_message(msg.channel, ":floppy_disk: Please give a backup name!")
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[0] == "exchange":
                formatting = bot.prefic + "exchange [amount] [item_name] - exchanges x of a resource for $x"
                amount = int(cmd[1])
                item_name = cmd[2]
                if bot.market.get_inventory(msg.author.id, item_name) >= amount:
                    bot.market.add_inventory(msg.author.id, item_name, -amount, "Exchanging " + item_name + " for money")
                    bot.market.give_money(msg.author.id, item_name, amount, "Exchanging " + item_name + " for money")
                    yield from bot.client.send_message(msg.channel, ":package: Converted **" + str(amount) + " " + item_name + "** to **$" + str(amount) + "**")
                else:
                    yield from bot.client.send_message(msg.channel, ":package: You don't have enough **" + item_name + "**!")
            elif cmd[0] == "ping":
                formatting = bot.prefix + "ping - shows the bots ping to the server"
                bot.ping_start = time.time()
                yield from bot.client.send_message(msg.channel, bot.ping_message)
            elif cmd[0] == "lookup" or cmd[0] == "lookup_all":
                formatting = bot.prefix + "lookup user|id|name|nick <search>"
                if bot.is_me(msg):
                    find_all = False
                    if cmd[0] == "lookup_all":
                        find_all = True
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
                    formatting = bot.prefix + "trade offer [user] {your items} for {their items} :: {items} = $money, 30 itemname, {factory_name} ..."
                    user_id = cmd[2]
                    user_name = cmd[2]
                    if cmd[2].startswith("<") and len(msg.mentions) > 0:
                        user_id = msg.mentions[0].id
                        user_name = msg.mentions[0].name
                    if market.is_number(user_id):
                        if user_id == msg.author.id:
                            yield from bot.client.send_message(msg.channel, ":envelope: Can't send a trade offer to yourself!")
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
                            factory_n = 0
                            for item in raw_trade_to:
                                nospace_item = item.replace(" ", "")
                                item_name = None
                                item_value = 0
                                if nospace_item.startswith("$"):
                                    item_name = "$$$"
                                    item_value = int(item.replace(" ", "")[1:])
                                elif nospace_item.startswith("{") and nospace_item.endswith("}"):
                                    factory_n += 1
                                    item_name = "!!!" + str(factory_n)
                                    item_value = item
                                    while item_value.startswith(" ") or item_value.startswith("{"):
                                        item_value = item_value[1:]
                                    while item_value.endswith(" ") or item_value.endswith("}"):
                                        item_value = item_value[:-1]
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
                                 yield from bot.client.send_message(msg.channel, ":envelope: Sent trade offer!")
                            elif result == market.Market.TRADE_ALREADY_EXISTS:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed as you already have a pending offer to " + user_name)
                            elif result == market.Market.TRADE_FROM_NOT_ENOUGH_ITEM:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because you don't have enough of an item to fulfill the trade!")
                            elif result == market.Market.TRADE_FROM_NOT_ENOUGH_MONEY:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because you don't have enough money to fulfill the trade!")
                            elif result == market.Market.TRADE_TO_NOT_ENOUGH_ITEM:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because " + user_name + " doesn't have enough of an item to fulfill the trade!")
                            elif result == market.Market.TRADE_TO_NOT_ENOUGH_MONEY:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because " + user_name + " doesn't have enough money to fulfill the trade!")
                            elif result == market.Market.TRADE_TO_NO_SUCH_FACTORY:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because " + user_name + " doesn't have one of the factories listed!")
                            elif result == market.Market.TRADE_FROM_NO_SUCH_FACTORY:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because you don't have one of the factories listed!")
                            elif result == market.Market.TRADE_FROM_UNSELLABLE_FACTORY:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because one of your listed factories can't be sold!")
                            elif result == market.Market.TRADE_TO_UNSELLABLE_FACTORY:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because one of " + user_name + "'s listed factories can't be sold!")
                            else:
                                yield from bot.client.send_message(msg.channel, ":envelope: Trade failed with an unspecified error " + str(result))
                    else:
                        yield from bot.client.send_message(msg.channel, ":envelope: Invalid user, must be a mention or a user ID")
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
                    if (changed and bot.is_me(msg)) or not changed:
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
                                        yield from bot.client.send_message(msg.channel, ":envelope: You have sent trade offers to " + ", ".join(result))
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":envelope: " + user_msg_name + " has sent trade offers to " + ", ".join(result))
                                else:
                                    if user_msg_name == "Your":
                                        yield from bot.client.send_message(msg.channel, ":envelope: You haven't sent any trade offers!")
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":envelope: " + user_msg_name + " hasn't sent any trade offers!")
                            else:
                                user_id = cmd[3]
                                if user_id.startswith("<") and len(msg.mentions) > 0:
                                    user_id = msg.mentions[0].id
                                if market.is_number(user_id):
                                    trade = bot.market.get_trade(msg.author.id, user_id)
                                    if trade is not None:
                                        yield from bot.client.send_message(msg.channel, market.Market.stringify("trade", trade))
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":envelope: Couldn't find a trade offer.")
                                else:
                                    yield from bot.client.send_message(msg.channel, ":envelope: Invalid user, use a mention or a user ID")
                        elif cmd[2] == "received" or cmd[2] == "recieved":
                            formatting = bot.prefix + "trade my received [user]"
                            if len(cmd) == 3:
                                result = bot.market.get_trades_to(user_id)
                                if len(result) > 0:
                                    if user_msg_name == "Your":
                                        yield from bot.client.send_message(msg.channel, ":envelope: You have pending trade offers from " + ", ".join(result))
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":envelope: " + user_msg_name + " has pending trade offers from " + ", ".join(result))
                                else:
                                    if user_msg_name == "Your":
                                        yield from bot.client.send_message(msg.channel, ":envelope: You don't have any trade offers!")
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":envelope: " + user_msg_name + " doesn't have any trade offers!")
                            else:
                                user_id = cmd[3]
                                if user_id.startswith("<") and len(msg.mentions) > 0:
                                    user_id = msg.mentions[0].id
                                if market.is_number(user_id):
                                    trade = bot.market.get_trade(user_id, msg.author.id)
                                    if trade is not None:
                                        yield from bot.client.send_message(msg.channel, bot.market.stringify("trade", trade))
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":envelope: Couldn't find a trade offer.")
                                else:
                                    yield from bot.client.send_message(msg.channel, ":envelope: Invalid user, use a mention or a user ID")
                    else:
                        yield from bot.client.send_message(msg.channel, ":envelope: Only the admin can use that command!")
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
                            yield from bot.client.send_message(msg.channel, ":envelope: Accepted trade: \n" + market.Market.stringify("trade", trade))
                        elif result == market.Market.TRADE_DOESNT_EXIST:
                            yield from bot.client.send_message(msg.channel, ":envelope: You don't have any pending trade offers from " + trade["from_name"])
                        elif result == market.Market.TRADE_TO_NOT_ENOUGH_ITEM:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because you don't have enough of an item to fulfill the trade!")
                        elif result == market.Market.TRADE_TO_NOT_ENOUGH_MONEY:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because you don't have enough money to fulfill the trade!")
                        elif result == market.Market.TRADE_FROM_NOT_ENOUGH_ITEM:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because " + trade["from_name"] + " doesn't have enough of an item to fulfill the trade!")
                        elif result == market.Market.TRADE_FROM_NOT_ENOUGH_MONEY:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because " + trade["from_name"] + " doesn't have enough money to fulfill the trade!")
                        elif result == market.Market.TRADE_FROM_NO_SUCH_FACTORY:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because " + trade["from_name"] + " no longer has one of the factories being traded!")
                        elif result == market.Market.TRADE_TO_NO_SUCH_FACTORY:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because you no longer have one of the factories being traded!")
                        elif result == market.Market.TRADE_FROM_UNSELLABLE_FACTORY:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because one of " + trade["from_name"] + "'s factories cannot be sold!")
                        elif result == market.Market.TRADE_TO_UNSELLABLE_FACTORY:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed because one of your factories can't be sold!")
                        else:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed with an unspecified error " + str(result))
                    else:
                        yield from bot.client.send_message(msg.channel, ":envelope: Invalid user, use a mention or a user ID")
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
                            yield from bot.client.send_message(msg.channel, ":envelope: Declined trade from " + trade["from_name"] + "\n " + market.Market.stringify("trade", trade))
                        elif result == market.Market.TRADE_DOESNT_EXIST:
                            yield from bot.client.send_message(msg.channel, ":envelope: You don't have any pending trade offers from " + trade["from_name"])
                        else:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed with an unspecified error " + str(result))
                    else:
                        yield from bot.client.send_message(msg.channel, ":envelope: Invalid user, use a mention or a user ID")
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
                            yield from bot.client.send_message(msg.channel, ":envelope: Cancelled trade to " + trade["to_name"] + "\n " + market.Market.stringify("trade", trade))
                        elif result == market.Market.TRADE_DOESNT_EXIST:
                            yield from bot.client.send_message(msg.channel, ":envelope: You haven't sent any trade offers to " + trade["to_name"])
                        else:
                            yield from bot.client.send_message(msg.channel, ":envelope: Trade failed with an unspecified error " + str(result))
                    else:
                        yield from bot.client.send_message(msg.channel, ":envelope: Invalid user, use a mention or a user ID")
                else:
                    raise IndexError
            elif cmd[0] == "factory":
                formatting = bot.prefix + "factory my|auto|upgrade|upgrades"
                if cmd[1] == "my" or cmd[1].startswith("<") or market.is_number(cmd[1]):
                    formatting = bot.prefix + "factory my list|change|info"
                    user_id = msg.author.id
                    user_msg_name = "Your"
                    changed = False
                    if cmd[1].startswith("<"):
                        user_id = cmd[1][2:-1]
                        changed = True
                    elif cmd[1] != "my":
                        user_id = cmd[1]
                        changed = True
                    if (changed and bot.is_me(msg)) or not changed:
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
                        if cmd[2] == "list":
                            formatting = bot.prefix + "factory my list"
                            names = bot.market.get_factory_name_list(user_id)
                            if len(names) == 0:
                                if user_msg_name == "Your":
                                    yield from bot.client.send_message(msg.channel, ":factory: You don't have any factories!")
                                else:
                                    yield from bot.client.send_message(msg.channel, ":factory: " + user_msg_name + " doesn't have any factories")
                            else:
                                if user_msg_name != "Your":
                                    user_msg_name += "'s"
                                yield from bot.client.send_message(msg.channel, ":factory: " + user_msg_name + " factories: " + ", ".join(names))
                        elif cmd[2] == "change":
                            formatting = bot.prefix + "factory my change [old_nickname] to [new_nickname]"
                            nicks = " ".join(cmd[3:]).split(" to ")
                            if market.is_number(nicks[1]):
                                yield from bot.client.send_message(msg.channel, ":factory: Factory nicknames cannot be entirely numeric (eg factory1 is allows, 111 is not)")
                            else:
                                if bot.market.set_factory_nick(user_id, nicks[0], nicks[1]):
                                    yield from bot.client.send_message(msg.channel, ":factory: Renamed " + nicks[0] + " to " + nicks[1])
                                else:
                                    if user_msg_name == "Your":
                                        yield from bot.client.send_message(msg.channel, ":factory: You don't have a factory named " + nicks[0])
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":factory: " + user_msg_name + " doesn't have a factory named " + nicks[0])
                        elif cmd[2] == "info":
                            formatting = bot.prefix + "factory my info [factory_name]"
                            name = " ".join(cmd[3:])
                            if name != "":
                                factory = bot.market.get_factory(user_id, name)
                                if factory is not None:
                                    if user_msg_name != "Your":
                                        user_msg_name += "'s"
                                    yield from bot.client.send_message(msg.channel, factory.get_info())
                                else:
                                    yield from bot.client.send_message(msg.channel, ":factory: You don't have a factory named '" + name + "'")
                            else:
                                yield from bot.client.send_message(msg.channel, ":factory: No factory name given, use m$factory my info [name]")
                        else:
                            raise IndexError
                    else:
                        yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
                elif cmd[1] == "produce":
                    formatting = bot.prefix + "factory produce [factory_name] [amount]"
                    factory_name = " ".join(cmd[2:-1])
                    amount = int(cmd[-1])
                    factory = bot.market.get_factory(msg.author.id, factory_name)
                    if factory is not None:
                        if amount <= factory.capacity:
                            timetaken = factory.produce(amount)
                            if timetaken > 0:
                                dtstr = ""
                                struct = datetime.datetime.fromtimestamp(timetaken)
                                if struct.hour > 0:
                                    dtstr += "**" + str(struct.hour) + "** hours "
                                if struct.minute > 0:
                                    dtstr += "**" + str(struct.minute) + "** minutes "
                                if struct.second > 0:
                                    dtstr += "**" + str(struct.second) + "** seconds"
                                yield from bot.client.send_message(msg.channel, ":factory: Your factory is now producing **" + str(amount) + " " + factory.item + "**, it will be done in " + dtstr)
                            else:
                                yield from bot.client.send_message(msg.channel, ":factory: Your factory is already producing something!")
                        else:
                            yield from bot.client.send_message(msg.channel, ":factory: Your factory can only produce a maximum of " + str(factory.capacity) + " " + factory.item + " at a time, upgrade it's capacity to improve this!")
                    else:
                        yield from bot.client.send_message(msg.channel, ":factory: Could not find factory named " + factory_name)

                elif cmd[1] == "auto":
                    formatting = bot.prefix + "factory auto on|off|restart [factory_name]"
                    toggle_on = -1
                    if cmd[2] == "on":
                        formatting = bot.prefix + "factory auto on [factory_name]"
                        toggle_on = 0
                    elif cmd[2] == "off":
                        formatting = bot.prefix + "factory auto off [factory_name]"
                        toggle_on = 1
                    elif cmd[2] == "restart":
                        formatting = bot.prefix + "factory auto restart [factory_name]"
                        toggle_on = 2
                    if toggle_on >= 0:
                        name = " ".join(cmd[3:])
                        factory = bot.market.get_factory(msg.author.id, name)
                        if factory is not None:
                            if factory.producing == 2 and toggle_on == 0:
                                yield from bot.client.send_message(msg.channel, ":factory: **" + name + "** is already auto producing!")
                            elif factory.producing == 0 and (toggle_on == 1 or toggle_on == 2):
                                yield from bot.client.send_message(msg.channel, ":factory: **" + name + "** isn't auto producing!")
                            elif factory.producing == 1:
                                yield from bot.client.send_message(msg.channel, ":factory: Is producing manually!")
                            else:
                                if factory.auto_efficieny > 0:
                                    if toggle_on == 0:
                                        amount = factory.start_auto_produce(bot.market.factories["produce_delay"])
                                        yield from bot.client.send_message(msg.channel, ":factory: **" + name + "** has started producing **" + str(amount) + " " + factory.item + "** every **" + str(bot.market.factories["produce_delay"]) + "** seconds")
                                    elif toggle_on == 1:
                                        factory.stop_auto()
                                        yield from bot.client.send_message(msg.channel, ":factory: **" + name + "** has stopped auto producing **" + factory.item + "**")
                                    elif toggle_on == 2:
                                        factory.stop_auto()
                                        amount = factory.start_auto_produce(bot.market.factories["produce_delay"])
                                        yield from bot.client.send_message(msg.channel, ":factory: **" + name + "** has restarted and is now producing **" + str(amount) + " " + factory.item + "** every **" + str(bot.market.factories["produce_delay"]) + "** seconds")
                                    else:
                                        yield from bot.client.send_message(msg.channel, ":factory: Whoops, something went wrong! (Error: " + str(toggle_on) + "), Please try again!")
                                else:
                                    yield from bot.client.send_message(msg.channel, ":factory: **" + name + "** cannot auto produce yet! see " + bot.prefix + "help factory upgrade")
                        else:
                            yield from bot.client.send_message(msg.channel, ":factory: Could not find factory named " + name)
                    else:
                        raise IndexError
                elif cmd[1] == "upgrades":
                    formatting = bot.prefix + "factory upgrades [name] [level]"
                    if len(cmd) == 2:
                        yield from bot.client.send_message(msg.channel, ":factory: Types of upgrade: **" + "**, **".join(market.Factory.FACTORY_UPGRADES) + " **")
                    elif len(cmd) == 3:
                        name = cmd[2]
                        if name in market.Factory.FACTORY_COSTS:
                            yield from bot.client.send_message(msg.channel, ":factory: " + market.Factory.FACTORY_COSTS[name][0])
                        else:
                            yield from bot.client.send_message(msg.channel, ":factory: " + name + " was not recognised as a type of upgrade, see " + bot.prefix + "factory upgrades")
                    else:
                        name = cmd[2]
                        level = int(cmd[3])
                        if name in market.Factory.FACTORY_COSTS:
                            if level > 0 and level < len(market.Factory.FACTORY_COSTS[name]):
                                yield from bot.client.send_message(msg.channel, ":factory: " + market.Factory.FACTORY_COSTS[name][level]["__DESC__"])
                            else:
                                yield from bot.client.send_message(msg.channel, ":factory: Invalid level, must be from 1 to " + str(len(market.Factory.FACTORY_COSTS[name])-1) + " (inclusive)")
                        else:
                            yield from bot.client.send_message(msg.channel, ":factory: " + name + " was not recognised as a type of upgrade, see " + bot.prefix + "factory upgrades")
                elif cmd[1] == "factories":
                    formatting = bot.prefix + "factory factories [itemtype]"
                    if len(cmd) == 2:
                        yield from bot.client.send_message(msg.channel, ":factory: Factories can be created for the following item types: " + ", ".join(market.Factory.FACTORY_CONSTUCT_TYPES))
                    else:
                        itemtype = cmd[2]
                        if itemtype in market.Factory.FACTORY_CONSTUCT_COSTS:
                            cost_type = market.Factory.FACTORY_CONSTUCT_COSTS[itemtype]["type"]
                            cost = market.Factory.FACTORY_CONSTUCT_COSTS[itemtype]["cost"]
                            amount = market.Factory.FACTORY_CONSTUCT_COSTS[itemtype]["amount"]
                            yield from bot.client.send_message(msg.channel, ":factory: To create a " + itemtype + " factory you need " + str(cost) + " of " + str(amount) + " " + cost_type + " resources")
                        else:
                            yield from bot.client.send_message(msg.channel, ":factory: Cannot create factories for item type '" + itemtype + "'")
                elif cmd[1] == "create":
                    formatting = bot.prefix + "factory create [item] with {optional items} :: {optional items} = item_name, item_name and item_name etc."
                    spl1 = " ".join(cmd[2:]).split(" with ")
                    spl3 = spl1[1].replace("and", ",").replace(" ", "").split(",")
                    item = spl1[0]
                    mats = []
                    for mat in spl3:
                        if mat in mats:
                            yield from bot.client.send_message(msg.channel, ":factory: You can't use the same item more than once!")
                            return
                        else:
                            mats.append(mat)
                    result = market.Factory.construct(bot.market, item, msg.author.id, mats)
                    if result > 100:
                        yield from bot.client.send_message(msg.channel, ":factory: Factory created with ID " + result)
                    elif result == market.Factory.CONSTRUCT_INVALID_ITEMS:
                        yield from bot.client.send_message(msg.channel, ":factory: One or more of the items you listed is not of the required item type!")
                    elif result == market.Factory.CONSTRUCT_NOT_ENOUGH_MATS:
                        yield from bot.client.send_message(msg.channel, ":factory: Invalid amount of mats given, you gave " + str(len(mats)) + ", " + str(market.Factory.FACTORY_CONSTUCT_COSTS[bot.market.get_item_type(item)]["amount"]) + " are required")
                    elif result == market.Factory.CONSTRUCT_NOT_ENOUGH_INVENTORY:
                        yield from bot.client.send_message(msg.channel, ":factory: You don't have enough of those items to create the factory!")
                    elif result == market.Factory.CONSTRUCT_INVALID_ITEMTYPE:
                        yield from bot.client.send_message(msg.channel, ":factory: Invalid item, please see " + bot.prefix + "factory factories for a list of valid item types (see " + bot.prefix + "items list [itemtype] for items of that type)")
                    else:
                        yield from bot.client.send_message(msg.channel, ":factory: Unknown error returned [ERROR: " + str(result) + "], please report this to the admins using " + bot.prefix + "ticket error [message]")
                elif cmd[1] == "upgrade":
                    formatting = bot.prefix + "factory upgrade [factory_name] [upgrade_type] with {optional items} :: {optional items} = item_name, item_name and item_name etc."
                    spl1 = " ".join(cmd[2:]).split(" with ")
                    spl2 = spl1[0].split(" ")
                    spl3 = spl1[1].replace("and", ",").replace(" ", "").split(",")
                    name = " ".join(spl2[0:-1])
                    upgrade_type = spl2[-1]
                    mats = {}
                    for item_name in spl3:
                        item_type = bot.market.get_item_type(item_name)
                        if item_type not in mats:
                            mats[item_type] = []
                        if item_name in mats[item_type]:
                            yield from bot.client.send_message(msg.channel, ":factory: You can't use the same item more than once!")
                            return
                        else:
                            mats[item_type].append(item_name)
                    factory = bot.market.get_factory(msg.author.id, name)
                    if factory is not None:
                        result = factory.upgrade(upgrade_type, mats)
                        if result is None: # success
                            yield from bot.client.send_message(msg.channel, ":factory: Succesfully upgraded **" + factory.get_name() + "** to **" + upgrade_type + "** level **" + str(factory.upgrade_levels[upgrade_type]) + "**")
                        elif result == "MAX": # max level
                            yield from bot.client.send_message(msg.channel, ":factory: **" + factory.get_name() + "** is already at max **" + upgrade_type + "** level!")
                        elif result == "ERROR": # invalid upgrade name
                            yield from bot.client.send_message(msg.channel, ":factory: **" + upgrade_type + "** was not recognised as a type of upgrade, see " + bot.prefix + "factory upgrades")
                        else:
                            yield from bot.client.send_message(msg.channel, ":factory: You don't have enough " + str(result) + "!")
                    else:
                        yield from bot.client.send_message(msg.channel, ":factory: Could not find factory named " + name)
                else:
                    raise IndexError
            elif cmd[0] == "info":
                lines = [
                    "**" + bot.name + "** is a CookieClicker-esque bot where you produce items in factories",
                    "Upgrading these factories with the items you produce or buy from the discord-wide market",
                    "",
                    "To see a list of my commands, use **" + bot.prefix + "help**",
                    "To get the bot in your server, use **" + bot.prefix + "join**",
                    "To get an invite to the official MarketBot server, use **" + bot.prefix + "server**",
                    "To register to play, use **" + bot.prefix + "register**",
                    "To get " + bot.name + " in your server, use https://discordapp.com/oauth2/authorize?client_id=187857778583404545&scope=bot&permissions=0"
                    "",
                    "To find out more, visit our website: http://billyoyo.me ",
                ]
                if len(cmd) > 1 and cmd[1] == "here":
                    yield from bot.client.send_message(msg.channel, "\n".join(lines))
                else:
                    yield from bot.client.send_message(msg.author, "\n".join(lines))
            elif cmd[0] == "join" or cmd[0] == "invite":
                yield from bot.client.send_message(msg.channel, "To add " + bot.name + " to your server, use this link: https://discordapp.com/oauth2/authorize?client_id=187857778583404545&scope=bot&permissions=0")
            elif cmd[0] == "ticket":
                formatting = bot.prefix + "ticket message|request|help|error|ban [message]"
                if cmd[1] == "*ban":
                    if bot.is_me(msg):
                        user_id = cmd[2]
                        user_name = user_id
                        if len(msg.mentions) > 0:
                            user_id = msg.mentions[0].id
                            user_name = msg.mentions[0].name
                        else:
                            if bot.lookup_enabled:
                                for server in bot.client.servers:
                                    for member in server.members:
                                        if member.id == user_id:
                                            user_name = member.name
                        if not user_id in bot.tickets["bans"]:
                            bot.tickets["bans"].append(user_id)
                            f = open("ticket_bans.txt", "w")
                            for uid in bot.tickets["bans"]:
                                f.write(uid + "\n")
                            f.close()
                            yield from bot.client.send_message(msg.channel, user_name + " was banned from sending tickets!")
                        else:
                            yield from bot.client.send_message(msg.channel, user_name + " is already banned!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
                elif cmd[1] == "*unban":
                    if bot.is_me(msg):
                        user_id = cmd[2]
                        user_name = user_id
                        if len(msg.mentions) > 0:
                            user_id = msg.mentions[0].id
                            user_name = msg.mentions[0].name
                        else:
                            if bot.lookup_enabled:
                                for server in bot.client.servers:
                                    for member in server.members:
                                        if member.id == user_id:
                                            user_name = member.name
                        if user_id in bot.tickets["bans"]:
                            bot.tickets["bans"].remove(user_id)
                            f = open("ticket_bans.txt", "w")
                            for uid in bot.tickets["bans"]:
                                f.write(uid + "\n")
                            f.close()
                        else:
                            yield from bot.client.send_message(msg.channel, user_name + " isn't banned!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
                elif msg.author.id not in bot.tickets["bans"] or bot.is_me(msg) or cmd[1] == "ban":
                    if msg.author.id not in bot.tickets["cds"] or time.time() - bot.tickets["cds"] > 30:
                        if cmd[1] == "ban" and not msg.author.id in bot.tickets["bans"]:
                            yield from bot.client.send_message(msg.channel, "Only users who are banned from sending tickets can send messages to the ban channel")
                        else:
                            if cmd[1] in bot.tickets["channels"]:
                                yield from bot.client.send_message(bot.tickets["channels"][cmd[1]], "[" + msg.author.name + " : " + msg.author.id + "] (" + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + ") : " + " ".join(cmd[2:]))
                            else:
                                yield from bot.client.send_message(msg.channel, "Invalid ticket type, must be one of message, request, help, error, ban")
                    else:
                        yield from bot.client.send_message(msg.channel, "You sent a ticket too recently, you must wait another " + str(30 - (time.time() - bot.tickets["cds"])) + " seconds before sending another!")
                else:
                    yield from bot.client.send_message(msg.channel, "You are banned from sending tickets, use " + bot.prefix + "ticket ban <message> to contest this ban")
            elif cmd[0] == "server":
                yield from bot.client.send_message(msg.channel, "https://discord.gg/013GE1ZeT5ntIaWCW")
            elif cmd[0] == "items":
                formatting = bot.prefix + "items set|del|get|list [item] [item_type]"
                if bot.is_me(msg) or cmd[1] == "get" or (cmd[1] == "list" and len(cmd) > 2):
                    if cmd[1] == "set":
                        bot.market.set_item_type(cmd[2], cmd[3])
                        yield from bot.client.send_message(msg.channel, "Set **" + cmd[2] + "'s** item type to **" + cmd[3] + "**")
                    elif cmd[1] == "get":
                        yield from bot.client.send_message(msg.channel, "**" + cmd[2] + "'s** item type is **" + bot.market.get_item_type(cmd[2]) + "**")
                    elif cmd[1] == "del":
                        old_type = bot.market.get_item_type(cmd[2])
                        bot.market.delete_item_type(cmd[2])
                        yield from bot.client.send_message(msg.channel, "Deleted item type for **" + cmd[2] + "** (was **" + old_type + "**)")
                    elif cmd[1] == "list":
                        item_type_name = "registered"
                        item_list = bot.market.item_types
                        if len(cmd) > 2:
                            item_list = bot.market.get_items_from(cmd[2])
                            item_type_name = cmd[2]
                        lines = "```\n"
                        for item in bot.market.item_types:
                            lines += item + ": " + bot.market.item_types[item] + "\n"
                        lines += "```"
                        yield from bot.client.send_message(msg.channel, "List of " + item_type_name + " items: \n" + lines)
                    else:
                        raise IndexError
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[0] == "register":
                if not msg.author.id in bot.market.factories:
                    lowest = None
                    lower_amt = 0
                    for item_name in bot.market.get_items_from("base"):
                        if lowest is None or bot.market.get_market_amount(item_name) < lower_amt:
                            lowest = item_name
                    if lowest is not None:
                        factory = bot.market.create_factory(msg.author.id, lowest)
                        yield from bot.client.send_message(msg.channel, "Registered! You have been given a **" + lowest + "** factory, it's ID is " + factory.id + "\n" +
                                                                        "To give your factory a name, do '" + bot.prefix + "factory my change " + factory.id + " to your_factory_name' \n" +
                                                                        "For tips on what to do next, use " + bot.prefix + "guide")
                    else:
                        yield from bot.client.send_message(msg.channel, "Failed to register, no base items could be found!")
                else:
                    yield from bot.client.send_message(msg.channel, "You are already registered! See " + bot.prefix + "guide for tips on what you should be doing next")
            elif cmd[0] == "unregister":
                if msg.author.id in bot.market.factories:
                    yield from bot.client.send_message(msg.author, "This is an unreversable action and will wipe all of your progress, are you sure you want to continue? (Type 'yes' to continue)")
                    response = yield from bot.client.wait_for_message(timeout=300, channel=msg.author)
                    if response.lower() == "yes":
                        bot.market.wipe(msg.author.id)
                        yield from bot.client.send_message(msg.author, "Wiped your progress and unregistered you.")
                    else:
                        yield from bot.client.send_message(msg.author, "Cancelled, did not wipe your progress.")
                else:
                    yield from bot.client.send_message(msg.channel, "You aren't registered!")
            elif cmd[0] == "close":
                if bot.is_me(msg):
                    bot.market.save()
                    bot.market.close()
                    asyncio.get_event_loop().stop()
                else:
                    yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            elif cmd[0] == "achiev":
                formatting = bot.prefix + "achiev mute|unmute|info"
                if cmd[1] == "mute":
                    if msg.author.id not in bot.market.achievs["__mute__"]:
                        bot.market.achievs["__mute__"].append(msg.author.id)
                        yield from bot.client.send_message(msg.channel, "Achievement updates muted")
                    else:
                        yield from bot.client.send_message(msg.channel, "Achievement updates already muted!")
                elif cmd[1] == "unmute":
                    if msg.author.id in bot.market.achievs["__mute__"]:
                        bot.market.achievs["__mute__"].remove(msg.author.id)
                        yield from bot.client.send_message(msg.channel, "Achievement updates unmuted")
                    else:
                        yield from bot.client.send_message(msg.channel, "Achievement updates are already unmuted!")
            elif cmd[0] == "guide":
                yield from bot.client.send_message(msg.channel, "Coming soon:tm:")
            elif cmd[0] == "chest":
                formatting = bot.prefix + "chest list|open|daily [chest_type]"
                if cmd[1] == "list":
                    #formatting = bot.prefix + "chest list"
                    if msg.author.id in bot.market.chests and len(bot.market.chests[msg.author.id]) != 0:
                        chest_types = []
                        for grade in bot.market.chests[msg.author.id]:
                            if market.is_number(grade):
                                amt = bot.market.chests[msg.author.id][grade]
                                if amt > 0:
                                    line = "**" + str(amt) + "** " + market.Chest.LOOT[int(grade)][0]["name"] + " chest"
                                    if amt > 1:
                                        line += "s"
                                    chest_types.append(line)
                        if len(chest_types) > 0:
                            yield from bot.client.send_message(msg.channel, ":gift: You have " + ", ".join(chest_types))
                        else:
                            yield from bot.client.send_message(msg.channel, ":gift: You don't have any chests!")
                    else:
                        yield from bot.client.send_message(msg.channel, ":gift: You don't have any chests!")
                elif cmd[1] == "open":
                    formatting = bot.prefix + "chest open [chest_name]"
                    chest_name = " ".join(cmd[2:])
                    if chest_name in market.Chest.LOOT_GRADE_NAMES:
                        grade = str(market.Chest.LOOT_GRADE_NAMES.index(chest_name))
                        if msg.author.id in bot.market.chests:
                            if grade in bot.market.chests[msg.author.id] and bot.market.chests[msg.author.id][grade] > 0:
                                chest = market.Chest(bot.market, msg.author.id, int(grade))
                                results = chest.open()
                                bot.market.chests[msg.author.id][grade] -= 1
                                yield from bot.client.send_message(msg.channel, ":gift: Success! You got: \n ```\n" + "\n".join(results) + "\n```")
                            else:
                                yield from bot.client.send_message(msg.channel, ":gift: You don't have any " + chest_name + " chests!")
                        else:
                            yield from bot.client.send_message(msg.channel, ":gift: You don't have any chests!")
                    else:
                        yield from bot.client.send_message(msg.channel, ":gift: Invalid chest type, must be one of: " + ", ".join(market.Chest.LOOT_GRADE_NAMES))
                elif cmd[1] == "daily":
                    #formatting = "chest daily"
                    time_left = -1
                    if msg.author.id in bot.market.chests and "__daily__" in bot.market.chests[msg.author.id]:
                        last_daily = bot.market.chests[msg.author.id]["__daily__"]
                        elap = time.time() - last_daily
                        if elap < 86400:
                            ok = False
                            time_left = 86400 - elap
                    if time_left < 0:
                        bot.market.give_chest(msg.author.id, 0)
                        bot.market.chests[msg.author.id]["__daily__"] = time.time()
                        yield from bot.client.send_message(msg.channel, ":gift: You claimed your daily chest!")
                    else:
                        line = ":gift: You can get another chest in "
                        struct = datetime.datetime.fromtimestamp(time_left)
                        if struct.hour > 0:
                            line += str(struct.hour) + " hours "
                        if struct.minute > 0:
                            line += str(struct.minute) + " minutes"
                        yield from bot.client.send_message(msg.channel, line)

    except (IndexError, ValueError, KeyError):
        yield from bot.client.send_message(msg.channel, formatting)
        traceback.print_exc()
    except Exception:
        yield from bot.client.send_message(msg.channel, "Something went wrong! Please use " + bot.prefix + "ticket error <message> to send an error report to me!")
        traceback.print_exc()

    yield from handle_achievs(bot)

def handle_achievs(bot):
    for obj in bot.market.achiev_stack:
        if not obj in bot.market.achievs["__mute__"]:
            dest = bot.client.connection._get_private_channel_by_user(obj[0])
            if dest is None:
                dest = yield from bot.client.start_private_message(discord.User(id=obj[0], name="???", desc="0000", avatar=None, bot=False))
            yield from bot.client.send_message(dest, "Test, you got an achiev: ! Use " + bot.prefix + "achiev mute to mute these messages")
    bot.market.achiev_stack = []

def market_handle_l(cmd):
    if cmd[0] == "market":
        return 2
    elif cmd[0] == "trade":
        return 2
    return 1


def setup(bot, help_page, filename):
    bot.admin_list = []
    f = open("adminlist.txt")
    for line in f:
        bot.admin_list.append(line)
    f.close()
    print("Loaded admins: " + str(bot.admin_list))

    bot.tickets["bans"] = []
    bot.tickets["channels"] = {}
    bot.tickets["cds"] = {}
    f = open("ticket_bans.txt", "r")
    for line in f:
        bot.tickets["bans"].append(line.replace("\n", ""))
    f.close()
    for server in bot.client.servers:
        if server.id == "188443977286942720": # marketbot server
            for channel in server.channels:
                if channel.id == "189102356955136000": # ticket_request channel
                    bot.tickets["channels"]["request"] = channel
                elif channel.id == "189103209581772810": # ticket_help channel
                    bot.tickets["channels"]["help"] = channel
                elif channel.id == "189103234240086016": # ticket_error channel
                    bot.tickets["channels"]["error"] = channel
                elif channel.id == "189103285154742273": # ticket_msg channel
                    bot.tickets["channels"]["message"] = channel
                elif channel.id == "189105413050990592": # ticket_ban channel
                    bot.tickets["channels"]["ban"] = channel

    bot.market = market.Market()
    print("Created market")

    help_page.register("core", "", "", hidden=True, header=[":notebook_with_decorative_cover:Core commands:", ":notebook_with_decorative_cover: Please note these commands are in beta and may fail sometimes, if they do please send me a ticket using %p%ticket error [message]"])
    help_page.register("misc", "", "", hidden=True, header=":notebook_with_decorative_cover:Miscellaneous commands:")
    help_page.register("admin", "", "", hidden=True, header=":notebook_with_decorative_cover:Admin commands:")
    help_page.register("market", "", "", hidden=True, header=":notebook_with_decorative_cover:Market commands:")
    help_page.register("items", "", "", hidden=True, header=":notebook_with_decorative_cover:Market commands:")
    help_page.register("trade", "", "", hidden=True, header=":notebook_with_decorative_cover:Trade commands:")
    help_page.register("factory", "", "", hidden=True, header=":notebook_with_decorative_cover:Factory commands:")
    help_page.register("chest", "", "", hidden=True, header=":notebook_with_decorative_cover:Chest commands:")
    help_page.register("fun", "", "", hidden=True, header=":notebook_with_decorative_cover:Fun commands:")
    help_page.register("mod", "", "", hidden=True, header=[":notebook_with_decorative_cover:Moderator commands:", ":notebook_with_decorative_cover:  Note: (P1) means the command requires the 'Manage Messages' permission"])
    help_page.register("util", "", "", hidden=True, header=":notebook_with_decorative_cover:Utility commands:")
    help_page.register("speedtype", "", "", hidden=True, header=":notebook_with_decorative_cover:Speed typing commands:")
    help_page.register("tag", "", "", hidden=True, header=":notebook_with_decorative_cover:Tag commands:")
    help_page.register("remindme", "", "", hidden=True, header=":notebook_with_decorative_cover:Remindme time args:")
    help_page.register("hangman", "", "", hidden=True, header=":notebook_with_decorative_cover:Hangman commands:")
    help_page.register("cleanup", "", "", hidden=True, header=[":notebook_with_decorative_cover:Cleanup commands:", ":notebook_with_decorative_cover:  Note: (P1) means the command requires the 'Manage Messages' permission"])
    help_page.register("purge-args", "", "", hidden=True, header=[":notebook_with_decorative_cover:Purge arguments:", ":notebook_with_decorative_cover: (n-c-s) means not-case-sensitive"])

    help_page.register("market", "", "does market stuff, see **%p%help market** for commands", root="core", header=":notebook_with_decorative_cover:Market commands:")
    help_page.register("market price", "", "information on the current market prices of items, see **%p%help market price**", root="market", header=":notebook_with_decorative_cover:Market price commands")
    help_page.register("market price buying", "[item] | [amount] [item]", "tells you the current minimum price to buy an item", root=["market", "price"])
    help_page.register("market price selling", "[item] | [amount] [item]", "tells you the current maximum price the item is being bought at", root=["market", "price"])
    help_page.register("market amount", "", "information on the amount of items being sold or offered on the market, see **%p%help market amount**", root="market", header=":notebook_with_decorative_cover:Market amount commands:")
    help_page.register("market amount selling", "[item] [price] [exact]", "how much of the item is being sold, if a price is given it's amount<=price, if exact is yes it's amount=price", root="market amount")
    help_page.register("market amount buying", "[item] [price] [exact]", "how much of the item is being sold, if a price is given it's amount>=price, if exact is yes it's amount=price", root="market amount")
    help_page.register("market sell", "[amount] [item] [price]", "sells an amount of that item at the given price per unit (eg 10 rock $5 sells 10 rocks at $5 each)", root="market")
    help_page.register("market buy", "[amount] [item]", "buys an amount of that item at the minimum possible price from the market", root="market")
    help_page.register("market offer", "[amount] [item] [price]", "puts an offer on the market for buying an amount of that item at or below a given price", root="market")
    help_page.register("market my", "", "commands for looking at information about your sales and offers, set **%p%help market my**", root="market", header=":notebook_with_decorative_cover:Market my commands:")
    help_page.register("market my offers", "[page]", "shows you the page of your current offers list", root="market my")
    help_page.register("market my offers get", "[item] [page]", "generates a list of offers based on the criteria (if item is not given it's a list of all your offers)", root="market my")
    help_page.register("market my offers remove", "[id]", "removes the offer with the given id from the market", root="market my")
    help_page.register("market my sales", "[page]", "shows you the page of your current sales list", root="market my")
    help_page.register("market my sales get", "[item] [page]", "generates a list of sales based on the criteria (if item is not given it's a list of all your sales)", root="market my")
    help_page.register("market my sales remove", "[id]", "removes the sale with the given id from the market", root="market my")
    help_page.register("market refresh", "[item]", "refreshes the market information on a certain item, or all items if no item is given", root="market")

    help_page.register("trade", "", "does trading stuff, see **%p%help trade** for commands", root="core", header=":notebook_with_decorative_cover:Trading commands:")
    help_page.register("trade offer", "[user] {your items} for {their items}", "see **%p%help trade offer** for mor information", root="trade", header=":notebook_with_decorative_cover:Trade offer commands:")
    help_page.register("trade offer", "[user] {your items} for {their items}", ["{items} is a list seperated , where each item is either:",
                                                                                "                                                  an item (amount item_type)",
                                                                                "                                                  money ($amount)",
                                                                                "                                                  a factory ({factory_name})",
                                                                                "                                             eg: trade offer @example 10 rock, 20 wool, {factory_2} for 1000 log, $10000"], root="trade offer")
    help_page.register("trade my sent", "[user]", "shows you a list of the people you've sent offers to, if user is given shows the offer you sent them", root="trade")
    help_page.register("trade my received", "[user]", "shows you a list of offers you've been sent, if user is given shows you the offer they have sent you", root="trade")
    help_page.register("trade accept", "[user]", "accepts an offer from that user", root="trade")
    help_page.register("trade decline", "[user]", "declines an offer from that user", root="trade")
    help_page.register("trade cancel", "[user]", "cancels an offer to that user", root="trade")

    help_page.register("factory", "", "does factory stuff, see **%p%help factory** for commands", root="core", header=":notebook_with_decorative_cover:Factory commands:")
    help_page.register("factory my", "", "commands for looking at information about your factories", root="factory", header=":notebook_with_decorative_cover:Factory my commands:")
    help_page.register("factory my list", "", "lists the names of your factories", root="factory my")
    help_page.register("factory my change", "[old_name] to [new_name]", "changes the name of one of your factories", root="factory my")
    help_page.register("factory my info", "[factory_name]", "shows some information about that factory", root="factory my")
    help_page.register("factory auto", "", "commands for changing the automation of your factory", root="factory", header=":notebook_with_decorative_cover:Factory auto commands:")
    help_page.register("factory auto on", "[factory_name]", "turns the automated production for your factory on", root="factory auto")
    help_page.register("factory auto off", "[factory_name]", "turns the automated production for your factory off", root="factory auto")
    help_page.register("factory auto restart", "[factory_name]", "restars the automation production, useful if you upgrade your factory", root="factory restart")
    help_page.register("factory upgrades", "[upgrade_type] [level]", "shows information about the different factory upgrades, both parameters are optional", root="factory")
    help_page.register("factory upgrade", "[factory_name] [upgrade_type] with {optional items}", "upgrades a factory, {optional item} = item1, item1 etc", root="factory")
    help_page.register("factory factories", "[item_type]", "shows how much constructing a factory of that type costs, or a list of item types if none is given", root="factory")
    help_page.register("factory create", "[item] with {optional item}", "creates a factory that produces wool, {optional items} is the same as in factory upgrade", root="factory")

    help_page.register("chest", "", "commands to do with reward chests, see **%p%help chest** for commands", root="core", header=":notebook_with_decorative_cover:Chest commands:")
    help_page.register("chest list", "", "shows you a list of your chests", root="chest")
    help_page.register("chest open [chest_type]", "", "opens a chest of the given type", root="chest")
    help_page.register("chest daily", "", "claims your daily chest", root="chest")

    help_page.register("exchange", "[amount] [item]", "exchanges x of an item for $x", root="core")
    help_page.register("balance", "", "checks your balance", root="core")
    help_page.register("balance history", "[page]", "shows your transaction history", root="core")
    help_page.register("inv", "[item]", "tells you have much of an item you have, if no item given tells you what items you have", root="core")
    help_page.register("items", "", "information about item types", root="core", header=":notebook_with_decorative_cover:Item commands:")
    help_page.register("items get", "[item]", "shows the item type for that item", root="items")
    help_page.register("items list", "[item_type]", "lists the items with that item type", root="items")
    help_page.register("register", "", "registers to play the game and sets you up with your first factory", root="core")
    help_page.register("unregister", "", "unregisters you, removing all trace of you from the market", root="core")

    help_page.register("guide", "", "gives you tips on what you should be working towards next", root="misc")
    help_page.register("join", "", "Gives you a bot invite link so you can get " + bot.name + " in your servers", root="misc")
    help_page.register("invite", "", "alias for join", root="misc")
    help_page.register("ticket", "message|request|help|error|ban [message]", "commands for sending a ticket to the admins", root="misc")
    help_page.register("server", "", "gives you an invite link to the offical MarketBot server", root="misc")
    help_page.register("ping", "", "tells you the bots ping to your server", root="misc")

    help_page.register("close", "", "saves and closes the bot (doesn't always close it, not very reliable)", root="help admin")
    help_page.register("backup", "", "commands for backup bot data", root="help admin")
    help_page.register("save", "", "manually save the bot data", root="admin")
    help_page.register("admin", "[code]", "manually perform some code", root="admin")
    help_page.register("lookup", "", "commands for looking up users and servers, lookup_all for returning all results completley", root="admin")
    help_page.register("ticket", "*ban|*unban [user]", "bans or unbans a user from sending tickets (except to the ban section)", root="admin")
    help_page.register("items list", "", "lists all registered items", root="admin")
    help_page.register("items set", "[item] [item_type]", "sets the item type for that item", root="admin")
    help_page.register("items del", "[item]", "deletes the item type for that item", root="admin")

    #help_page.register("profile", "", "shows you your profile card", root="fun")
    help_page.register("8ball", "[question]", "gives you a reply from the magic 8 ball", root="fun")
    help_page.register("roll", "[amount]", "rolls that amount of dice, one if no amount given", root="fun")
    help_page.register("flip", "", "flips a coin", root="fun")
    help_page.register("reverse", "[text]", "reverse the text", root="fun")
    help_page.register("xkcd", "[n]", "gives you the xkcd comic with that id, or a random one if n isn't given", root="fun")
    help_page.register("canh", "[n]", "gives you the cyanide and happiness comic with that id, or a random one if n isn't given", root="fun")
    help_page.register("hb", "[suffix]", "gives you the information about the current humble bundle, suffix is a url suffix (optional)", root="fun")
    help_page.register("cat", "", "gives you a random cat picture", root="fun")
    help_page.register("speedtype", "", "commands for a speed typing gaming, see **%p%help speedtype** for information", root="fun")
    help_page.register("speedtype rules", "", "details the rules for the game", root="speedtype")
    help_page.register("speedtype new", "[time] [mentions]", "creates a new game with everyone mentioned, time is the length of the game and defaults to 30secs", root="speedtype")
    help_page.register("speedtype accept", "", "accepts an invite to a game", root="speedtype")
    help_page.register("speedtype decline", "", "declines an invite to a game", root="speedtype")
    help_page.register("hangman", "", "commands for hangman game, see **%p%help hangman** for information", root="fun")
    help_page.register("hangman new", "", "creates a new hangman game for the channel", root="hangman")
    help_page.register("hangman end", "", "ends the current hangman game for the channel", root="hangman")
    help_page.register("hangman [guess]", "", "make a guess, can be a letter or a word", root="hangman")
    #help_page.register("vs", "[width] [height] [code]", "experimental command for creating vector graphics, no documentation on how it works until I finalize it.", root="fun")
    #help_page.register("vs", "[width] [height] [code]", "experimental command for creating vector graphics, no documentation on how it works until I finalize it.", root="fun")
    help_page.register("riddle", "", "gives you a riddle, see **%p%help riddle** for more information", root="fun")
    help_page.register("riddle new", "", "gives you a new riddle, use **%p%riddle [guess]** to make guesses. Riddles are per-channel", root="riddle")
    help_page.register("riddle giveup", "", "gives up on the channel's current riddle", root="riddle")
    help_page.register("riddle [guess]", "", "make a guess", root="riddle")

    help_page.register("stats", "", "shows some stats about the bot", root="util")
    help_page.register("search", "[search]", "shows the top result of a web search", root="util")
    help_page.register("wiki", "[search]", "shows the most relevant wiki page to what you wrote", root="util")
    help_page.register("ud", "[search]", "shows the top result of an Urban Dictionary search", root="util")
    help_page.register("uptime", "", "shows you how long the bots been running for", root="util")
    help_page.register("motd", "", "shows you the message-of-the-day for the current channel", root="util")
    help_page.register("remindme", "[messsage] in [time args]", "sends the message to you after the specified amount of time see **%p%help remindme**", root="util")
    help_page.register("remindme args", "[seconds] seconds [minutes] minutes etc..", "works for weeks, days, hours, minutes & seconds, non-plurals work too", root="remindme")
    help_page.register("remindme** eg1", "%p%remindme hello world in 10 seconds and 3 minutes**", "sends you 'hello world' after 10 seconds and 3 minutes", root="remindme")
    help_page.register("remindme** eg2", "%p%remindme example text in 3 weeks 5 days 1 hour", "sends you 'example text' after 3 weeks, 5 days and 1 hour", root="remindme")
    help_page.register("remindme** eg3", "%p%remindme last example in 5 hours, 10 minutes", "sends you 'last exmaple' after 5 hours and 10 minutes", root="remindme")
    help_page.register("tag", "", "commands for creating text-tags, see **%p%help tag** for more information", root="util")
    help_page.register("tag \"tag_name\" tag", "", "creates a new tag (tags are channel-specific)", root="tag")
    help_page.register("tag tag_name", "", "pastes that tag in to chat", root="tag")
    help_page.register("erate", "[currency_1] [currency_2]", "gets the exchange rate between those two currencies", root="util")
    help_page.register("erate bind", "[bind] [currency]", "creates a binding so 'bind' can be used instead of 'currency' when using erate", root="util")

    help_page.register("prefix", "[prefix]", "sets the prefix for this channel", root="mod")
    help_page.register("purge", "[limit] [args]", "purges the chat for the given args, see **%p%help purge-args** for details on these args", root="mod")
    help_page.register("purge-args** user", "%u%username%u%**", "purges all message by users with the name 'username' (n-c-s)", root="purge-args")
    help_page.register("purge-args** not user", "%nu%username%nu%**", "purges all messages by users without the name 'username' (n-c-s)", root="purge-args")
    help_page.register("purge-args** contains", "%c%string%c%**", "purges all messages which contain 'string'", root="purge-args")
    help_page.register("purge-args** contains (n-c-s)", "%ic%string%ic%**", "purges all messages which contain 'string'", root="purge-args")
    help_page.register("purge-args** doesn't contain", "%nc%string%nc%**", "purges all messages which don't contain 'string'", root="purge-args")
    help_page.register("purge-args** doesn't contain (n-c-s)", "%inc%string%inc%**", "purges all messages which don't contain 'string", root="purge-args")
    help_page.register("purge-args** all", "%all%**", "purges all messages", root="purge-args")
    help_page.register("purge-args** eg_1", "%p%purge 50 %nu%user%nu% %nc%save%nc%**", "purge the first 50 messages not by user or that don't contain save", root="purge-args")
    help_page.register("purge-args** eg_2", "%p%purge 100 %u%troll%u%**", "purges the first 100 messages by troll", root="purge-args")
    help_page.register("purge-args** eg_3", "%p%purge 20 %all%**", "purges the last 20 messages", root="purge-args")
    help_page.register("tag ban|unban", "[mentions]", "bans or unbans all members mentioned from using tags in that channel (P1)", root="mod")
    help_page.register("tag delete", "[tagname]", "deletes that tag name (P1)", root="mod")
    help_page.register("ignore", "", "makes the bot ignore this channel (P1)", root="mod")
    help_page.register("unignore", "", "stops the bot from ignoring this channel (P1)", root="mod")
    help_page.register("cleanup", "", "commands for changing the bots auto-delete settings, see **%p%help cleanup** for commans (P1)", root="mod")
    help_page.register("cleanup stop", "", "stops the bot from auto-deleting messages in this channel (P1)", root="cleanup")
    help_page.register("cleanup [delay]", "", "makes the bot auto-delete messages after 'delay' seconds (P1)", root="cleanup")
    help_page.register("cleanup tags stop", "", "stops the bot from auto-deleting tag-messages in this channel (P1)", root="cleanup")
    help_page.register("cleanup tags [delay]", "", "makes the bot auto-delete tag-messages after 'delay' seconds (P1)", root="cleanup")
    help_page.register("motd set [message]", "", "sets the message-of-the-day for the current channel", root="mod")

    help_page.register("help core", "", "see list of core commands")
    help_page.register("help misc", "", "see list of miscellaneous commands")
    help_page.register("help fun", "", "see list of fun commands")
    help_page.register("help util", "", "see list of utility commands")
    help_page.register("help mod", "", "see list of moderator commands (for channel moderators use)")
    help_page.register("help admin", "", "see list of global admin commands (not for general use)")
    help_page.register("info", "", "displays information about the bot")

    print("Registered help pages")

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
    bot.register_command("invite", market_handle, market_handle_l)
    bot.register_command("ticket", market_handle, market_handle_l)
    bot.register_command("register", market_handle, market_handle_l)
    bot.register_command("unregister", market_handle, market_handle_l)
    bot.register_command("server", market_handle, market_handle_l)
    bot.register_command("factory", market_handle, market_handle_l)
    bot.register_command("items", market_handle, market_handle_l)
    bot.register_command("close", market_handle, market_handle_l)
    bot.register_command("exchange", market_handle, market_handle_l)
    bot.register_command("achiev", market_handle, market_handle_l)
    bot.register_command("guide", market_handle, market_handle_l)
    bot.register_command("chest", market_handle, market_handle_l)
    bot.register_command("avatar", market_handle, market_handle_l)

    print("Registered commands")