import botlib
import discord
import asyncio
import time


def run(restarter, restart_source=None):
    client = discord.Client()

    def help_handle(bot, message, cmd):
        yield from bot.client.send_message(message.author, help_page.get(bot, command=cmd[1:]))


    def help_length_handle(cmd):
        return 1

    @client.event
    @asyncio.coroutine
    def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('Loading plugins:')
        botlib.load_plugins(bot, help_page)
        if restart_source is not None:
            print('Confirming successful restart.')
            yield from client.send_message(restart_source.channel, ">>> Restart Complete <<<")
        print('Done!')

    @client.event
    @asyncio.coroutine
    def on_message(message):
        if message.author.id == bot.client.user.id:
            if message.content == bot.ping_message:
                yield from bot.client.edit_message(message, "Pong! Took " + str(int((time.time() - bot.ping_start)*1000000)/1000) + " milliseconds")
            if not message.channel.is_private:
                yield from asyncio.sleep(60)  # delete messages after 60 seconds
                if bot.market.running:
                    yield from client.delete_message(message)
        else:
            yield from bot.run_command(message, test_role)

    print("Creating bot..")
    bot = botlib.Bot(client)
    print("Initialising bot...")
    bot.restarter = restarter
    bot.ping_message = "Ping!"
    bot.name = "MarketBot"
    bot.prefix = "m$"
    bot.lookup_enabled = True
    bot.register_command("help", help_handle, help_length_handle)
    help_page = botlib.HelpPage(":notebook_with_decorative_cover:MarketBot help homepage:")
    test_role = botlib.Role(all=True)
    print("Finding bot token...")
    token = None
    f = open("credentials.txt")
    for line in f:
        token = line
        break
    f.close()
    print("Logging in...")
    client.run(token)
    restarter()
