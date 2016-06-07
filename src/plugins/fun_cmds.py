import traceback, random, asyncio, requests, market

import requests
import re


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
            if len(self.accepts) > 0:
                return 2
            return 1
        return 0

    def accept(self, userid):
        member = None
        for mem in self.members:
            if mem.id == userid:
                member = mem
        if member is not None:
            self.accepts.append(member)
            return True
        return False

    def decline(self, userid):
        member = None
        for mem in self.members:
            if mem.id == userid:
                member = mem
        if member is not None:
            self.members.remove(member)
            del self.bot.games["speedtype"][userid]
            return True
        return False

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
                            if game.accept(msg.author.id):
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

    bot.register_command("roll", fun_handle, fun_handle_l)
    bot.register_command("speedtype", fun_handle, fun_handle_l)
    bot.register_command("xkcd", fun_handle, fun_handle_l)
    bot.register_command("candh", fun_handle, fun_handle_l)
    bot.register_command("hb", fun_handle, fun_handle_l)
    bot.register_command("hangman", fun_handle, fun_handle_l)
    bot.register_command("strawpoll", fun_handle, fun_handle_l)