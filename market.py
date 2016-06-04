import threading, math, copy, json, os

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class Factory:
    FACTORY_LEVELS = [
        {
            "time_scaling": 5,
            "max_production": 20
        },
        {
            "time_scaling": 9,
            "max_production": 25
        }
    ]
    def __init__(self, market, user, item, factory_id, factory_level = 1):
        self.market = market
        self.user = user
        self.item = item
        self.factory_level = 0
        self.modifiers = {}
        self.time_scale = 5
        self.max_production = 10
        self.id = factory_id
        self.nickname = None

        self.update_factory_level()

    def set_nickname(self, nickname):
        self.nickname = nickname

    def set_modifier(self, factory_detail, value):
        self.modifiers[factory_detail] = value
        self.update_factory_level()

    def get_modifier(self, factory_detail):
        if factory_detail in self.modifiers:
            return self.modifiers[factory_detail]
        return None

    def add_modifier(self, factory_detail, value):
        mod = self.get_modifier(factory_detail)
        if mod is not None:
            value += mod
        self.set_modifier(factory_detail, mod)

    def update_factory_level(self, factory_level=-1):
        if factory_level >= 0:
            self.factory_level = factory_level
        level = Factory.FACTORY_LEVELS[factory_level]
        for factory_detail in level:
            value = level[factory_detail]
            if factory_detail in self.modifiers:
                value += self.modifiers[factory_detail]
            setattr(self, factory_detail, value)

    def get_time_taken(self, amount, time_scaling=-1):
        if time_scaling < 0:
            time_scaling = self.time_scaling
        return (amount*10) / math.log(time_scaling * 0.95)

    def produce(self, amount):
        delay = self.get_time_taken(amount)
        self.market.queue_event(delay, self.market.add_inventory, self.user, self.item, amount)
        return delay

class Market:
    BUY_NO_SUCH_ITEM = 0
    BUY_NOT_ENOUGH_ITEM = 1
    BUY_NOT_ENOUGH_MONEY = 2
    BUY_SUCCESS = 3

    TRADE_SUCCESS = 0
    TRADE_FROM_NOT_ENOUGH_MONEY = 1
    TRADE_FROM_NOT_ENOUGH_ITEM = 2
    TRADE_TO_NOT_ENOUGH_MONEY = 3
    TRADE_TO_NOT_ENOUGH_ITEM = 4
    TRADE_ALREADY_EXISTS = 5
    TRADE_DOESNT_EXIST = 6

    def __init__(self):
        self.running = True
        self.market = {}
        self.offers = {}
        self.money = {}
        self.inventory = {}
        self.factories = {}
        self.money_history = {}
        self.last_offer_lists = {}
        self.last_market_lists = {}
        self.trading = {}
        self.market["___last_id___"] = 100000
        self.inventory["save_delay"] = 60 # save every minute
        self.inventory["save_id"] = 0
        self.load()
        self.save_loop()

    def set_save_delay(self, delay):
        self.inventory["save_delay"] = delay

    def close(self):
        self.running = False

    def save(self, dir_suffix=""):
        if dir_suffix == "":
            self.inventory["save_id"] += 1
        if not os.path.exists("data/"):
            os.makedirs("data/")
        if not os.path.exists("data/" + dir_suffix):
            os.makedirs("data/" + dir_suffix)
        to_save = ["market", "offers", "money", "inventory", "factories", "money_history", "trading"]
        for fname in to_save:
            try:
                data = getattr(self, fname)
                if data is not None:
                    f = open("data/" + dir_suffix + fname + ".json", "w")
                    json.dump(data, f)
                    if not f.closed:
                        f.close()
                else:
                    raise()
            except:
                print("[SAVE ERROR] Failed to save " + fname)
        if dir_suffix != "":
            print("[BACKUP] Backed up, ID: " + dir_suffix + ", Save ID: " + str(self.inventory["save_id"]))
        else:
            print("[SAVE] Saved, ID: " + str(self.inventory["save_id"]))

    def load(self, dir_suffix=""):
        print("[LOAD] Loading...")
        if not os.path.exists("data/"):
            os.makedirs("data/")
        if os.path.exists("data/" + dir_suffix):
            to_load = ["market", "offers", "money", "inventory", "factories", "money_history", "trading"]
            for fname in to_load:
                try:
                    file_name = "data/" + dir_suffix + fname + ".json"
                    if os.path.exists(file_name):
                        f = open(file_name, "r")
                        setattr(self, fname, json.load(f))
                        if not f.closed:
                            f.close()
                    else:
                        print("[LOAD ERROR] Couldn't find file " + file_name)
                except:
                    print("[LOAD ERROR] Failed to load " + fname)
            if dir_suffix == "":
                print("[LOAD] Loaded!")
            else:
                print("[BACKUP] Loaded backup " + dir_suffix + ", Save ID: " + self.inventory["save_id"])
        else:
            print("[BACKUP] Invalid backup name " + dir_suffix)

    def save_backup(self, backup_name):
        index = 0
        while os.path.exists("data/" + backup_name + "/"):
            index += 1
            backup_name += str(index)
        self.save(backup_name + "/")

    def load_backup(self, backup_name):
        self.load(backup_name + "/")

    def save_loop(self):
        if self.running:
            self.save()
            threading.Timer(self.inventory["save_delay"], self.save_loop).start()

    def queue_event(self, delay, func, *args):
        threading.Timer(delay, func, args).start()

    def get_market_list(self, user, item=None):
        if user in self.last_market_lists:
            return self.last_market_lists[user]
        else:
            return self.find_market_list(user, item)

    def find_market_list(self, user, item=None):
        market_list = []
        if item is None:
            for item_name in self.market:
                if not item_name.startswith("_"):
                    market_list = market_list + self.find_market_list(user, item_name)
        elif item in self.market:
            for item_id in self.market[item]:
                if is_number(item_id):
                    if self.market[item][item_id]["user"] == user:
                        market_list.append(self.market[item][item_id])
        self.last_market_lists[user] = market_list
        return market_list

    def get_offer_list(self, user, item=None):
        if user in self.last_offer_lists:
            return self.last_offer_lists[user]
        else:
            return self.find_offer_list(user, item)

    def find_offer_list(self, user, item=None):
        offer_list = []
        if item is None:
            for item_name in self.offers:
                if not item_name.startswith("_"):
                    offer_list = offer_list + self.find_offer_list(user, item_name)
        elif item in self.offers:
            for offer in self.offers[item]:
                if is_number(offer):
                    if self.offers[item][offer]["user"] == user:
                        offer_list.append(self.offers[item][offer])
        self.last_offer_lists[user] = offer_list
        return offer_list

    def get_registered_users(self):
        return list(self.factories.keys())

    def create_factory(self, user, item, factory_level=1):
        if user not in self.factories:
            self.factories[user] = {}
        factory_id = self._next_id()
        factory = Factory(self, user, item, factory_id, factory_level)
        self.factories[user][factory_id] = factory
        return factory

    def get_factory(self, user, factory_id, by_nickname=False):
        if user in self.factories:
            if by_nickname:
                for f_id in self.factories[user]:
                    nick = self.factories[user][f_id].nickname
                    if nick is not None and nick == factory_id:
                        return self.factories[user][f_id]
            elif factory_id in self.factories[user]:
                return self.factories[user][factory_id]
        return None

    def get_inventory(self, user, item):
        if user in self.inventory:
            if item in self.inventory[user]:
                return self.inventory[user][item]
        return 0

    def set_inventory(self, user, item, amount, note=""):
        if user not in self.inventory:
            self.inventory[user] = {}
        self.inventory[user][item] = amount
        if note is not None:
            if note != "":
                note = "{" + note + "}"
                self.add_transaction(user, "Your **" + item + "** inventory was set to **" + str(amount) + "** " + note)

    def add_inventory(self, user, item, amount, note=""):
        if self.running:
            self.set_inventory(user, item, self.get_inventory(user, item) + amount, None)
            if note is not None:
                if note != "":
                    note = "{" + note + "}"
                self.add_transaction(user, "You had **" + str(amount) + " " + item + "** added to your inventory (Total: " + str(self.get_inventory(user, item)) + ") " + note)

    def exchange_inventory(self, user_from, user_to, item, amount, note=""):
        self.add_inventory(user_from, item, -amount, None)
        self.add_inventory(user_to, item, amount, None)
        if note is not None:
            if note != "":
                note = "{" + note + "}"
            self.add_transaction(user_from, "You sent **" + str(amount) + " " + item + "** to " + user_to + " (Total: **" + str(self.get_inventory(user_from, item)) + " " + item + "**) " + note)
            self.add_transaction(user_to, "You recieved **" + str(amount) + " " + item + "** from " + user_from + " (Total: **" + str(self.get_inventory(user_to, item)) + " " + item + "**) " + note)

    def get_trade(self, user_from, user_to):
        if user_from in self.trading:
            if user_to in self.trading[user_from]:
                return self.trading[user_from][user_to]
        return None

    def check_trade(self, user_from, user_to, items_from, items_to):
        for item in items_from:
            if item == "$$$":
                if self.get_money(user_from) < items_from[item]:
                    return Market.TRADE_FROM_NOT_ENOUGH_MONEY
            elif self.get_inventory(user_from, item) < items_from[item]:
                return Market.TRADE_FROM_NOT_ENOUGH_ITEM
        for item in items_to:
            if item == "$$$":
                if self.get_money(user_to) < items_to[item]:
                    return Market.TRADE_TO_NOT_ENOUGH_MONEY
            elif self.get_inventory(user_to, item) < items_to[item]:
                return Market.TRADE_TO_NOT_ENOUGH_ITEM
        return Market.TRADE_SUCCESS

    def create_trade_offer(self, user_from, user_from_name, user_to, user_to_name, items_from, items_to):
        result = self.check_trade(user_from, user_to, items_from, items_to)
        if result == 0:
            if user_from not in self.trading:
                self.trading[user_from] = {}
                self.trading[user_from]["offers"] = []
            if user_to not in self.trading:
                self.trading[user_to] = {}
                self.trading[user_to]["offers"] = []
            if user_to in self.trading[user_from]:
                return Market.TRADE_ALREADY_EXISTS
            else:
                self.trading[user_to]["offers"].append(user_from)
                self.trading[user_from][user_to] = {"from": items_from, "from_name": user_from_name, "to_name": user_to_name, "to": items_to}
        return result

    def accept_trade(self, user_from, user_to):
        if user_from in self.trading and user_to in self.trading[user_from]:
            trade = self.trading[user_from][user_to]
            result = self.check_trade(user_from, user_to, trade["from"], trade["to"])
            if result == Market.TRADE_SUCCESS:
                for item in trade["from"]:
                    self.exchange_inventory(user_from, user_to, item, trade["from"][item])
                for item in trade["to"]:
                    self.exchange_inventory(user_to, user_from, item, trade["to"][item])
            if user_from in self.trading[user_to]["offers"]:
                self.trading[user_to]["offers"].remove(user_from)
            del self.trading[user_from][user_to]
            return [result, trade]
        else:
            return [Market.TRADE_DOESNT_EXIST, None]

    def cancel_trade(self, user_from, user_to):
        if user_from in self.trading and user_to in self.trading[user_from]:
            trade = self.trading[user_from][user_to]
            if user_from in self.trading[user_to]["offers"]:
                self.trading[user_to]["offers"].remove(user_from)
            del self.trading[user_from][user_to]
            return [Market.TRADE_SUCCESS, trade]
        else:
            return [Market.TRADE_DOESNT_EXIST, None]

    def get_trades_from(self, user):
        result = []
        if user in self.trading:
            for user_to in self.trading[user]:
                if is_number(user_to):
                    result.append(user_to)
        return result

    def get_trades_to(self, user):
        if user in self.trading:
            return self.trading[user]["offers"]
        return []

    def get_inventory_items(self, user):
        if user in self.inventory:
            return list(self.inventory[user].keys())
        return []

    def get_money(self, user):
        if user in self.money:
            return self.money[user]
        return 0

    def add_transaction(self, user, transaction):
        if user not in self.money_history:
            self.money_history[user] = []
        self.money_history[user].append(transaction + "  [Balance: **$" + str(self.get_money(user)) + "**]")

    def get_transations(self, user):
        if user in self.money_history:
            return self.money_history[user]
        return []

    def set_money(self, user, money, note=""):
        self.money[user] = money
        if note is not None:
            if note != "":
                note = "{" + note + "}"
            self.add_transaction(user, "Your balance was set to **$" + str(money) + "**  " + note)

    def give_money(self, user, amount, note=""):
        self.set_money(user, self.get_money(user) + amount, None)
        if note is not None:
            if note != "":
                note = "{" + note + "}"
            if amount > 0:
                self.add_transaction(user, "You were gifted **$" + str(amount) + "**  " + note)
            elif amount < 0:
                self.add_transaction(user, "You had **$" + str(-amount) + "** taken from you!  " + note)

    def exchange_money(self, user_from, user_to, amount, note=""):
        self.give_money(user_from, -amount, None)
        self.give_money(user_to, amount, None)
        if note is not None:
            if note != "":
                note = "{" + note + "}"
            self.add_transaction(user_from, "You sent **$" + str(amount) + "** to " + user_to + "  " + note)
            self.add_transaction(user_to, "You received **$" + str(amount) + "** from " + user_from + "  " + note)

    def _next_id(self):
        self.market["___last_id___"] += 1
        return str(self.market["___last_id___"])

    def get_market_min_price(self, item):
        if item in self.market:
            return self.market[item]["min"]
        return 0

    def calculate_market_min_price(self, item):
        if item in self.market:
            for item_id in self.market[item]:
                if is_number(item_id):
                    if self.market[item][item_id]["price"] < self.market[item]["min"]:
                        self.market[item]["min"] = self.market[item][item_id]["price"]

    def get_market_amount(self, item, price=-1, exact=False):
        if item in self.market:
            if price == -1:
                return self.market[item]["total"]
            elif price >= 0:
                total = 0
                for item_id in self.market[item]:
                    if is_number(item_id):
                        if (self.market[item][item_id]["price"] == price and exact) or (self.market[item][item_id]["price"] <= price and not exact):
                            total += self.market[item][item_id]["amount"]
                return total
        return 0

    def calculate_market_amount(self, item):
        if item in self.market:
            self.market[item]["total"] = 0
            for item_id in self.market[item]:
                if is_number(item_id):
                    self.market[item]["total"] += self.market[item][item_id]["amount"]

    def get_offer_min_price(self, item):
        if item in self.offers:
            return self.offers[item]["min"]
        return -1

    def calculate_offer_min_price(self, item):
        if item in self.offers:
            for item_id in self.offers[item]:
                if is_number(item_id):
                    if self.offers[item][item_id]["price"] < self.offers[item]["min"]:
                        self.offers[item]["min"] = self.offers[item][item_id]["price"]

    def get_offer_amount(self, item, price=-1, exact=False):
        if item in self.offers:
            if price == -1:
                return self.offers[item]["total"]
            elif price >= 0:
                total = 0
                for item_id in self.offers[item]:
                    if is_number(item_id):
                        if (self.offers[item][item_id]["price"] == price and exact) or (self.offers[item][item_id]["price"] <= price and not exact):
                            total += self.offers[item][item_id]["amount"]
                return total
        return 0

    def calculate_offer_amount(self, item):
        if item in self.offers:
            self.offers[item]["total"] = 0
            for item_id in self.offers[item]:
                if is_number(item_id):
                    self.offers[item]["total"] += self.offers[item][item_id]["amount"]

    def get_market_price(self, item, amount):
        if self.get_market_amount(item) > amount:
            ordered_prices = []
            for item_id in self.market[item]:
                if is_number(item_id):
                    obj = self.market[item][item_id]
                    done = False
                    for i in range(len(ordered_prices)):
                        if ordered_prices[i]["price"] > obj["price"]:
                            new_obj = copy.copy(obj)
                            ordered_prices = ordered_prices[:i] + [new_obj] + ordered_prices[i:]
                            done = True
                            break
                        elif ordered_prices[i]["price"] == obj["price"]:
                            ordered_prices[i]["amount"] += obj["amount"]
                            done = True
                            break
                    if not done:
                        new_obj = copy.copy(obj)
                        ordered_prices = ordered_prices + [new_obj]
            price = 0
            for obj in ordered_prices:
                if obj["amount"] > amount:
                    price += obj["price"] * amount
                else:
                    price = price + (obj["amount"] * obj["price"])
                    amount -= obj["amount"]
            return price
        return -1

    def get_offer_price(self, item, amount):
        if self.get_offer_amount(item) > amount:
            ordered_prices = []
            for item_id in self.offers[item]:
                if is_number(item_id):
                    obj = self.offers[item][item_id]
                    done = False
                    for i in range(len(ordered_prices)):
                        if ordered_prices[i]["price"] > obj["price"]:
                            new_obj = copy.copy(obj)
                            ordered_prices = ordered_prices[:i] + [new_obj] + ordered_prices[i:]
                            done = True
                            break
                        elif ordered_prices[i]["price"] == obj["price"]:
                            ordered_prices[i]["amount"] += obj["amount"]
                            done = True
                            break
                    if not done:
                        ordered_prices = ordered_prices + [copy.copy(obj)]
            price = 0
            for obj in ordered_prices:
                if obj["amount"] > amount:
                    price += obj["price"] * amount
                else:
                    price = price + (obj["amount"] * obj["price"])
                    amount -= obj["amount"]
            return price
        return 0

    def sell_item(self, user_id, item, amount, price):
        if self.get_inventory(user_id, item) > amount:
            if item not in self.market:
                self.market[item] = {}
                self.market[item]["total"] = 0
                self.market[item]["min"] = -1
            item_id = self._next_id()
            self.market[item][item_id] = {"amount": amount, "price": price, "item": item, "item_id": item_id, "user": user_id}
            self.market[item]["total"] += amount
            self.add_inventory(user_id, item, -amount)
            if price < self.market[item]["min"] or self.market[item]["min"] < 0:
                self.market[item]["min"] = price
            return item_id
        return -1

    def update_offers(self, item):
        if item in self.offers:
            temp_order = self.offers[item]["id_order"][:]
            for offer_id in temp_order:
                self.check_offer(item, offer_id)
            self.calculate_offer_amount(item)
        return False

    @staticmethod
    def stringify(obj_type, obj_list):
        result = []
        if obj_type == "trade":
            from_result = obj_list["from_name"] + " is offering " + obj_list["to_name"] + "\n```"
            to_result = "```in return for\n```"
            for item in obj_list["from"]:
                if item == "$$$":
                    from_result += "$" + str(obj_list["from"][item]) + "\n"
                else:
                    from_result += str(obj_list["from"][item]) + " " + item + "\n"
            for item in obj_list["to"]:
                if item == "$$$":
                    to_result += "$" + str(obj_list["to"][item]) + "\n"
                else:
                    to_result += str(obj_list["to"][item]) + " " + item + "\n"
            result = from_result + to_result + "```"
        else:
            for obj in obj_list:
                if obj_type == "offer":
                    result.append("Offering to buy **" + str(obj["amount"]) + " " + obj["item"] + "** at a price of **$" + str(obj["price"]) +"** per unit (investment: **$" + str(obj["investment"]) + "**)")
                elif obj_type == "market":
                    result.append("Selling **" + str(obj["amount"]) + " " + obj["item"] + "** at a price of **$" + str(obj["price"]) + "** per unit (total price: **$" + str(obj["amount"] * obj["price"]) + "**)")
        return result

    def offer_price(self, user_id, item, amount, price):
        investment = amount*price
        if self.get_money(user_id) >= investment:
            if item not in self.offers:
                self.offers[item] = {}
                self.offers[item]["total"] = 0
                self.offers[item]["min"] = 0
                self.offers[item]["id_order"] = []
            item_id = self._next_id()
            self.offers[item][item_id] = {"amount": amount, "price": price, "user": user_id, "item": item, "item_id": item_id, "investment": investment}
            self.offers[item]["total"] += amount
            self.offers[item]["id_order"].append(item_id)
            self.give_money(user_id, -investment, "offer investment")
            if price < self.offers[item]["min"] or self.offers[item]["min"] < 0:
                self.market[item]["min"] = price
            return item_id
        return -1

    def cancel_offer(self, offer):
        if offer["item"] in self.offers:
            if offer["item_id"] in self.offers[offer["item"]]:
                self.give_money(offer["user"], offer["investment"], "offer investment return")
                del self.offers[offer["item"]][offer["item_id"]]
                return True
        return False

    def buy_item(self, user_id, item, amount):
        if item in self.market:
            if self.get_market_amount(item) > amount:
                ordered_prices = []
                for item_id in self.market[item]:
                    if is_number(item_id):
                        obj = self.market[item][item_id]
                        done = False
                        for i in range(len(ordered_prices)):
                            if ordered_prices[i]["price"] > obj["price"]:
                                new_obj = copy.copy(obj)
                                ordered_prices = ordered_prices[:i] + [new_obj] + ordered_prices[i:]
                                done = True
                                break
                            elif ordered_prices[i]["price"] == obj["price"]:
                                ordered_prices[i]["amount"] += obj["amount"]
                                done = True
                                break
                        if not done:
                            ordered_prices = ordered_prices + [copy.copy(obj)]
                temp_amount = amount
                price = 0
                for obj in ordered_prices:
                    if obj["amount"] >= temp_amount:
                        price += obj["price"] * temp_amount
                        break
                    else:
                        price = price + (obj["amount"] * obj["price"])
                        temp_amount -= obj["amount"]
                if price <= self.get_money(user_id):
                    original_amount = amount
                    for obj in ordered_prices:
                        if obj["amount"] >= amount:
                            exch_money = obj["price"] * amount
                            self.exchange_money(user_id, obj["user"], exch_money, "trading item (**" + str(amount) + " " + item + "**)")
                            self.market[item][obj["item_id"]]["amount"] -= amount
                            break
                        else:
                            exch_money = obj["amount"] * obj["price"]
                            self.exchange_money(user_id, obj["user"], exch_money, "trading item (**" + str(amount) + " " + item + "**)")
                            amount -= obj["amount"]
                            del self.market[item][obj["item_id"]]
                    self.add_inventory(user_id, item, original_amount)
                    self.calculate_market_amount(item)
                    return [Market.BUY_SUCCESS, price]
                return [Market.BUY_NOT_ENOUGH_MONEY, price]  # not enough money
            return [Market.BUY_NOT_ENOUGH_ITEM, -1]  # not enough items
        return [Market.BUY_NO_SUCH_ITEM, -1]  # item doesn't exist

    def check_offer(self, item, offer_id):
        if item in self.offers:
            if offer_id in self.offers:
                obj = self.offers[offer_id]
                amt = self.get_market_amount(item, obj[1])
                if amt >= obj["amount"]:  # offer can be fulfilled
                    self.give_money(obj["user"], obj["investment"], "returning investment")
                    self.buy_item(obj["user"], item, obj["amount"])
                    self.offers[item]["id_order"].remove(offer_id)
                    del self.offers[item][offer_id]
                elif amt > 0:  # offer can be reduced
                    price = self.get_market_price(item, obj["price"])
                    obj["investment"] -= price
                    obj["amount"] -= amt
                    self.give_money(obj["user"], price, "partially returning investment")
                    if self.buy_item(obj["user"], item, amt)[0] != Market.BUY_SUCCESS:
                        self.give_money(obj["user"], -price, "failed to buy - retaking investment")

