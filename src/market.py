import threading, math, copy, json, os, shutil, datetime, time, traceback, random

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class Factory:
    FACTORY_UPGRADES = [
        "auto"
    ]
    FACTORY_COSTS = {
        "auto": [
            "Upgrades your factories automatic production capabilities. Level 1 is required to be able to automatically produce things.",
            {
                "base": [100, 100],
                "__RESULT__": ['self.auto_produce = self.get_amount(self.market.factories["produce_delay"])',
                               'self.auto_efficieny = 0.8'],
                "__DESC__": "Allows your factory to produce automatically with 80% efficiency"
            },
            {
                "base": [150, 150],
                "__RESULT__": ['self.start_auto_produce(self.market.factories["produce_delay"], eff=0.85)'],
                "__DESC__": "Allows your factory to produce items automatically with 85% efficiency"
            }
        ]
    }

    def __init__(self, market, user, item, factory_id, sellable=False):
        self.market = market
        self.user = user
        self.item = item
        self.time_scale = 5
        self.id = factory_id
        self.nickname = None

        self.auto_produce = -1
        self.auto_efficieny = -1
        self.production_amount = 0
        self.production_start = time.time()
        self.producing = 0
        self.sellable = sellable

        self.upgrade_levels = {
            "time_scaling": 1,
            "auto": 0
        }

    def get_save_json(self):
        return {
            "user": self.user,
            "item": self.item,
            "time_scale": self.time_scale,
            "auto_efficiency": self.auto_efficieny,
            "producing": self.producing,
            "auto_produce": self.auto_produce,
            "upgrade_levels":  self.upgrade_levels,
            "id": self.id,
            "nickname": self.nickname,
            "sellable": self.sellable
        }

    @staticmethod
    def load_from_json(market, json_data):
        factory = Factory(market, json_data["user"], json_data["item"], json_data["id"])
        factory.time_scale = json_data["time_scale"]
        factory.auto_efficieny = json_data["auto_efficiency"]
        factory.auto_produce = json_data["auto_produce"]
        factory.upgrade_levels = json_data["upgrade_levels"]
        factory.nickname = json_data["nickname"]
        factory.producing = json_data["producing"]
        factory.sellable = json_data["sellable"]
        if not factory.user in market.factories:
            market.factories[factory.user] = {}
            market.factories[factory.user][factory.id] = factory
        if factory.producing == 2:
            factory.start_auto_produce(market.factories["produce_delay"])
        else:
            factory.producing = 0

    def get_info(self):
        auto_line = "Cannot"
        if self.auto_efficieny > 0:
            auto_line = "Can"
        elap = int(time.time() - self.production_start)
        production_line = "It has not been producing any items for " + str(elap) + " seconds"
        if self.producing == 1:
            production_line = "It is currently producing **" + str(self.production_amount) + " " + self.item + "**. It started **" + str(elap) + "** seconds ago"
        elif self.producing == 2:
            production_line = "It is currently automatically producing **" + str(self.auto_produce) + " " + self.item + "** every " + str(self.market.factories["produce_delay"]) + " seconds. It started **" + str(elap) + "** seconds ago"
        sell_line = "It is sellable"
        if not self.sellable:
            sell_line = "It is not sellable"
        lines = [
            "ID: " + self.id,
            "Name: " + self.get_name(),
            sell_line,
            production_line,
            "It's production speed level is **" + str(self.upgrade_levels["time_scaling"]) + "**",
            "It's automated efficiency level is **" + str(self.upgrade_levels["auto"]) + "**",
            "Produces ** " + str(self.get_amount(30)) + " " + self.item + "** in **30** seconds",
            auto_line + " produce items automatically"
        ]
        if self.auto_efficieny > 0:
            lines.append("Has an automated efficiency of **" + str(self.auto_efficieny * 100) + "%**")
        return "\n".join(lines)

    def get_name(self):
        if self.nickname is not None:
            return self.nickname
        return self.id

    # upgrade: { item_type = [amount_1, ...] }
    # mats: { item_type = [item_name_1, ...] }
    def _use_upgrade(self, upgrade, mats):
        to_use = []
        for item_type in upgrade:
            if not item_type.startswith("_"):
                if item_type == "$$$" or (item_type in mats and len(upgrade[item_type]) == len(mats[item_type])):
                    if item_type == "$$$":
                        if self.market.get_money(self.user) >= upgrade[item_type]:
                            to_use.append(obj)
                        else:
                            return "money"
                    else:
                        for i in range(len(upgrade[item_type])):
                            obj = [mats[item_type][i], upgrade[item_type][i]]
                            if (obj[0] == "$$$" and self.market.get_money(self.user) >= obj[1]) or (obj[0] != "$$$" and self.market.get_inventory(self.user, obj[0]) >= obj[1]):
                                to_use.append(obj)
                            else:
                                return obj[0]
                else:
                    return item_type + " resources"
        note = "upgrading factory " + self.get_name()
        for obj in to_use:
            if obj[0] == "$$$":
                self.market.give_money(self.user, -obj[1], note)
            else:
                self.market.add_inventory(self.user, obj[0], -obj[1], note)
        for code_block in upgrade["__RESULT__"]:
            #print(code_block)
            eval(code_block)
        return None

    def upgrade(self, name, mats):
        if name in self.upgrade_levels:
            if self.upgrade_levels[name] + 1 == len(Factory.FACTORY_COSTS[name]):
                return "MAX"
            else:
                result = self._use_upgrade(Factory.FACTORY_COSTS[name][self.upgrade_levels[name]+1], mats)
                if result is None:
                    self.upgrade_levels[name] += 1
                self.market.update_achievs(self.user)
                return result
        return "ERROR"

    def set_level(self, upgrade_type, level):
        if upgrade_type in self.upgrade_levels:
            if 1 <= level <= len(Factory.FACTORY_COSTS[upgrade_type]):
                for code_block in Factory.FACTORY_COSTS[upgrade_type][level]:
                    eval(code_block)

    def start_auto_produce(self, delay, time_scaling=-1, eff=-1):
        if time_scaling < 0:
            time_scaling = self.time_scale
        if eff != -1:
            self.auto_efficieny = eff
        self.production_start = time.time()
        self.auto_produce = math.ceil(self.auto_efficieny * self.get_amount(delay, time_scaling))
        if self not in self.market.auto_factories:
            self.market.auto_factories.append(self)
        self.producing = 2

    def stop_auto(self):
        self.auto_produce = -1
        if self in self.market.auto_factories:
            self.market.auto_factories.remove(self)
        self.producing = 0
        self.production_start = time.time()

    def set_nickname(self, nickname):
        self.nickname = nickname

    def get_amount(self, time_taken, time_scaling=-1):
        if time_scaling < 0:
            time_scaling = self.time_scale
        return math.floor((time_taken * math.log(time_scaling * 0.95)) / 10)

    def get_time_taken(self, amount, time_scaling=-1):
        if time_scaling < 0:
            time_scaling = self.time_scale
        return (amount*10) / math.log(time_scaling * 0.95)

    def raw_produce(self, amount=-1):
        if self.producing == 1:
            amount = self.production_amount
            self.producing = 0
            self.production_start = time.time()
        self.market.add_inventory(self.user, self.item, amount, None)

    def produce(self, amount):
        if not self.producing:
            delay = self.get_time_taken(amount)
            self.production_amount = amount
            self.producing = 1
            self.production_start = time.time()
            self.market.queue_event(delay, self.raw_produce)
            return delay
        return -1

class Chest:
    # types: $$$ for money, {item|?item_type} for factory, ?item_type for a random item from the item_type, item for an item
    # factories: "sellable": True|False, "levels": [ { "type": upgrade_type, "lower": lower level, "upper", upper level }, .. ]
    LOOT_GRADE_NAMES = [
        "daily reward"
    ]
    LOOT = [
        [
            {"name": "daily reward", "lower": 10, "upper": 10},
            {"type": "$$$", "lower": 50, "upper": 110},
            {"type": "?base", "lower": 20, "upper": 60}
        ]
    ]
    def __init__(self, market, user, grade):
        self.market = market
        self.user = user
        self.grade = grade

    def open(self):
        loot = Chest.LOOT[self.grade]
        amount = random.randint(loot[0]["lower"], loot[0]["upper"])
        rewards = []
        for i in range(amount):
            reward = loot[random.randint(1, len(loot)-1)]
            if reward["type"] == "$$$": # money
                amt = random.randint(reward["lower"], reward["upper"])
                self.market.give_money(self.user, amt, "chest reward")
                done = False
                for i in range(len(rewards)):
                    if rewards[i].startswith("$"):
                        rewards[i] = "$" + str( int(rewards[i][1:]) + amt )
                        done = True
                        break
                if not done:
                    rewards.append("$" + str(amt))
            elif reward["type"].startswith("{") and reward["type"].endswith("}"): # factory
                item = reward["type"][1:-1]
                if item.startswith("?"):
                    item_list = self.market.get_items_from(item[1:])
                    item = random.randint(len(item_list)-1)
                sellable = True
                if "sellable" in reward:
                    sellable = reward["sellable"]
                factory = Factory(self.market, self.user, item, self.market._next_id(), sellable)
                if "levels" in reward:
                    for obj in reward["levels"]:
                        factory.set_level(obj["type"], random.randint(obj["lower"], obj["upper"]))
                if not self.user in self.market.factories:
                    self.market.factories[self.user] = {}
                self.market.factories[self.user][factory.id] = factory
                rewards.append("an " + item + " factory")
            else : # item type
                item = reward["type"]
                if item.startswith("?"):
                    item_list = self.market.get_items_from(item[1:])
                    item = item_list[random.randint(0, len(item_list)-1)]
                amt = random.randint(reward["lower"], reward["upper"])
                self.market.add_inventory(self.user, item, amt, "chest reward")
                done = False
                for i in range(len(rewards)):
                    if rewards[i].endswith(" " + item):
                        rewards[i] = str( int(rewards[i][:-len(" " + item)]) + amt ) + " " + item
                        done = True
                        break
                if not done:
                    rewards.append(str(amt) + " " + item)
        return rewards
class Market:
    ACHIEVEMENTS = {
        "Base": {
            "desc": ":package: Achievements to do with collecting resources:",
            "name": "base",
            "achievs": [
                {
                    "condition": lambda market, user: market.get_money(user) > 100,
                    "desc": "Have a balance of over $100"
                }
            ]
        }
    }

    BUY_NO_SUCH_ITEM = 0
    BUY_NOT_ENOUGH_ITEM = 1
    BUY_NOT_ENOUGH_MONEY = 2
    BUY_SUCCESS = 3

    TRADE_SUCCESS = 0
    TRADE_FROM_NOT_ENOUGH_MONEY = 1
    TRADE_FROM_NOT_ENOUGH_ITEM = 2
    TRADE_FROM_NO_SUCH_FACTORY = 7
    TRADE_FROM_UNSELLABLE_FACTORY = 9
    TRADE_TO_NOT_ENOUGH_MONEY = 3
    TRADE_TO_NOT_ENOUGH_ITEM = 4
    TRADE_TO_NO_SUCH_FACTORY = 8
    TRADE_TO_UNSELLABLE_FACTORY = 10
    TRADE_ALREADY_EXISTS = 5
    TRADE_DOESNT_EXIST = 6


    def __init__(self):
        self.running = True
        self.market = {}
        self.offers = {}
        self.money = {}
        self.inventory = {}
        self.factories = {}
        self.auto_factories = []
        self.money_history = {}
        self.last_offer_lists = {}
        self.last_market_lists = {}
        self.achievs = {}
        self.achievs["__mute__"] = []
        self.achiev_stack = []
        self.trading = {}
        self.item_types = {}
        self.refresh_cd = 0
        self.market["___last_id___"] = 100000
        self.inventory["save_delay"] = 60 # save every minute
        self.inventory["save_id"] = 0
        self.factories["produce_delay"] = 30

        self.chests = {}
        self.tags = {}
        self.tags["__tagban__"] = {}
        self.load()
        self.save_loop()
        self.produce_loop()

    def give_chest(self, user_id, grade):
        if not is_number(grade):
            if grade in Chest.LOOT_GRADE_NAMES:
                grade = Chest.LOOT_GRADE_NAMES.index(grade)
            else:
                return False
        grade = str(grade)
        if not user_id in self.chests:
            self.chests[user_id] = {}
        if grade in self.chests[user_id]:
            self.chests[user_id][grade] += 1
        else:
            self.chests[user_id][grade] = 1


    def has_achiev(self, user_id, name, index=-1):
        if user_id in self.achievs:
            if index >= 0:
                name = name + "_" + str(index)
            return name in self.achievs[user_id]
        return False

    def update_achievs(self, user_id):
        if not user_id in self.achievs:
            self.achievs[user_id] = []
        for title in Market.ACHIEVEMENTS:
            info = Market.ACHIEVEMENTS[title]
            for i in range(len(info["achievs"])):
                ach_name = info["name"] + "_" + str(i)
                if ach_name not in self.achievs[user_id] and info["achievs"][i]["condition"](self, user_id):
                    self.achievs[user_id].append(ach_name)
                    self.achiev_stack.append([user_id, ach_name])

    def wipe(self, user_id):
        for item in self.market:
            if user_id in self.market[item]:
                del self.market[item][user_id]
        for item in self.offers:
            if user_id in self.offers[item]:
                del self.market[item][user_id]
        if user_id in self.money:
            del self.money[user_id]
        if user_id in self.inventory:
            del self.inventory[user_id]
        if user_id in self.factories:
            for f_id in self.factories[user_id]:
                factory = self.factories[user_id][f_id]
                if factory in self.auto_factories:
                    self.auto_factories.remove(factory)
            del self.factories[user_id]
        if user_id in self.trading:
            offers = self.trading[user_id]["offers"]
            for uid in self.offers:
                if uid in self.tradinga and user_id in self.trading[uid]:
                    del self.trading[uid][user_id]
            del self.trading[user_id]

    def get_items_from(self, item_type):
        result = []
        for item in self.item_types:
            if self.item_types[item] == item_type:
                result.append(item)
        return result

    def get_item_type(self, item):
        if item in self.item_types:
            return self.item_types[item]
        return "item"

    def set_item_type(self, item, item_type):
        self.item_types[item] = item_type

    def delete_item_type(self, item):
        if item in self.item_types:
            del self.item_types[item]

    def auto_produce_loop(self):
        for factory in self.auto_factories:
            factory.raw_produce(factory.auto_produce)

    def produce_loop(self):
        if self.running:
            self.auto_produce_loop()
            threading.Timer(self.factories["produce_delay"], self.produce_loop).start()

    def save_loop(self):
        if self.running:
            self.save()
            threading.Timer(self.inventory["save_delay"], self.save_loop).start()

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
        to_save = ["market", "offers", "money", "inventory", "money_history", "trading", "item_types", "achievs", "chests", "tags"]
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
        try:
            total_data = {}
            for user in self.factories:
                if is_number(user):
                    for f_id in self.factories[user]:
                        total_data[f_id] = self.factories[user][f_id].get_save_json()
            f = open("data/" + dir_suffix + "factories.json", "w")
            json.dump(total_data, f)
            if not f.closed:
                f.close()
        except:
            traceback.print_exc()
            print("[SAVE ERROR] Failed to save factories")

        if dir_suffix != "":
            print("[BACKUP] Backed up, ID: " + dir_suffix + ", Save ID: " + str(self.inventory["save_id"]))
        else:
            print("[SAVE] Saved, ID: " + str(self.inventory["save_id"]))

    def load(self, dir_suffix=""):
        print("[LOAD] Loading...")
        if not os.path.exists("data/"):
            os.makedirs("data/")
        if os.path.exists("data/" + dir_suffix):
            to_load = ["market", "offers", "money", "inventory", "money_history", "trading", "item_types", "achievs", "chests", "tags"]
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
            try:
                file_name = "data/" + dir_suffix + "factories.json"
                if os.path.exists(file_name):
                    f = open(file_name, "r")
                    data = json.load(f)
                    for f_id in data:
                        Factory.load_from_json(self, data[f_id])
                    if not f.closed:
                        f.close()
                else:
                    print("[LOAD ERROR] Couldn't find file " + file_name)
            except:
                traceback.print_exc()
                print("[LOAD ERROR] Failed to load factories")
            if dir_suffix == "":
                print("[LOAD] Loaded!")
            else:
                print("[BACKUP] Loaded backup " + dir_suffix + ", Save ID: " + str(self.inventory["save_id"]))
        else:
            print("[BACKUP] Invalid backup name " + dir_suffix)

    def save_backup(self, bot, backup_name):
        index = 0
        og_backup_name = backup_name
        while os.path.exists("data/" + backup_name + "/"):
            index += 1
            backup_name = og_backup_name + str(index)
        self.save(backup_name + "/")
        print("[BACKUP] Saving backup metadata: ")
        meta_data = {
            "save_id": self.inventory["save_id"],
            "timestamp": datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
            "bot_version": bot.version,
            "users": len(self.get_registered_users()),
            "bot_name": bot.name,
            "commands": bot.help_page.registered_commands
        }
        f = open("data/" + backup_name + "/__meta__.json", "w")
        json.dump(meta_data, f)
        if not f.closed:
            f.close()
        print("[BACKUP] Done!")

    def load_backup(self, backup_name):
        if os.path.exists("data/" + backup_name + "/"):
            self.load(backup_name + "/")
            return True
        return False

    def delete_backup(self, backup_name):
        if os.path.exists("data/" + backup_name + "/"):
            shutil.rmtree("data/" + backup_name + "/")
            return True
        return False

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

    def exchange_factory(self, user_from, user_to, factory_name):
        factory = self.get_factory(user_from, factory_name)
        if factory is not None:
            del self.factories[user_from][factory.id]
            self.factories[user_to][factory.id] = factory
            factory.user = user_to
            self.add_transaction(user_from, "You gave " + user_to + " your factory (name: " + factory.get_name() +"; id: " + factory.id + ")")
            self.add_transaction(user_to, "You were a factory by " + user_from + " (name: " + factory.get_name() + "; id: " + factory.id + ")")



    def create_factory(self, user, item, sellable=False):
        if user not in self.factories:
            self.factories[user] = {}
        factory_id = self._next_id()
        factory = Factory(self, user, item, factory_id, sellable)
        self.update_achievs(user)
        self.factories[user][factory_id] = factory
        return factory

    def get_factory(self, user, factory_id):
        by_nickname = not is_number(factory_id)
        if user in self.factories:
            if by_nickname:
                for f_id in self.factories[user]:
                    nick = self.factories[user][f_id].nickname
                    if nick is not None and nick == factory_id:
                        return self.factories[user][f_id]
            elif factory_id in self.factories[user]:
                return self.factories[user][factory_id]
        return None

    def get_factory_name_list(self, user):
        names = []
        if user in self.factories:
            for f_id in self.factories[user]:
                factory = self.factories[user][f_id]
                if factory.nickname is not None:
                    names.append(factory.nickname)
                else:
                    names.append(f_id)
        return names

    def set_factory_nick(self, user, old_nick, new_nick):
        factory = self.get_factory(user, old_nick)
        if factory is not None:
            factory.nickname = new_nick
            return True
        return False

    def get_inventory(self, user, item):
        if user in self.inventory:
            if item in self.inventory[user]:
                return self.inventory[user][item]
        return 0

    def set_inventory(self, user, item, amount, note=""):
        if user not in self.inventory:
            self.inventory[user] = {}
        self.inventory[user][item] = amount
        self.update_achievs(user)
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
            elif item.startswith("!!!"): # factory
                factory = self.get_factory(user_from, items_from[item])
                if factory is None:
                    return Market.TRADE_FROM_NO_SUCH_FACTORY
                elif not factory.sellable:
                    return Market.TRADE_FROM_UNSELLABLE_FACTORY
            elif self.get_inventory(user_from, item) < items_from[item]:
                return Market.TRADE_FROM_NOT_ENOUGH_ITEM
        for item in items_to:
            if item == "$$$":
                if self.get_money(user_to) < items_to[item]:
                    return Market.TRADE_TO_NOT_ENOUGH_MONEY
            elif item.startswith("!!!"):
                factory = self.get_factory(user_from, items_from[item])
                if factory is None:
                    return Market.TRADE_TO_NO_SUCH_FACTORY
                elif not factory.sellable:
                    return Market.TRADE_TO_UNSELLABLE_FACTORY
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

    def _accept_item(self, user_from, user_to, item, trade):
        if item == "$$$":
            self.exchange_money(user_from, user_to, trade["from"][item])
        elif item.startswith("!!!"):
            self.exchange_factory(user_from, user_to, trade["from"][item])
        else:
            self.exchange_inventory(user_from, user_to, item, trade["from"][item])

    def accept_trade(self, user_from, user_to):
        if user_from in self.trading and user_to in self.trading[user_from]:
            trade = self.trading[user_from][user_to]
            result = self.check_trade(user_from, user_to, trade["from"], trade["to"])
            if result == Market.TRADE_SUCCESS:
                for item in trade["from"]:
                    self._accept_item(user_from, user_to, item, trade)
                for item in trade["to"]:
                    self._accept_item(user_from, user_to, item, trade)
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
        self.update_achievs(user)
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

    def refresh(self, item=None):
        if time.time() - self.refresh_cd < 60:
            if item is None:
                for item in self.market:
                    self.calculate_market_min_price(item)
                    self.calculate_market_amount(item)
                for item in self.offers:
                    self.calculate_offer_amount(item)
                    self.calculate_offer_min_price(item)
            else:
                if item in self.market:
                    self.calculate_market_amount(item)
                    self.calculate_offer_min_price(item)
                if item in self.offers:
                    self.calculate_offer_min_price(item)
                    self.calculate_offer_amount(item)
            return True
        else:
            return False

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

    def cancel_sale(self, sale):
        if sale["item"] in self.market:
            if sale["item_id"] in self.market[sale["item"]]:
                self.add_inventory(sale["user"], sale["item"], sale["amount"])
                del self.market[sale["item"]][sale["item_id"]]
                self.calculate_market_amount(sale["item"])
                self.calculate_market_min_price(sale["item"])
                return True
        return False

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
                elif obj_type == "sale":
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
                self.calculate_offer_amount(offer["item"])
                self.calculate_offer_min_price(offer["item"])
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

