
MarketBot is a bot for Discord written in python 3.4 with discord.py

If you're looking for information about the bot and how to use it, please visit http://billyoyo.me

Note: MarketBot won't run if you run it from here as I've .gitignored some files it relies on (no code, just things like word-lists)
so if you want to run it look at Missing File Information

File information:

    /src/run.py - runs the bot
    /src/main.py - starts the bot (this is what run.py runs)
    /src/botlib.py - some classes to make my life easier and keep all the information nice and together
    /src/market.py - container for all of the persistent data (data kept through saves) also where the main bulk of the game is.
    /src/profiler.py - creates profile cards for users. WIP
    /src/formatter.py - formats my hangman/speedtype word list for me.
    /src/corruptfun2.py - filters a 64bit .bmp file with a kernal
    /src/poem-getter.py - gets a large list of poems from a website and loads them in to poems.txt
    /src/textart.py - creates text art in a similar fashion to pygame
    /src/vectorscript.py - unused, not sure if I'll bring this back, it is an image equivelant to textart
    /srt/styload.py - used to load and run .sty files, see /stories/example.sty for an example of what .sty looks like
    /src/plugins/market_cmds.py - contains the code for the main game + some extra (generally 'core' and 'misc' commands)
    /src/plugins/fun_cmds.py - contains the code for the 'fun' commands
    /src/plugins/moderation_cmds.py - contains the code for the 'moderation' commands
    /src/plugins/util_cmds.py - contains the code for the 'utility' commands
    /src/avatars - unused whilst profiler is out of action
    /src/card_img - unused whilst profiler is out of action
    /src/cards - unused whilst profiler is out of action
    /src/corrupt - contains .bmp files for use with corruptfun2
    /src/stories - contains .sty files for use with styload

Missing information:

    /src/adminlist.txt - list of client ID's who are admins - one ID per line
    /src/credentials.txt - the bot's token and nothing else
    /src/riddles.txt - list of riddles, riddles are seperated by ;; and question/answers are seperated by ::
    /src/words_new.txt - list of words, all on one line, seperated by ; (this is what I made formatter.py for)
    /src/data - create this folder
    /src/avatars - create this folder
    /src/card_img - create this folder
    /src/cards - create this folder
    /src/scripts - create this folder
    
some of those folders are currently unused because of pygame not being installed and most of them will create themselves.

**Want to create your own plugin?**

  * Go ahead, it's pretty easy, to create a plugin:
  * create your plugin file, name it whatever you want (as long as it ends in .py)
  * create a function "setup(bot, help_page, filename)" in your plugin file
  * create as many command handlers as you want, these come in pairs: 
  
        example_handle(bot, message, command)
        example_handle_l(command)
    
  * where bot is the instance of the botlib Bot class, message is the discord.Message instance and command is the command split by " "
  (so m$example command -> command=["example", "command"])
  * example\_handle has no returns and example\_handle\_l should just return 1 (it's not relevant as I haven't implemented command binds)
  * I'll get around to making example\_handle\_l not-required at some point (I'll make sure it's backwards compatible though)
  * now in your setup function register your handlers:
  
        bot.register_command("command_root", example_handle, example_handle_l)
    
  * Now the command will be registered. 
  * I don't really have a solution to how you can test your own plugins though, as downloading and running /src/ won't compile I'm afraid,
  * if you want to just develop them and send them to me I can run them on my test bot and debug them with/for you though!
  
