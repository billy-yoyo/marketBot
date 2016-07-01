import signal, pickle, safeexec, sys, marshal, types, traceback, os

def _handle_timeout(a, b):
    raise safeexec.ExecTimeoutError

def check_timeout(seconds, func, *args):
    try:
        signal.signal(signal.SIGALRM, _handle_timeout)
        signal.alarm(seconds)
        try:
            func(*args)
        finally:
            signal.alarm(0)
    except safeexec.ExecTimeoutError:
        return False
    return True

if __name__  == "__main__":
    args = sys.argv
    seconds = int(args[1])
    fname = args[2]
    f = open(fname + "_func", "rb")
    args.append(types.FunctionType(marshal.load(f), globals(), "func"))
    f.close()

    index = 0
    while os.path.exists(fname + "_obj_" + str(index)):
        f = open(fname + "_obj_" + str(index), "rb")
        args.append(pickle.load(f))
        f.close()
        index += 1

    if check_timeout(seconds, *args[3:]):
        exit(1)