import ast, os, subprocess, pickle, marshal

CODE_SAFE = 0
ERROR_IMPORT = 1
ERROR_CLASS = 2
ERROR_GLOBAL = 3
ERROR_YIELD = 4
ERROR_FUNCTION_NAME = 5
ERROR_FUNCTION_CALL = 6
ERROR_FUNCTION = 7
ERROR_WHILE = 8
ERROR_RETURN = 9

error_map = [
    "Code is fine",
    "Code cannot contain import",
    "Code cannot define a class",
    "Code cannot load a global",
    "Code cannot yield anything",
    "Code cannot contain the string '___EXEC_FUNCTION___'",
    "Code cannot contain a function call not on the whitelist",
    "Code cannot define a function",
    "Code cannot use while loops",
    "Code does not contain a return"
]

obj_banned = {
    ast.Import: ERROR_IMPORT,
    ast.ImportFrom: ERROR_IMPORT,
    ast.ClassDef: ERROR_CLASS,
    ast.Global: ERROR_GLOBAL,
    ast.Yield: ERROR_YIELD,
    ast.YieldFrom: ERROR_YIELD,
    ast.FunctionDef: ERROR_FUNCTION,
    ast.While: ERROR_WHILE
}


def _is_safe(node):
    if type(node) in obj_banned:
        return obj_banned[type(node)]
    return 0


def check_safe(code, allowed_function_names=[]):
    if "___EXEC_FUNCTION___" in code:
        return ERROR_FUNCTION_NAME
    source = ast.parse(code)
    next = [source]
    has_return = False
    while len(next) > 0:
        new_next = []
        for obj in next:
            if type(obj) is ast.Return:
                has_return = True
            result = _is_safe(obj)
            if result > 0:
                return result
            if type(obj) is ast.Call:
                if type(obj.func) is ast.Name:
                    if obj.func.id not in allowed_function_names:
                        return ERROR_FUNCTION_CALL
                elif type(obj.func) is ast.Attribute:
                    if obj.func.attr not in allowed_function_names:
                        return ERROR_FUNCTION_CALL
                else:
                    return ERROR_FUNCTION_CALL
            new_next += ast.iter_child_nodes(obj)
        next = new_next
    if not has_return:
        return ERROR_RETURN
    return 0


def get_exec_function(code, local_space=[]):
    code = "def ___EXEC_FUNCTION___(" +  ", ".join(local_space) +  "):\n    " + "\n    ".join(code.split("\n"))
    exec_local = {}
    exec(code, {}, exec_local)
    return exec_local["___EXEC_FUNCTION___"]


class ExecTimeoutError(Exception):
    pass

def _handle_timeout(a, b):
    raise ExecTimeoutError


def check_timeout(seconds, func, *args):
    index = 0
    fname = "automod/dump_" + str(index)
    while os.path.exists(fname):
        index += 1
        fname = "automod/dump_" + str(index)
    f = open(fname+"_func", "wb")
    marshal.dump(func.__code__, f)
    f.close()
    for i in range(len(args)):
        f = open(fname + "_obj_" + str(i), "wb")
        for obj in args:
            pickle.dump(obj, f)
        f.close()

    result = subprocess.call(["python", "safeexec_sub.py", str(seconds), fname])
    os.remove(fname + "_func")
    for i in range(len(args)):
        os.remove(fname + "_obj_" + str(i))

    if result == 1:
        return True
    return False


#example_code = """d = { 'a': 'okay', 'b': 'not okay'}
#return d['a'] """
#print(check_safe(example_code, ["test"]))
#func = get_exec_function(example_code)

#def test_func():
#    while True:
#        pass

#print(check_timeout(1, test_func))

#print("hello world")