import botlib
import discord
import asyncio
import time
import requests
from os import listdir
from os.path import isfile, join

def run(restarter, restart_source=None):
    client = discord.Client()

    def help_handle(bot, message, cmd):
        if cmd[-1] == "here":
            yield from bot.client.send_message(message.channel, bot.help_page.get(bot, command=cmd[1:-1]))
        else:
            yield from bot.client.send_message(message.author, bot.help_page.get(bot, command=cmd[1:]))

    def help_length_handle(cmd):
        return 1

    @client.event
    @asyncio.coroutine
    def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('Loading plugins:')
        botlib.load_plugins(bot, bot.help_page)
        if restart_source is not None:
            print('Confirming successful restart.')
            yield from client.send_message(restart_source.channel, ">>> Restart Complete <<<")
        print('Done!')
        bot.setup = True

    @client.event
    @asyncio.coroutine
    def on_server_join(server):
        if not is_test_bot:
            requests.post("https://www.carbonitex.net/discord/data/botdata.php", data={'key': carbon_key, 'servercount': len(bot.client.servers)})

    @client.event
    @asyncio.coroutine
    def on_server_remove(server):
        if not is_test_bot:
            requests.post("https://www.carbonitex.net/discord/data/botdata.php",
                          data={'key': carbon_key, 'servercount': len(bot.client.servers)})

    @client.event
    @asyncio.coroutine
    def on_message(message):
        if bot.setup:
            if message.channel.is_private and message.author.id in bot.market.games["speedtype"] and bot.market.games["speedtype"][message.author.id].in_progress:
                yield from bot.market.games["speedtype"][message.author.id].input(message)
            else:
                if message.author.id == bot.client.user.id:
                    if message.content == bot.ping_message:
                        yield from bot.client.edit_message(message, "Pong! Took " + str(int((time.time() - bot.ping_start)*1000000)/1000) + " milliseconds")
                    cleanup = -1
                    #if message.channel.is_private:
                    #    cleanup = -1
                    if message.content.startswith("~"):
                        if message.channel.id in bot.market.settings["cleanup_tags"]:
                            cleanup = bot.market.settings["cleanup_tags"][message.channel.id]
                        else:
                            cleanup = -1
                    elif message.channel.id in bot.market.settings["cleanup"]:
                        cleanup = bot.market.settings["cleanup"][message.channel.id]
                    if cleanup > 0:
                        yield from asyncio.sleep(cleanup)  # delete messages after 60 seconds
                        if bot.market.running:
                            yield from client.delete_message(message)
                elif not message.author.bot:
                    bot.prefix = bot.market.get_prefix(bot, message)
                    yield from bot.run_command(message, test_role)
                    yield from bot.market.check_reminders(bot)
            yield from bot.update_status(message.author.name)

    print("Creating bot..")
    bot = botlib.Bot(client)
    print("Initialising bot...")
    bot.restarter = restarter
    bot.ping_message = "Ping!"
    bot.name = "MarketBot"
    bot.prefix = "m$"
    bot.tickets = {}
    bot.lookup_enabled = True
    bot.version = "0.1.0"
    bot.register_command("help", help_handle, help_length_handle)
    bot.help_page = botlib.HelpPage(":notebook_with_decorative_cover:MarketBot help homepage: (Note: command prefixs are channel specific, prefix isn't required when PMing the bot)")
    test_role = botlib.Role(all=True)
    print("Finding bot token...")
    token = None
    carbon_key = None
    is_test_bot = True

    if is_test_bot:
        f = open("credentials_test.txt")
    else:
        f = open("credentials.txt")
    for line in f:
        if token is None:
            token = line.replace("\n", "")
        else:
            carbon_key = line.replace("\n", "")
            break

    f.close()
    print("Logging in...")

    client.run(token)
    #restarter()
