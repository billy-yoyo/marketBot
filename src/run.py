import main, importlib

# C:\Python33\python projects\marketBot\src

def restarter():
    print("reloading main.py")
    importlib.reload(main)
    print("Restart done!")
    main.run(restarter, 1)

main.run(restarter)
