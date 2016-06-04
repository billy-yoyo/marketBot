import main, importlib


def restarter():
    print("reloading main.py")
    importlib.reload(main)
    print("Restart done!")
    main.run(restarter, 1)

main.run(restarter)
