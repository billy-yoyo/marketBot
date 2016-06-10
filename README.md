
MarketBot is a bot for Discord written in python 3.4 with discord.py

If you're looking for information about the bot and how to use it, please visit http://billyoyo.me

File information:

    /src/run.py - runs the bot
  
    /src/main.py - starts the bot (this is what run.py runs)
  
    /src/botlib.py - some classes to make my life easier and keep all the information nice and together
  
    /src/market.py - container for all of the persistent data (data kept through saves) also where the main bulk of the game is.
  
    /src/profiler.py - creates profile cards for users. WIP
  
    /src/formatter.py - formats my hangman/speedtype word list for me.
  
    /src/plugins/market_cmds.py - contains the code for the main game + some extra (generally 'core' and 'misc' commands)
  
    /src/plugins/fun_cmds.py - contains the code for the 'fun' commands
  
    /src/plugins/moderation_cmds.py - contains the code for the 'moderation' commands
  
    /src/plugins/util_cmds.py - contains the code for the 'utility' commands
  



Want to create your own plugin?

  Go ahead, it's pretty easy, to create a plugin:
  
  create your plugin file, name it whatever you want (as long as it ends in .py)
  
  create a function "setup(bot, help_page, filename)" in your plugin file
  
  create as many command handlers as you want, these come in pairs: 
  
    example_handle(bot, message, command)
    example_handle_l(command)
    
  where bot is the instance of the botlib Bot class, message is the discord.Message instance and command is the command split by " "
  (so m$example command -> command=["example", "command"])
    
  example\_handle has no returns and example\_handle\_l should just return 1 (it's not relevant as I haven't implemented command binds)
  
  I'll get around to making example\_handle\_l not-required at some point (I'll make sure it's backwards compatible though)
  
  in your setup function register your handlers:
  
    bot.register_command("command_root", example_handle, example_handle_l)
    
  Now the command will be registered. 
  
  I don't really have a solution to how you can test your own plugins though, as downloading and running /src/ won't compile I'm afraid,
  
  if you want to just develop them and send them to me I can run them on my test bot and debug them with/for you though!
  
