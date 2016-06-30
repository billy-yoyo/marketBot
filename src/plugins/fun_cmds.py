import traceback, random, asyncio, market, aiohttp, json, textart, os, copy, styload, math, poker, operator
from PIL import Image
from difflib import SequenceMatcher
from os import listdir

import requests
import re

ball_8 = [
        "It is certain",
        "It is decidedly so",
        "Without a doubt",
        "Yes, definitely",
        "You may rely on it",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes",
        "Reply hazy try again",
        "Ask again later",
        "Better not tell you now",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "My reply is no",
        "My sources say no",
        "Outlook not so good",
        "Very doubtful"
    ]

card_template = "\n".join([
    "+-----+",
    "|!   |",
    "|  ?  |",
    "|   :|",
    "+-----+"
])
suits = {"H": "♥", "D": "♦", "S": "♠", "C": "♣"}
cards1 = {"2": "2 ", "3": "3 ", "4": "4 ", "5": "5 ", "6": "6 ", "7": "7 ", "8": "8 ", "9": "9 ",
          "T": "10", "J": "J ", "Q": "Q ", "K": "K ", "A": "A "}
cards2 = {"2": " 2", "3": " 3", "4": " 4", "5": " 5", "6": " 6", "7": " 7", "8": " 8", "9": " 9",
          "T": "10", "J": " J", "Q": " Q", "K": " K", "A": " A"}

def get_card(card):
    return card_template.replace("?", suits[card[1]]).replace("!", cards1[card[0]]).replace(":", cards2[card[0]])

def get_hand_str(raw_cards):
    card_list = raw_cards.split(" ")
    lines = ["", "", "", "", ""]
    for card in card_list:
        if len(card) == 2: # is card
            for i, line in enumerate(get_card(card).split("\n")):
                lines[i] += " " + line
        elif len(card) == 1: # is label of length 1
            lines[0] += "    "
            lines[1] += "    "
            lines[2] += "  " + card + " "
            lines[3] += "    "
            lines[4] += "    "
        elif len(card) == 3: # is label of length 3
            for i in range(len(lines)): lines[i] += "     "
            lines[0] += "  " + card[0] + " "
            lines[1] += "    "
            lines[2] += "  " + card[1] + " "
            lines[3] += "    "
            lines[4] += "  " + card[2] + " "
        elif len(card) == 4: # is a label of length 4
            lines[0] += "    "
            lines[1] += "  " + card[0] + " "
            lines[2] += "  " + card[1] + " "
            lines[3] += "  " + card[2] + " "
            lines[4] += "  " + card[3] + " "
        elif len(card) == 5:
            for i in range(5):
                lines[i] += "  " + card[i] + " "

    return "```diff\n" + "\n".join(lines) + "\n```"


class PokerGame:
    @staticmethod
    def valid_float(v, acc=2):
        sv = str(v)
        if "." in sv:
            return len(sv[sv.find(".")+1:]) <= acc
        return True

    def __init__(self, bot, invited, origin, start_money=100, ante=1):
        self.bot = bot
        self.invited = invited
        self.start_money = start_money
        self.ante = ante
        self.origin = origin
        self.accepted = []
        self.declined = []
        self.rot_offset = 0

        self.started = False

    def _origin(self, msg):
        yield from self.bot.client.send_message(self.origin, msg)

    def _pm(self, user, msg):
        yield from self.bot.client.send_message(user, msg)

    def _check(self):
        if not self.started:
            if len(self.accepted) + len(self.declined) == len(self.invited): # everyone has responded
                if len(self.accepted) > 1: # at least two people responded
                    yield from self._origin("Everyone has responded, game is now starting with " + ", ".join([x.name for x in self.accepted]))
                    yield from self._start_round(True)
                else:
                    yield from self._origin("Not enough people accepted, ending game.")

    def _start_round(self, init=False):
        self.started = True
        if not init:
            yield from self._origin("```\nStarting next round!\n```")
            new_accepted = []
            for user in self.accepted:
                if self._money(user) < self.ante:
                    self.accepted.remove(user)
                    yield from self._origin(user.mention + " can't afford the ante so they're out! Use " + self.bot.prefix + "poker leave to leave the game" )
                else:
                    new_accepted.append(user)
            self.accepted = new_accepted

        if len(self.accepted) > 1:
            numbers = "23456789TJQKA"
            suits = "HSCD"
            self.deck = ["2C"] * 52
            self.hands = {}
            self.bets = {}
            if init:
                self.money = {}
            self.rotation = []
            self.cur_user = 0
            self.pot = len(self.accepted) * self.ante
            self.round = {"checked": 0, "bet": self.ante, "table": "TABLE", "allin": []}

            indexs = [x for x in range(52)]
            for number in numbers:
                for suit in suits:
                    index = random.choice(indexs)
                    self.deck[index] = number + suit
                    indexs.remove(index)


            for user in self.accepted:
                self.hands[user.id] = "CARDS " + " ".join(self.deck[:2])
                self.bets[user.id] = self.ante
                self.deck = self.deck[2:]
                self.rotation.append(user)
                if init:
                    self.money[user.id] = self.start_money
                yield from self._pm(user, get_hand_str(self.hands[user.id] + " " + self.round["table"]))

            for i in range(self.rot_offset % len(self.rotation)):
                self.rotation = [self.rotation[-1]] + self.rotation[:-1]

            yield from self._origin(self.rotation[0].mention + " it's your turn!")

            self.rot_offset += 1
        else:
            yield from self._origin(self.accepted[0].mention + ", everyone else has left so the game is now ending.")
            self.started = False
            del self.bot.market.games["poker"][self.accepted[0].id]

    def _next_card(self, force_win=False):
        if len(self.round["table"].split(" ")) == 1 and not force_win: # add 3 cards
            self.round["table"] += " " + " ".join(self.deck[:3])
            self.deck = self.deck[3:]
        elif len(self.round["table"].split(" ")) < 6 and not force_win: # add 1 card
            self.round["table"] += " " + self.deck[0]
            self.deck = self.deck[1:]
        else: # round over, see who won
            if len(self.rotation) == 1:
                yield from self._origin(self.rotation[0].mention + " wins the pot of `$" + str(self.pot) + "` (everyone else folded)")
                for uid in self.bets:
                    self.money[uid] -= self.bets[uid]
                self.money[self.rotation[0].id] += self.pot
            else:
                score_map = [
                    "high card",
                    "pair",
                    "two Pairs",
                    "three of a kind",
                    "straight",
                    "flush",
                    "full House",
                    "four of a kind",
                    "straight Flush",
                    "royal Flush"
                ]

                results = {}
                id_map = {}
                cached = {u.id: {v.id: -1 for v in self.rotation if v != u} for u in self.rotation}
                for user in self.rotation:
                    self.hands[user.id] = [x for x in self.hands[user.id].split(" ") + self.round["table"].split(" ") if len(x) == 2]
                best_scores = {u.id: None for u in self.rotation}
                for user1 in self.rotation:
                    wins = 0
                    for user2 in self.rotation:
                        if user1 != user2:
                            result = 0
                            if cached[user2.id][user1.id] > -1:
                                result = cached[user2.id][user1.id]
                                if result == 1:
                                    result = 2
                                elif result == 2:
                                    result = 1
                            else:
                                raw_result = poker.resolve(self.hands[user1.id], self.hands[user2.id])
                                best_scores[user1.id] = raw_result[1]
                                best_scores[user2.id] = raw_result[2]
                                cached[user1.id][user2.id] = raw_result[0]
                            if result == 1:
                                wins += 1
                    id_map[user1.id] = user1
                    results[user1.id] = wins

                print(results)
                raw_top = sorted(results.items(), key=operator.itemgetter(1))[::-1]
                print(raw_top)
                last_wins = raw_top[0][1]
                top = [([id_map[raw_top[0][0]]], raw_top[0][1])]
                for obj in raw_top[1:]:
                    if obj[1] == last_wins:
                        top[-1][0].append(id_map[obj[0]])
                    else:
                        last_wins = obj[1]
                        top.append(([id_map[obj[0]]], obj[1]))

                for uid in self.bets:
                    self.money[uid] -= self.bets[uid]

                index = 0
                while self.pot > 0:
                    best = top[index][0]
                    if len(best) == 0:
                        yield from self._origin("No winner found? (error!) returning everyone their bets.")
                        for uid in self.bets:
                            self.money[uid] += self.bets[uid]
                        break
                    elif len(best) == 1:
                        if best[0].id in self.round["allin"]:
                            winamt = self.bets[best[0].id] * len(self.rotation)
                            if winamt >= self.pot:
                                self.money[best[0].id] += self.pot
                                self.pot = 0
                                yield from self._origin(best[0].mention + " wins the pot of `$" + str(self.pot) + "`")
                            else:
                                self.pot -= winamt
                                self.money[best[0].id] += winamt
                                yield from self._origin(best[0].mention + " wins a pot of `$" + str(winamt) + "`, there is not `$" + str(self.pot) + "` left in the pot")
                        else:
                            self.money[best[0].id] += self.pot
                            self.pot = 0
                            yield from self._origin(best[0].mention + " wins the pot of `$" + str(self.pot) + "`")
                    else:
                        winamt = math.floor(self.pot / len(best))
                        for user in best:
                            self.money[user.id] += winamt
                        self.pot = 0
                        yield from self._origin(market.word_list_format([u.mention for u in best]) + " draw, the split the pot and win `$" + str(winamt) + "` each")
                    index += 1

                yield from self._origin(" Everyone's hands: (S: Spades, C: Clubs, H: Hearts, D: Diamonds) \n```" + "\n".join([u.display_name + " had " + " ".join(self.hands[u.id]).replace("T", "10") + " (" + score_map[best_scores[u.id]] + ")" for u in self.rotation]) + "\n```")
            yield from self._start_round()
            return

        self.round["checked"] = 0
        self.pot = 0
        for uid in self.bets:
            self.pot += self.bets[uid]
        yield from self._origin("The pot is now `$" + str(self.pot) + "`\n\n" + get_hand_str(self.round["table"]))
        for user in self.rotation:
            self._pm(user, get_hand_str(self.hands[user.id]))
        self.cur_user = 0
        yield from self._origin(self.rotation[0].mention + " it's your turn!")

    def _next_user(self, last_user):
        index = (self.rotation.index(last_user) + 1) % len(self.rotation)
        while self.rotation[index].id in self.round["allin"]:
            index = (index + 1) % len(self.rotation)
        self.cur_user = index
        yield from self._origin(self.rotation[self.cur_user].mention + " it's your turn!")

    def _money(self, user):
        if self.started:
            return self.money[user.id]
        return 0

    def _pot(self):
        if self.started:
            return self.pot
        return 0

    def _bet(self):
        if self.started:
            return self.round["bet"]
        return 0

    def _turn(self):
        if self.started:
            return self.rotation[self.cur_user].display_name
        return "nobody"

    def check(self, user):
        if self.is_turn(user):
            if self._money(user) > self.round["bet"]:
                self.bets[user.id] = self.round["bet"]
                self.round["checked"] += 1
                yield from self._origin(user.mention + " checked the bet of `$" + str(self.round["bet"]) + "`")
                if self.round["checked"] >= len(self.rotation):
                    yield from self._next_card()
                else:
                    yield from self._next_user(user)
                return True
            else: # all in
                self.bets[user.id] = self._money(user)
                self.round["checked"] += 1
                self.round["allin"].append(user.id)
                yield from self._origin(user.mention + " has gone all in with `$" + str(self.round["bet"]) + "`!")
                if self.round["checked"] == len(self.rotation) or len(self.round["allin"]) == len(self.rotation):
                    yield from self._next_card()
                else:
                    yield from self._next_user(user)
        return False

    def fold(self, user, msg=None):
        if self.is_turn(user):
            self.rotation.remove(user)
            if msg is None:
                msg = user.mention + " folded"
            yield from self._origin(msg)
            if len(self.rotation) == 1:
                yield from self._next_card(True)
            elif self.round["checked"] >= len(self.rotation):
                yield from self._next_card()
            else:
                yield from self._next_user(user)
            return True
        return False

    def bet(self, user, bet):
        if self.is_turn(user) and bet > self.round["bet"]:
            if self._money(user) >= bet:
                self.round["bet"] = bet
                self.round["checked"] += 1
                self.bets[user.id] = bet
                if self._money(user) == bet:
                    self.round["allin"].append(user.id)
                    yield from self._origin(user.mention + " has gone all in, raising the bet to `$" + str(self.round["bet"]) + "`")
                else:
                    yield from self._origin(user.mention + " raised to bet to `$" + str(self.round["bet"]) + "`")
                yield from self._next_user(user)
                return True
        return False

    def is_turn(self, user):
        return self.rotation[self.cur_user] == user

    def is_invited(self, user):
        return user in self.invited

    def accept(self, user):
        if user in self.invited and user not in self.accepted and user not in self.declined:
            self.accepted.append(user)
            yield from self._origin(user.mention + " has accepted the game invite")
            yield from self._check()
            return True
        return False

    def decline(self, user):
        if user in self.invited and user not in self.accepted and user not in self.declined:
            self.declined.append(user)
            yield from self._origin(user.mention + " has declined the game invite")
            yield from self._check()
            return True
        return False

    def leave(self, user):
        if not self.started and user in self.invited:
            yield from self.decline(user)
            return True
        elif user in self.accepted:
            self.accepted.remove(user)
            if self.is_turn(user):
                yield from self.fold(user, msg=user.mention + " left the game!")
            elif user in self.rotation:
                self.rotation.remove(user)
                yield from self._origin(user.mention + " has left the game!")

            if user.id in self.bot.market.games["poker"]:
                del self.bot.market.games["poker"][user.id]

            if len(self.accepted) == 1:
                yield from self._origin(self.accepted[0].mention + ", everyone else has left so the game is now ending.")
                self.started = False
                del self.bot.market.games["poker"][self.accepted[0].id]
            return True
        return False

class StrawPoll(object):
    def __init__(self, data = None, url = None):

        self.url = None
        self.title = None
        self.results = {}
        self.totalVotes = None

        if url != None:
            self.url = url
            self.updateResults()

        elif data != None:
            r = requests.post('http://strawpoll.me/ajax/new-poll', json = data)
            print(r.content)
            print(r.json())
            if r.status_code == requests.codes.ok:
                self.url = "http://strawpoll.me/%s" % r.json()["id"]
                self.updateResults()
            else:
                self.url = None



    @classmethod
    def fromID(cls, id):
        return cls(url = "http://strawpoll.me/%s" % str(id))

    @classmethod
    def fromURL(cls, url):
        return cls(url = url.strip('/'))

    @classmethod
    def new(cls, title, options, multi = False, permissive = False):
        return cls(data = {"title":title, "options[]":options, "multi":True, "permissive":True})


    def updateResults(self):
        if self.url != None:
            r = requests.get("%s/r" % self.url)
            if r.status_code != requests.codes.ok: return

            content = r.content
            # Options
            matches = re.findall('<div class="pollOptionName">(.+?)</div>.+?<span>(.*?) vote[s]*</span>', content, flags = re.DOTALL)
            if matches != None:
                self.results = {k:int(v) for k,v in matches}
            else:
                self.results = {}


            # Title
            self.title = re.search('<div id="pollHeader">.+?<div>(.+?)</div>', content, flags = re.DOTALL)
            if self.title != None: self.title = self.title.group(1).strip()

            # Total count
            self.totalVotes = re.search('<div id="pollTotalVotes">.+?<span>(.+?)</span>', content, flags = re.DOTALL)

            if self.totalVotes != None: self.totalVotes = int(self.totalVotes.group(1))



xkcd_range = [100, 1600]


def get_xkcd_link(n=-1):
    if n == -1:
        n = random.randint(xkcd_range[0], xkcd_range[1])
    link = "http://xkcd.com/" + str(n) + "/"
    f = requests.get(link)
    lines = f.text.split('\n')
    imgurl = None
    for line in lines:
        if line.startswith("Image URL"):
            line = line.replace(" ", "")
            index = line.find("http")
            imgurl = line[index:]
            break
    return imgurl


def get_humblebundle(suffix=""):
    link = "https://www.humblebundle.com/" + suffix
    f = requests.get(link)

    lines = f.text.split('\n')
    base_games = ""
    average_games = ""
    average_price = "???"
    bonus_games = ""
    bonus_price = "???"

    game_index = 0
    last_line = None
    for line in lines:
        if "prepend section-heading price bta" in line and game_index == 0:
            game_index = 1
            index = line.find("$")
            average_price = line[index:]
            index = average_price.find(" ")
            average_price = average_price[:index]
        if "prepend section-heading price fixed" in line and game_index == 1:
            game_index = 2
            index = line.find("$")
            bonus_price = line[index:]
            index = bonus_price.find(" ")
            bonus_price = bonus_price[:index]
        if "section game-border prepend coupons" in line:
            break
        if "<h2>" in line and "game-description" in last_line:
            index = line.find("<h2>")
            gamename = line[index + 4:]
            gamename = gamename[:-5]
            if game_index == 0:
                base_games = base_games + "    - " + gamename + "\n"
            elif game_index == 1:
                average_games = average_games + "     - " + gamename + "\n"
            else:
                bonus_games = bonus_games + "     - " + gamename + "\n"
        last_line = line
    return "BASE GAMES ($1):```\n" + base_games + "```\n" + "AVERAGE GAMES (" + average_price + "):\n```" + average_games + "```\n" + "BONUS GAMES (" + bonus_price + "):\n```" + bonus_games + "```"


cah_range = [100, 4300]


def get_cah_link(n=-1):
    if n == -1:
        n = random.randint(cah_range[0], cah_range[1])
    link = "http://explosm.net/comics/" + str(n) + "/"
    f = requests.get(link)
    lines = f.text.split('\n')
    imgurl = None
    for line in lines:
        if line.startswith("<meta property") and "og:image" in line:
            line = line.replace(" ", "")
            index = line.find("http")
            imgurl = line[index:]
            imgurl = imgurl[:-2]
            break
    return imgurl

class SpeedTypeGame:

    def __init__(self, bot, members, channel, gametime=30):
        self.bot = bot
        self.members = members
        self.channel = channel
        self.accepts = []
        self.in_progress = False
        self.gametime = gametime
        self.words = []
        self.indexs = {}
        self.score = {}

    def send_all(self, message):
        for member in self.accepts:
            yield from self.bot.client.send_message(member, message)

    def _generate_word(self):
        word = self.bot.word_list[random.randint(0, len(self.bot.word_list)-1)]
        while word == "":
            word = self.bot.word_list[random.randint(0, len(self.bot.word_list)-1)]
        return word

    def next_word(self, userid):
        while self.indexs[userid] >= len(self.words):
            self.words.append(self._generate_word())
        self.indexs[userid] += 1
        return self.words[self.indexs[userid] - 1]

    def start(self):
        for member in self.accepts:
            self.indexs[member.id] = 1
            self.score[member.id] = []
        yield from self.send_all("Get ready...")
        yield from asyncio.sleep(1)
        yield from self.send_all("3..")
        yield from asyncio.sleep(1)
        yield from self.send_all("2..")
        yield from asyncio.sleep(1)
        yield from self.send_all("1..")
        yield from asyncio.sleep(1)
        self.in_progress = True
        self.words.append(self._generate_word())
        yield from self.send_all(self.words[0])
        yield from asyncio.sleep(self.gametime)
        self.in_progress = False
        yield from self.send_all("FINISHED, look at the channel this game was created in to see scores!")
        lines = "Game completed! Score(s): \n```\n"
        highest_score = 0
        highest_member = None
        for member in self.accepts:
            charcount = 0
            for word in self.score[member.id]:
                charcount += len(word)
            permin = int((60 / self.gametime) * charcount)
            lines += member.name + " got " + str(len(self.score[member.id])) + " out of " + str(self.indexs[member.id]-1) + " words correct (" + str(charcount) + " characters), that's roughly " + str(permin) + " chars per minute\n"
            if highest_member is None or charcount > highest_score:
                highest_member = member
                highest_score = charcount
            del self.bot.market.games["speedtype"][member.id]
        lines += "\n```\n"
        if len(self.accepts) > 1:
            lines += highest_member + " was the winner, with " + str(highest_score) + " characters correct!"

        yield from self.bot.client.send_message(self.channel, lines)

    def input(self, msg):
        if msg.author.id in self.indexs:
            if msg.content.replace(" ", "") == self.words[self.indexs[msg.author.id]-1]:
                self.score[msg.author.id].append(msg.content)
            yield from self.bot.client.send_message(msg.author, self.next_word(msg.author.id))

    def check_status(self):
        if len(self.members) == len(self.accepts):
            print(len(self.members))
            if len(self.accepts) > 0:
                return 2
            return 1
        return 0

    def accept(self, userid):
        member = None
        for mem in self.members:
            if mem.id == userid:
                member = mem
                break
        if member is not None and member not in self.accepts:
            self.accepts.append(member)
            return True
        return False

    def decline(self, userid):
        member = None
        for mem in self.members:
            if mem.id == userid:
                member = mem
                break
        if member is not None:
            self.members.remove(member)
            del self.bot.market.games["speedtype"][userid]
            return True
        return False

def update_story(bot, msg):
    game = bot.market.games["stories"][msg.author.id]
    card = game["story"][game["current"]]
    yield from bot.client.send_message(msg.channel, "\n```" + "\n".join(styload.get_text(game["story"], game["current"])) + "```\n" + "\n\n".join(["`" + option + "`: \n`>  " + "\n>  ".join(styload.get_text(game["story"], game["current"], option)) + "`" for option in card["options_order"] if card["options"][option]["enabled"]]))


nums = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
tens = ["", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
powers = ["thousand", "million", "billion", "trillion", "quadrillion", "quintillion", "sextillion", "septillion", "octillion", "nonillion", "decillion", "undecillion", "duodecillion",
          "tredecillion", "quatttuor-decillion", "quindecillion", "sexdecillion", "septen-decillion", "octodecillion", "novemdecillion", "vigintillion", "centillion"]


def get_word(n):
    if n == 0:
        return "zero"

    is_negative = False
    if n < 0:
        is_negative = True
        n = abs(n)

    strn = str(n)

    word = ""
    power = 0
    had_hundred = False
    while power < len(strn):
        digit = int(strn[-(power+1)])
        if power == 0: # number
            word += nums[digit]
            power += 1
        elif power == 1: #
            if digit == 1:
                word = teens[int(strn[-1])]
            else:
                if word != "":
                    if tens[digit] != "":
                        word = tens[digit] + "-" + word
                else:
                    word = tens[digit]
            power += 1
        elif power == 2:
            if digit > 0:
                if word != "":
                    word = nums[digit] + "-hundred-and-" + word
                else:
                    word = nums[digit] + "-hundred"
                had_hundred = True
            power += 1
        else:
            next_power = min(len(strn), power + 3)
            prefix = get_word(int(strn[-next_power:-power]))

            if prefix != "" and prefix != "zero":
                power_index = math.floor(power/3) - 1
                if word != "":
                    if had_hundred or power_index > 0:
                        word = prefix + "-" + powers[power_index] + "-" + word
                    else:
                        word = prefix + "-" + powers[power_index] + "-and-" + word
                else:
                    word = prefix + "-" + powers[power_index]
            power += 3

    if is_negative:
        return "minus-" + word
    else:
        return word

def find_largest_prime(n):
    factors = []
    if n % 2 == 0:
        factors.append(2)
        while n % 2 == 0:
            n /= 2
        if n == 1:
            return 2

    i = 3
    while i * i < n:
        if n % i == 0:
            factors.append(i)
            while n % i == 0:
                n /= i
        i += 2
    if n != 1:
        factors.append(int(n))
    return factors

def get_seqs(strn, is_number=False):
    strn = strn.lower()
    if is_number:
        digits = "0123456789"
    else:
        digits = "abcdefghijklmnopqrstuvwxyz"

    rising_sequence = strn[0]
    best_rising_sequence = ""
    falling_sequence = strn[0]
    best_falling_sequence = ""
    repeat_sequence = strn[0]
    best_repeat_sequence = ""
    digit_sum = 0
    if is_number:
        digit_sum = int(strn[0])
    for i in range(1, len(strn)):
        if is_number:
            digit_sum += int(strn[i])
        if strn[i] == repeat_sequence[-1]:
            repeat_sequence += strn[i]
        else:
            if len(repeat_sequence) > len(best_repeat_sequence):
                best_repeat_sequence = repeat_sequence
            repeat_sequence = strn[i]

        if digits.find(strn[i]) == digits.find(rising_sequence[-1]) + 1:
            rising_sequence += strn[i]
        else:
            if len(rising_sequence) > len(best_rising_sequence):
                best_rising_sequence = rising_sequence
            rising_sequence = strn[i]

        if digits.find(strn[i]) == digits.find(falling_sequence[-1]) - 1:
            falling_sequence += strn[i]
        else:
            if len(falling_sequence) > len(best_falling_sequence):
                best_falling_sequence = falling_sequence
            falling_sequence = strn[i]

    best_pal = ""
    for digit in digits:
        index = strn.find(digit)
        while index > -1:
            nindex = strn.find(digit, index + 1)
            if nindex != -1:
                substr = strn[index:nindex + 1]
                if len(substr) > len(best_pal):
                    if substr == substr[::-1]:
                        best_pal = "Best palindrome: " + substr
            index = nindex
    if best_pal == "":
        best_pal = "Doesn't contain a palindrome"

    return [best_rising_sequence, best_falling_sequence, best_repeat_sequence, best_pal, digit_sum]



def fun_handle(bot, msg, cmd):
    formatting = bot.prefix + "help to see help!"
    try:
        cd_result = bot.get_cooldown(msg.author.id, cmd)
        if cd_result > 0:
            yield from bot.client.send_message(msg.channel, "That command is on cooldown, please wait another " + str(int(cd_result)) + " seconds before using it")
        else:
            if cmd[0] == "roll":
                amount = 1
                if len(cmd) > 1:
                    amount = int(cmd[1])
                results = []
                total = 0
                for i in range(amount):
                    results.append(str(random.randint(1, 6)))
                    total += int(results[i])
                if amount == 1:
                    yield from bot.client.send_message(msg.channel, "You roll a " + str(total))
                else:
                    yield from bot.client.send_message(msg.channel, "You roll " + ", ".join(results) + " total: " + str(total))
            elif cmd[0] == "reverse":
                yield from bot.client.send_message(msg.channel, " ".join(cmd[1:])[::-1])
            elif cmd[0] == "8ball":
                yield from bot.client.send_message(msg.channel, ball_8[random.randint(0, len(ball_8)-1)])
            elif cmd[0] == "wordify":
                try:
                    yield from bot.client.send_message(msg.channel, "```" + cmd[1] + " is written as: \n" + get_word(int(cmd[1])))
                except ValueError:
                    yield from bot.client.send_message(msg.channel, "Must give an integer!")
            elif cmd[0] == "flip":
                if random.randint(0, 1) == 0:
                    yield from bot.client.send_message(msg.channel, "It lands on head.")
                else:
                    yield from bot.client.send_message(msg.channel, "It lands on tail.")
            elif cmd[0] == "xkcd":
                n = -1
                if len(cmd) > 1:
                    n = int(cmd[1])
                yield from bot.client.send_message(msg.channel, get_xkcd_link(n))
            elif cmd[0] == "candh":
                n = -1
                if len(cmd) > 1:
                    n = int(cmd[1])
                yield from bot.client.send_message(msg.channel, get_cah_link(n))
            elif cmd[0] == "hb":
                suffix = ""
                if len(cmd) > 1:
                    suffix = " ".join(cmd[1:])
                yield from bot.client.send_message(msg.channel, get_humblebundle(suffix))
            elif cmd[0] == "poker":
                formatting = bot.prefix + "help poker"
                if cmd[1] == "new":
                    formatting = bot.prefix + "poker new (ante) (start_money) {mentions}"
                    start_money, ante = 100, 1
                    if len(cmd) > 2 and market.is_number(cmd[2]):
                        ante = float(cmd[2])
                        if not PokerGame.valid_float(ante):
                            yield from bot.client.send_message(msg.channel, "Invalid ante, must be to 2 decimal places (e.g 3.62)")
                            return
                    if len(cmd) > 3 and market.is_number(cmd[3]):
                        start_money = float(cmd[3])
                        if not PokerGame.valid_float(start_money):
                            yield from bot.client.send_message(msg.channel, "Invalid starting money, must be to 2 decimal places (e.g 3.62)")
                    invited = msg.mentions + [msg.author]
                    failed = []
                    success = []
                    for u in invited:
                        if not u.id == msg.author.id:
                            if u.id not in bot.market.games["poker"]:
                                if not u in success:
                                    success.append(u)
                            else:
                                if not u in failed:
                                    failed.append(u)

                    if len(failed) > 0:
                        yield from bot.client.send_message(msg.channel, "Failed to create game as " + market.word_list_format([x.mention for x in failed]) + " are already in poker games!")
                    elif len(success) > 1:
                        game = PokerGame(bot, success, msg.channel, start_money=start_money, ante=ante)
                        for user in success:
                            bot.market.games["poker"][user.id] = game
                        yield from bot.client.send_message(msg.channel, "Game created, starting money is `$" + str(start_money) + "`, ante is `$" + str(ante) + "`, now everyone needs to either accept or decline using " + bot.prefix + "poker accept or " + bot.prefix + "poker decline")
                    else:
                        yield from bot.client.send_message(msg.channel, "Must invite at least on player (can't play by yourself!)")
                elif cmd[1] == "accept":
                    formatting = bot.prefix + "poker accept"
                    if msg.author.id in bot.market.games["poker"]:
                        result = yield from bot.market.games["poker"][msg.author.id].accept(msg.author)
                        if not result:
                            yield from bot.client.send_message(msg.channel, "You've already responded")
                    else:
                        yield from bot.client.send_message(msg.channel, "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "decline":
                    formatting = bot.prefix + "poker decline"
                    if msg.author.id in bot.market.games["poker"]:
                        result = yield from bot.market.games["poker"][msg.author.id].decline(msg.author)
                        if not result:
                            yield from bot.client.send_message(msg.channel, "You've already responded")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "leave":
                    formatting = bot.prefix + "poker leave"
                    if msg.author.id in bot.market.games["poker"]:
                        result = yield from bot.market.games["poker"][msg.author.id].leave(msg.author)
                        if not result:
                            yield from bot.client.send_message(msg.channel, "You're not in the game")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "raise":
                    formatting = bot.prefix + "poker raise [bet]"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel, "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            game = bot.market.games["poker"][msg.author.id]
                            if game.is_turn(msg.author):
                                bet = float(cmd[2])
                                if PokerGame.valid_float(bet):
                                    if game._money(msg.author) >= bet:
                                        result = yield from game.bet(msg.author, bet)
                                        if not result:
                                            yield from bot.client.send_message(msg.channel, "Your bet must be higher than the current one (`$" + str(game._bet()) + "`)")
                                    else:
                                        yield from bot.client.send_message(msg.channel, "You don't have enough money to bet that!")
                                else:
                                    yield from bot.client.send_message(msg.channel, "Invalid bet, must be to 2 decimal places (e.g 3.62)")
                            else:
                                yield from bot.client.send_message(msg.channel, "It's not your turn!")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "check":
                    formatting = bot.prefix + "poker check"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel,
                                                               "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            game = bot.market.games["poker"][msg.author.id]
                            if game.is_turn(msg.author):
                                result = yield from game.check(msg.author)
                                #if not result:
                                #    yield from bot.client.send_message(msg.channel, "You've gone")
                            else:
                                yield from bot.client.send_message(msg.channel, "It's not your turn!")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "fold":
                    formatting = bot.prefix + "poker fold"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel,
                                                               "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            result = yield from bot.market.games["poker"][msg.author.id].fold(msg.author)
                            if not result:
                                yield from bot.client.send_message(msg.channel, "It's not your turn!")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "money":
                    formatting = bot.prefix + "poker money"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel,
                                                               "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            yield from bot.client.send_message(msg.channel, "You have `$" + str(bot.market.games["poker"]._money(msg.author)) + "`")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "pot":
                    formatting = bot.prefix + "poker pot"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel,
                                                               "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            yield from bot.client.send_message(msg.channel, "The pot is currently `$" + bot.market.games["poker"]._pot() + "`")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "bet":
                    formatting = bot.prefix + "poker bet"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel,
                                                               "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            yield from bot.client.send_message(msg.channel,
                                                               "The current bet is `$" + bot.market.games[
                                                                   "poker"][msg.author.id]._bet() + "`")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "turn":
                    formatting = bot.prefix = "poker turn"
                    if msg.author.id in bot.market.games["poker"]:
                        if not bot.market.games["poker"][msg.author.id].started:
                            yield from bot.client.send_message(msg.channel,
                                                               "The game hasn't started yet, still waiting for people to respond!")
                        else:
                            yield from bot.client.send_message(msg.channel, "It's `" + bot.market.games["poker"]._turn() + "`'s turn!")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You aren't in a game! Use " + bot.prefix + "poker new to create one")
                elif cmd[1] == "rules":
                    yield from bot.client.send_message(msg.channel,
                        """```
Rules for Texas Hold 'Em:

    - Betting
        a round of betting is played in a circle, everyone betting takes turns to either:
          'raise' - increase the bet to a given amount
          'check' - match the current bet, signifying you want to finish this betting round
          'fold'  - don't bet anything and fold, you then sit out for the rest of the round (whole round, not betting round)
        the round is played until either everyone hasn't folded has checked or all but one player has folded.

    - Part 1
        initially everyone pays the ante (initial bet, marketbot usually uses $1) gets dealt two cards,
        you then do betting round

    - Part 2
        after the first round of betting, 3 cards are then shown face up on the 'table',
        these cards work so everyone shares them (they are a part of everyone's hands simultaneously)
        after the 3 cards have been shown, you do another round of betting

    - Part 3
        You then show one more card so that there are 4 cards on the table and do another round of betting

    - Part 4
        You show one last card so that there are 5 cards on the table, then do another round of betting.
        At the end of this round the winner is decided based on who has the best hand (using their hand and the table)
        the winner (or winners in some cases) are then given their prize money and the next round is started.

                        ```""")
                    yield from bot.client.send_message(msg.channel, """```
Hand order (from worst hand to best hand):

    - High card : the highest card by value (2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A)
    - pair : two cards of the same number, e.g queen of spades and queen of hearts
    - two pairs : two of the above
    - three of a kind : three cards of the same number, e.g 3 of spades, 3 of hearts, 3 of clubs
    - straight : 5 cards in a row, e.g. 8, 9, 10, J, Q
    - flush : 5 cards of the same suit
    - full house : 3 of a kind and a pair
    - four of a kind : four cards of the same number
    - straight flush : 5 cards in a row all of the same suit
    - royal flush : 10, J, Q, K, A all of the same suit

    In the event of a draw it either goes down to highest card or highest set (e.g highest pair, highest 4-of-a-kind)
    if there is still somehow a draw (generally unlikely) the pot is split amongst the winners```""")
            elif cmd[0] == "hangman":
                formatting = bot.prefix + "hangman new|guess|[guess]"
                if cmd[1] == "new":
                    if msg.channel.id not in bot.market.games["hangman"]:
                        word = bot.word_list[random.randint(0, len(bot.word_list)-1)]
                        bot.market.games["hangman"][msg.channel.id] = {
                            "word": word,
                            "done": "-" * len(word),
                            "guessed": [],
                            "left": 7,
                            "author": msg.author.id
                        }
                        yield from bot.client.send_message(msg.channel, "Created a new hangman game with a **" + str(len(word)) + "** lettered word, use " + bot.prefix + "hangman [guess] to guess")
                    else:
                        yield from bot.client.send_message(msg.channel, "This channel already has an in-progress hangman game!")
                elif cmd[1] == "end":
                    if msg.channel.id in bot.market.games["hangman"]:
                        if bot.is_me(msg) or msg.author.id == bot.market.games["hangman"][msg.channel.id]["author"] or msg.channel.permissions_for(msg.author).manage_messages:
                            game = bot.market.games["hangman"][msg.channel.id]
                            yield from bot.client.send_message(msg.channel, "Game ended, the word was '" + game["word"] + "', you got '" + game["done"] + "' in " + str(len(game["guessed"])) + " guesses")
                            del bot.market.games["hangman"][msg.channel.id]
                        else:
                            yield from bot.client.send_message(msg.channel, "You don't have permission to use that command!")
                    else:
                        yield from bot.client.send_message(msg.channel, "There isn't a game in progress!")
                else:
                    if msg.channel.id in bot.market.games["hangman"]:
                        game = bot.market.games["hangman"][msg.channel.id]
                        if len(cmd[1]) == 1: # guess letter
                            if cmd[1] not in game["guessed"]:
                                game["guessed"] += cmd[1]
                                if cmd[1] in game["word"]:
                                    for i in range(len(game["word"])):
                                        if game["word"][i] == cmd[1]:
                                            game["done"] = game["done"][:i] + cmd[1] + game["done"][i+1:]
                                    if not "-" in game["done"]:
                                        yield from bot.client.send_message(msg.channel, "You win! The word was " + game["word"] + " you got it in " + str(len(game["guessed"])) + " guesses!")
                                        del bot.market.games["hangman"][msg.channel.id]
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Correct guess! Current progress: " + game["done"] + ", Guessed letters: " + ", ".join(game["guessed"]) + ", You can make " + str(game["left"]) + " more mistakes")
                                else:
                                    game["left"] -= 1
                                    if game["left"] <= 0:
                                        yield from bot.client.send_message(msg.channel, "You lose! The word was " + game["word"] + " you got " + game["done"] + " in " + str(len(game["guessed"])) + " guesses!")
                                        del bot.market.games["hangman"][msg.channel.id]
                                    else:
                                        yield from bot.client.send_message(msg.channel, "Wrong guess! Current progress: " + game["done"] + ", Guessed letters: " + ", ".join(game["guessed"]) + ", You can make " + str(game["left"]) + " more mistakes")
                            else:
                                yield from bot.client.send_message(msg.channel, cmd[1] + " has already been guessed! Current progress: " + game["done"] + ", Guessed letters: " + ", ".join(game["guessed"]))
                        else:
                            if cmd[1] == game["word"]:
                                yield from bot.client.send_message(msg.channel, "You win! The word was " + game["word"] + " you got it in " + str(len(game["guessed"])) + " guesses!")
                                del bot.market.games["hangman"][msg.channel.id]
                            else:
                                game["left"] -= 1
                                if game["left"] <= 0:
                                    yield from bot.client.send_message(msg.channel, "You lose! The word was " + game["word"] + " you got " + game["done"] + " in " + str(len(game["guessed"])) + " guesses!")
                                    del bot.market.games["hangman"][msg.channel.id]
                                else:
                                    yield from bot.client.send_message(msg.channel, "Wrong guess! Current progress: " + game["done"] + ", Guessed letters: " + ", ".join(game["guessed"]) + ", You can make " + str(game["left"]) + " more mistakes")
                    else:
                        yield from bot.client.send_message(msg.channel, "There isn't currently a game in progress, do " + bot.prefix + "hangman new to create one")
            elif cmd[0] == "strawpoll":
                if cmd[1] == "new":
                    title = " ".join(cmd[2:])
                    options_raw = None
                    title = title[title.index('"')+1:]
                    options_raw = title[title.index('"')+1:]
                    title = title[:title.index('"')]
                    while options_raw[0] == " ":
                        options_raw = options_raw[1:]
                    options = options_raw.split(",")
                    for i in range(len(options)):
                        while options[i][0] == " ":
                            options[i] = options[i][1:]
                        while options[i][-1] == " ":
                            options[i] = options[i][:-1]
                    s = StrawPoll.new(title, options_raw)
                    yield from bot.client.send_message(msg.channel, s.url)
            elif cmd[0] == "speedtype":
                formatting = bot.prefix + "speedtype new|accept|decline [gametime] [mentions]"
                if cmd[1] == "new":
                    if len(msg.mentions) > 0:
                        ok = True
                        for member in msg.mentions:
                            if member.id in bot.market.games["speedtype"] and bot.market.games["speedtype"][member.id] is not None:
                                ok = False
                                break
                        if ok:
                            gametime = 30
                            if market.is_number(cmd[2]):
                                gametime = int(cmd[2])
                            if gametime > 60:
                                yield from bot.client.send_message(msg.channel, "Games can be a maximum of 60 seconds long")
                            else:
                                game = SpeedTypeGame(bot, msg.mentions, msg.channel)
                                for member in msg.mentions:
                                    if member.id != bot.client.user.id:
                                        bot.market.games["speedtype"][member.id] = game
                                yield from bot.client.send_message(msg.channel, "Game created, now everyone needs to either " + bot.prefix + "speedtype accept or " + bot.prefix + "speedtype decline")
                        else:
                            yield from bot.client.send_message(msg.channel, "One or more members invited are already invited to games, please do " + bot.prefix + "speedtype decline to decline the game")
                    else:
                        yield from bot.client.send_message(msg.channel, "You must mention at least one user!")
                elif cmd[1] == "rules":
                    yield from bot.client.send_message(msg.channel, "Rules: After everyone has responded to the game invite, " + bot.name + " will start sending you words in DM. Write these words back to him (in dm) as quickly as possible to get better scores, your scores are then told to you at the end")
                elif cmd[1] == "accept":
                    if msg.author.id in bot.market.games["speedtype"] and bot.market.games["speedtype"][msg.author.id] is not None:
                        game = bot.market.games["speedtype"][msg.author.id]
                        if game.in_progress:
                            yield from bot.client.send_message(msg.channel, "The game is in progress! Go to DM to play (quick!)")
                        else:
                            if game.accept(msg.author.id):
                                yield from bot.client.send_message(msg.channel, "Accepted game invite!")
                                status = game.check_status()
                                if status == 2:
                                    yield from bot.client.send_message(msg.channel, "All players have responded, starting game")
                                    yield from game.start()
                                elif status == 1:
                                    yield from bot.client.send_message(msg.channel, "All players declined, deleting game.")
                            else:
                                yield from bot.client.send_message(msg.channel, "You have already responded!")
                    else:
                        yield from bot.client.send_message(msg.channel, "You are not currently invited to a game!")
                elif cmd[1] == "decline":
                    if msg.author.id in bot.market.games["speedtype"] and bot.market.games["speedtype"][msg.author.id] is not None:
                        game = bot.market.games["speedtype"][msg.author.id]
                        if game.in_progress:
                            yield from bot.client.send_message(msg.channel, "The game is in progress! Go to DM to play (quick!)")
                        else:
                            if game.decline(msg.author.id):
                                yield from bot.client.send_message(msg.channel, "Declined game invite!")
                                status = game.check_status()
                                if status == 2:
                                    yield from bot.client.send_message(msg.channel, "All players have responded, starting game")
                                    yield from game.start()
                                elif status == 1:
                                    yield from bot.client.send_message(msg.channel, "All players declined, deleting game.")
                            else:
                                yield from bot.client.send_message(msg.channel, "You have already responded!")
                    else:
                        yield from bot.client.send_message(msg.channel, "You are not currently invited to a game!")
            elif cmd[0] == "riddle":
                formatting = bot.prefix + "riddle new|giveup|[guess]"
                if len(cmd) == 1 or (cmd[1] != "new" and cmd[1] != "giveup"):
                    if msg.channel.id in bot.market.riddles:
                        formatting = bot.prefix + "riddle guess [guess]"
                        guess = " ".join(cmd[1:]).replace('"', "").replace(" the ", "").replace(" a ", "")
                        if guess.startswith("the "):
                            guess = guess[4:]
                        if guess.startswith("a "):
                            guess = guess[2:]
                        if len(guess) <= 2:
                            guess = "letter " + guess
                        answer = bot.market.riddles[msg.channel.id][1]
                        sqs = SequenceMatcher(None, guess, answer)
                        n = 0
                        matching = sqs.get_matching_blocks()
                        for t in matching:
                            n += t.size
                        ratio = n / min(len(answer), len(guess))
                        print(guess + " : " + answer + " : " + str(ratio))
                        if ratio > 0.9:
                            del bot.market.riddles[msg.channel.id]
                            yield from bot.client.send_message(msg.channel, "Correct! The answer was: " + answer)
                        elif ratio > 0.8:
                            del bot.market.riddles[msg.channel.id]
                            yield from bot.client.send_message(msg.channel, "Almost, the answer was: " + answer)
                        else:
                            yield from bot.client.send_message(msg.channel, "Nope, sorry!")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You don't have a riddle! Use " + bot.prefix + "riddle new to create a new one")
                else:
                    if cmd[1] == "new":
                        if not msg.channel.id in bot.market.riddles:
                            riddle = bot.riddles[random.randint(0, len(bot.riddles) - 1)]
                            bot.market.riddles[msg.channel.id] = riddle
                            yield from bot.client.send_message(msg.channel, riddle[0])
                        else:
                            yield from bot.client.send_message(msg.channel, "You already have a riddle: " +
                                                               bot.market.riddles[msg.channel.id][0])
                    elif cmd[1] == "giveup":
                        if msg.channel.id in bot.market.riddles:
                            formatting = bot.prefix + "riddle giveup"
                            del bot.market.riddles[msg.channel.id]
                            yield from bot.client.send_message(msg.channel, "Oh well! Better luck next time :)")
                        else:
                            yield from bot.client.send_message(msg.channel,
                                                               "You don't have a riddle! Use " + bot.prefix + "riddle new to create a new one")
                    else:
                        raise IndexError
            elif cmd[0] == "cat":
                with aiohttp.Timeout(10):
                    response = yield from bot.client.session.get("http://random.cat/meow")
                    data = yield from response.json()
                    yield from bot.client.send_message(msg.channel, data["file"])
            elif cmd[0] == "poem":
                yield from bot.client.send_message(msg.channel, "```\n" + "\n".join(bot.poems[random.choice(list(bot.poems.keys()))]) + "\n```")
            elif cmd[0] == "string":
                formatting = bot.prefix + "string [string]"
                word = " ".join(cmd[1:])

                seqs = get_seqs(word, is_number=False)

                digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                uword = word.upper()
                raw_freqs = {digit: int((uword.count(digit) / float(len(uword))) * 10000) / 100 for digit in digits}
                top_digits = sorted(raw_freqs.items(), key=operator.itemgetter(1))[-10:][::-1]
                freqs = "; ".join(["%s: %s%s" % (digit[0], digit[1], "%") for digit in top_digits])

                sortword = "".join(sorted(word))
                yield from bot.client.send_message(msg.channel,  "```\n" + "\n".join([
                    "Information about " + word + ":",
                    "  -  Best sequence of repeating letters: " + seqs[2],
                    "  -  Best sequence of rising letters: " + seqs[0],
                    "  -  Best sequence of falling letters: " + seqs[1],
                    "  -  " + seqs[3],
                    "  -  Top 10 most frequent digits: " + freqs,
                    "  -  The word sorted alphabetically: " + sortword
                ]) + "\n```")
            elif cmd[0] == "number":
                formatting = bot.prefix + "number [number] - must be an integer"
                n = int(cmd[1])
                real_n = n
                strn = cmd[1]
                negative = False
                if n < 0:
                    negative = True
                    n = abs(n)

                prime_factors = find_largest_prime(n)

                seqs = get_seqs(strn, is_number=True)

                square_line = "Is not a square number"
                if math.sqrt(n).is_integer():
                    square_line = "Is " + str(int(math.sqrt(n))) + " squared"

                prime_line = "Is a prime number"
                if len(prime_factors) != 0:
                    prime_line = "Prime factors: " + ", ".join([str(x) for x in prime_factors])

                neg_line = "Is not negative."
                if negative:
                    strn = "-" + strn
                    neg_line = "Is negative"

                digits = "0123456789"
                freqs = ["%s: %s%s" % (digit, str(int((strn.count(digit) / len(strn)) * 10000) / 100), "%") for digit in
                         digits]

                sortstrn = "".join(sorted(strn))
                yield from bot.client.send_message(msg.channel, "```\n" + "\n".join([
                    "Information about " + strn + ":",
                    "  -  Written as " + get_word(real_n),
                    "  -  " + neg_line,
                    "  -  " + prime_line,
                    "  -  Best sequence of repeating digits: " + seqs[2],
                    "  -  Best sequence of rising digits: " + seqs[0],
                    "  -  Best sequence of falling digits: " + seqs[1],
                    "  -  " + seqs[3],
                    "  -  " + square_line,
                    "  -  The sum of its digits is: " + str(seqs[4]),
                    "  -  The frequences of the digits are: " + "; ".join(freqs),
                    "  -  The number sorted lowest to highest: " + sortstrn
                ]) + "\n```")
            elif cmd[0] == "art":
                formatting = bot.prefix + "art [width] [height] [args]"
                width, height = int(cmd[1]), int(cmd[2])
                if 0 < width < 61:
                    if 0 < height < 31:
                        rawcode = [x.replace(" ", "") for x in " ".join(cmd[3:]).replace("```", "").split("\n") if x != ""]
                        result = textart.art_script(width, height, rawcode)
                        yield from bot.client.send_message(msg.channel, result.art().text())
                        if len(result.get_log()) > 0:
                            yield from bot.client.send_message(msg.channel, "\n```\n" + "\n".join(result.get_log()) + "\n```")
                    else:
                        yield from bot.client.send_message(msg.channel, "Invalid height, must be from 1 and 20")
                else:
                    yield from bot.client.send_message(msg.channel, "Invalid width, must be from 1 and 20")
            elif cmd[0] == "hand":
                yield from bot.client.send_message(msg.channel, get_hand_str(" ".join(cmd[1:])))
            #elif cmd[0] == "ker":
            #    if bot.is_me(msg):
            #        formatting = bot.prefix + "ker [file_in] [file_out] [coef] [kernel]"
            #        file_in = "corrupt/" + cmd[1]
            #        file_out = "corrupt/ " + cmd[2]
            #        file_final = "corrupt/" + cmd[2]
            #        if not file_in.endswith(".bmp"):
            #            file_in += ".bmp"
            #        if not file_out.endswith(".bmp"):
            #            file_out += ".bmp"
            #            file_final += ".png"
            #        else:
            #            file_final = file_final[:-4] + ".png"
            #        coef = float(cmd[3])
            #        rawker = [[float(y) for y in x.split(" ") if y != ""] for x in " ".join(cmd[4:]).replace("```", "").replace(",", "").split("\n") if x.replace(" ", "") != ""]
            #        print(rawker)
            #        if len(rawker) <= 5 and len(rawker[0]) <= 5:
            #            try:
            #                yield from bot.client.send_typing(msg.channel)
            #                ker = corruptfun2.Kernal(rawker, coef=coef)
            #                corruptfun2.run(file_in, file_out, ker, doprint=False)
            #                im = Image.open(file_out)
            #                im.save(file_final, "PNG")
            #                yield from bot.client.send_file(msg.channel, file_final)
            #                os.remove(file_out)
            #                os.remove(file_final)
            #            except corruptfun2.InvalidGrid:
            #                yield from bot.client.send_message(msg.channel, "Invalid kernel, must be an odd square matrix")
            #        else:
            #            yield from bot.client.send_message(msg.channel, "Maximum kernel size is 5x5!")
            #    else:
            #        yield from bot.client.send_message(msg.channel, "This command is still in development and can only be used by admins for now, sorry!")
            elif cmd[0] == "story":
                formatting = bot.prefix + "story "
                if not "stories" in bot.market.games:
                    bot.market.games["stories"] = {}
                if cmd[1] == "new":
                    if not msg.author.id in bot.market.games["stories"]:
                        name = " ".join(cmd[2:])
                        if name in bot.market.stories:
                            bot.market.games["stories"][msg.author.id] = {"story": copy.deepcopy(bot.market.stories[name]),
                                                                          "current": "main"}
                            yield from bot.client.send_message(msg.channel, "Story created, use m$story [option] to select an option,  m$story add {mentions} to add other people to the story and m$story end to quit the story\nPlease consider doing your story in a private channel or in a PM with MarketBot so that you don't spam chat!\n")
                            yield from update_story(bot, msg)
                        else:
                            yield from bot.client.send_message(msg.channel, "No story named " + name)
                    else:
                        yield from bot.client.send_message(msg.channel, "You're already in a story! use m$end to quit the story (Other people added can continue playing)")
                elif cmd[1] == "end":
                    if msg.author.id in bot.market.games["stories"]:
                        del bot.market.games["stories"][msg.author.id]
                        yield from bot.client.send_message(msg.channel, "You left the current story.")
                    else:
                        yield from bot.client.send_message(msg.channel, "You're not in a story, use m$new [name] to create a new one")
                elif cmd[1] == "cheat":
                    if bot.is_me(msg):
                        if msg.author.id in bot.market.games["stories"]:
                            dest = " ".join(cmd[2:])
                            if dest in bot.market.games["stories"][msg.author.id]["story"]:
                                bot.market.games["stories"][msg.author.id]["current"] = dest
                                yield from update_story(bot, msg)
                            else:
                                yield from bot.client.send_message(msg.channel, "Invalid destination!")
                        else:
                            yield from bot.client.send_message(msg.channel, "You aren't in a story!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Only the admins can use that command!")
                elif cmd[1] == "reload":
                    if bot.is_me(msg):
                        name = " ".join(cmd[2:])
                        if os.path.exists("stories/" + name + ".sty"):
                            bot.market.stories[name] = styload.load("stories/" + name + ".sty")
                            yield from bot.client.send_message(msg.channel, "Reloaded story " + name)
                        else:
                            yield from bot.client.send_message(msg.channel, "Couldn't find a story named " + name + "!")
                    else:
                        yield from bot.client.send_message(msg.channel, "Only the admins can use that command!")
                elif cmd[1] == "add":
                    if msg.author.id in bot.market.games["stories"]:
                        if len(msg.mentions) > 0:
                            failed = []
                            added = []
                            for member in msg.mentions:
                                if not member.id in bot.market.games["stories"]:
                                    bot.market.games["stories"][member.id] = bot.market.games["stories"][msg.author.id]
                                    added.append(member.name)
                                else:
                                    failed.append(member.name)
                            if len(failed) == 0:
                                yield from bot.client.send_message(msg.channel, "Added " + market.word_list_format(added) + " to the story.")
                            else:
                                yield from bot.client.send_message(msg.channel, "Added " + market.word_list_format(added) + " to the story. Couldn't add : " + market.word_list_format(failed) + " as they are already in other stories")
                        else:
                            yield from bot.client.send_message(msg.channel, "You must mention at least one person!")
                    else:
                        yield from bot.client.send_message(msg.channel,
                                                           "You're not in a story, use m$new [name] to create a new one")
                elif cmd[1] == "repeat":
                    if msg.author.id in bot.market.games["stories"]:
                        yield from update_story(bot, msg)
                    else:
                        yield from bot.client.send_message(msg.channel, "You're not in a story, use m$new [name] to create a new one")
                elif msg.author.id in bot.market.games["stories"]:
                    option = " ".join(cmd[1:])
                    game = bot.market.games["stories"][msg.author.id]
                    if option in game["story"][game["current"]]["options_order"] and game["story"][game["current"]]["options"][option]["enabled"]:
                        game["current"] = styload.run_option(game["story"], game["current"], option)
                        yield from update_story(bot, msg)
                    else:
                        yield from bot.client.send_message(msg.channel, "Invalid option, must be one of: " + ", ".join([option for option in game["story"][game["current"]]["options_order"] if game["story"][game["current"]]["options"][option]["enabled"]]) + ". Use m$repeat to see the story text again")
                else:
                    yield from bot.client.send_message(msg.channel, "You're not in a story, use m$new [name] to create a new one")
            #elif cmd[0] == "profile":
            #    if len(cmd) > 1 and cmd[1] == "clean":
            #        if bot.is_me(msg):
            #            n = profiler.cleanup(bot)
            #            yield from bot.client.send_message(msg.channel, "Removed " + str(n) + " profile cards.")
            #        else:
            #            yield from bot.client.send_message(msg.channel, "Only the admin can use that command!")
            #    else:
            #        yield from bot.client.send_typing(msg.channel)
            #        fn = yield from profiler.get_card(bot, msg.author)
            #        if fn is not None:
            #            yield from bot.client.send_message(msg.channel, "Profile for <@" + msg.author.id + ">")
            #            yield from bot.client.send_file(msg.channel, fn)
            #            bot.cooldown(msg.author.id, "profile", 5)
            #        else:
            #            yield from bot.client.send_message(msg.channel, "Failed to create profile card!")
            #elif cmd[0] == "vs":
            #    yield from bot.client.send_typing(msg.channel)
            #    formatting = bot.prefix + "vs create [width] [height] [code]"
            #    width = min(500, int(cmd[1]))
            #    height = min(500, int(cmd[2]))
            #    rawcode = " ".join(cmd[3:]).replace("```", "")
            #    scriptid = str(random.randint(100000, 999999))
            #    filename = "scripts/" + scriptid + ".vec"
            #    f = open(filename, "w")
            #    f.write(rawcode)
            #    f.close()
            #    surf = vectorscript.render_file(filename, width, height, [])
            #    os.remove(filename)
            #    filename = "scripts/" + scriptid + ".png"
            #    pygame.image.save(surf, filename)
            #    yield from bot.client.send_file(msg.channel, filename)
            #    os.remove(filename)
    except (IndexError, ValueError, KeyError):
        yield from bot.client.send_message(msg.channel, formatting)
        traceback.print_exc()
    except Exception:
        yield from bot.client.send_message(msg.channel, "Something went wrong! Please use " + bot.prefix + "ticket error <message> to send an error report to me!")
        traceback.print_exc()

def fun_handle_l(cmd):
    return 1

def setup(bot, help_page, filename):
    bot.word_list = []
    print("loading words list..")
    f = open("words_new.txt", "r")
    for line in f:
        bot.word_list += line.replace("\n", "").split(";")
    f.close()
    f = open("riddles.txt", "r")
    spl = f.read().split(";;")
    bot.riddles = []
    for riddle in spl:
        bot.riddles.append(riddle.replace('"', "").split("::"))
    f = open("poems.txt", "r")
    bot.poems = json.load(f)
    if not f.closed:
        f.close()
    print(len(bot.riddles))

    #onlyfiles = [f for f in listdir("card_img/") if isfile(join("card_img/", f))]
    #for filename in onlyfiles:
    #    if filename.endswith(".png"):
    #        bot.imgs[filename[:-4]] = pygame.image.load("card_img/" + filename)

    bot.register_command("8ball", fun_handle, fun_handle_l)
    bot.register_command("roll", fun_handle, fun_handle_l)
    bot.register_command("flip", fun_handle, fun_handle_l)
    bot.register_command("speedtype", fun_handle, fun_handle_l)
    bot.register_command("xkcd", fun_handle, fun_handle_l)
    bot.register_command("candh", fun_handle, fun_handle_l)
    bot.register_command("hb", fun_handle, fun_handle_l)
    bot.register_command("hangman", fun_handle, fun_handle_l)
    #bot.register_command("strawpoll", fun_handle, fun_handle_l)
    #ot.register_command("profile", fun_handle, fun_handle_l)
    #bot.register_command("vs", fun_handle, fun_handle_l)
    bot.register_command("riddle", fun_handle, fun_handle_l)
    bot.register_command("reverse", fun_handle, fun_handle_l)
    bot.register_command("cat", fun_handle, fun_handle_l)
    bot.register_command("poem", fun_handle, fun_handle_l)
    bot.register_command("art", fun_handle, fun_handle_l)
    #bot.register_command("ker", fun_handle, fun_handle_l)
    bot.register_command("story", fun_handle, fun_handle_l)
    bot.register_command("hand", fun_handle, fun_handle_l)
    bot.register_command("wordify", fun_handle, fun_handle_l)
    bot.register_command("number", fun_handle, fun_handle_l)
    bot.register_command("string", fun_handle, fun_handle_l)
    bot.register_command("poker", fun_handle, fun_handle_l)