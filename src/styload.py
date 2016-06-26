

def load(filename):
    f = open(filename, "r")
    story = {
        "@vars": {},
        "@head": [],
        "@tail": []
    }
    block = None
    for line in f:
        line = line.replace("\n", "")
        while len(line) > 0 and (line[0] == "\t" or line[0] == " " or line[0] == "{" or line[0] == "}"):
            line = line[1:]
        if len(line) > 0:
            escaped = False
            if line[0] == "\\":
                line = line[1:]
                escaped = True
            if line.startswith("$") and not escaped:
                spl = line[1:].split("=")
                vdef = spl[0].split(" ")
                vdef[1] = " ".join(vdef[1:])
                raw_value = "=".join(spl[1:])
                story["@vars"][vdef[1]] = _get_value(vdef, raw_value)
            elif line.startswith("@") and not escaped:
                if block is not None:
                    story[block["title"]] = block
                if "@" in line[1:]:
                    raise SyntaxError
                block = {
                    "title": line[1:],
                    "text": [],
                    "options_order": [],
                    "options": {},
                    "startup": [],
                    "head": True,
                    "tail": True
                }
            elif line.startswith("!HEAD ") and not escaped:
                text = line[6:]
                while len(text) > 0 and text[0] == " ":
                    text = text[1:]
                if len(text) > 0 and text[0] == "\\":
                    text = text[1:]
                story["@head"].append(text)
            elif line.startswith("!TAIL ") and not escaped:
                text = line[6:]
                while text[0] == " ":
                    text = text[1:]
                if text[0] == "\\":
                    text = text[1:]
                story["@tail"].append(text)
            elif line.startswith(">") and not escaped: # option definition
                line = line[1:]
                while len(line) > 0 and (line[0] == "\t" or line[0] == " " or line[0] == "{" or line[0] == "}"):
                    line = line[1:]
                opescaped = False
                if line[0] == "\\":
                    line = line[1:]
                    opescaped = True
                if line.startswith("@") and not opescaped:
                    if "@" in line[1:]:
                        raise SyntaxError
                    block["options_order"].append(line[1:])
                    block["options"][line[1:]] = {
                        "title": line[1:],
                        "text": [],
                        "args": [],
                        "enabled": True
                    }
                elif line.startswith("#") and not opescaped:
                    arg = [x.upper() for x in line[1:].split(" ")]
                    if arg[0] == "ENABLE":
                        if arg[1] == "HEAD":
                            block["head"] = True
                        elif arg[1] == "TAIL":
                            block["tail"] = True
                        else:
                            raise IndexError
                    elif arg[0] == "DISABLE":
                        if arg[1] == "HEAD":
                            block["head"] = False
                        elif arg[1] == "TAIL":
                            block["tail"] = False
                        else:
                            raise IndexError
                    else:
                        print("INVALID: " + arg[0])
                        raise IndexError
                elif line.startswith("?") and not opescaped:
                    block["startup"].append(line[1:])
                elif line.startswith(">") and not opescaped:
                    arg = line[1:]
                    if arg.startswith("#"):
                        command = arg[1:].upper()
                        if command == "DISABLE":
                            block["options"][block["options_order"][-1]]["enabled"] = False
                        elif command == "ENABLE":
                            block["options"][block["options_order"][-1]]["enabled"] = True
                    else:
                        block["options"][block["options_order"][-1]]["args"].append(arg)
                else:
                    block["options"][block["options_order"][-1]]["text"].append(line)
            elif not line.startswith("//") and block is not None and (line != "" or escaped): # not a comment
                block["text"].append(line)
    story[block["title"]] = block
    f.close()

    return story


def _get_value(vdef, raw_value):
    if "@" in vdef[1]:
        raise SyntaxError
    if vdef[0] == "int":
        return int(raw_value)
    elif vdef[0] == "str":
        return raw_value
    elif vdef[0] == "float":
        return float(raw_value)
    elif vdef[0] == "bool":
        raw_value = raw_value.lower()
        if raw_value == "true":
            return True
        elif raw_value == "false":
            return False
        else:
            raise SyntaxError
    else:
        raise SyntaxError


def _run_command(story, arg):
    if arg.startswith("$"):
        spl = arg[1:].split("=")
        vdef = spl[0].split(" ")
        vdef[1] = " ".join(vdef[1:])
        raw_value = "=".join(spl[1:])
        story["@vars"][vdef[1]] = _get_value(vdef, raw_value)
    elif not arg.startswith("#"):
        spl = arg.split("@")
        if spl[0] == "GOTO":
            return spl[1]
        elif spl[0] == "ENABLE":
            if spl[1] in story and spl[2] in story[spl[1]]["options"]:
                story[spl[1]]["options"][spl[2]]["enabled"] = True
        elif spl[0] == "DISABLE":
            if spl[1] in story and spl[2] in story[spl[1]]["options"]:
                story[spl[1]]["options"][spl[2]]["enabled"] = False
        elif spl[0] == "SET":
            dest = None
            index = 2
            if spl[1] == "OPTION":
                dest = story[spl[2]]["options"][spl[3]]
                index = 4
            else:
                dest = story[spl[1]]
            if spl[index] == "TEXT":
                insert = False
                if spl[index+1] == "INSERT":
                    index += 1
                    insert = True
                in_index = int(spl[index+1])
                text = "@".join(spl[index+2:])
                while in_index >= len(dest["text"]):
                    dest["text"].append("")
                if insert:
                    dest["text"].insert(in_index, text)
                else:
                    dest["text"][in_index] = text
            elif spl[index] == "HEAD":
                if spl[index + 1].upper() == "TRUE":
                    dest["head"] = True
                elif spl[index + 1].upper() == "FALSE":
                    dest["head"] = False
                else:
                    raise SyntaxError
            elif spl[index] == "TAIL":
                if spl[index+1].upper() == "TRUE":
                    dest["tail"] = True
                elif spl[index+1].upper() == "FALSE":
                    dest["tail"] = False
                else:
                    raise SyntaxError
            else:
                raise SyntaxError
        elif spl[0] == "CLEAR":
            dest = None
            if spl[1] == "OPTION":
                dest = story[spl[2]]["options"][spl[3]]
            else:
                dest = story[spl[1]]
            dest["text"] = []
        elif spl[0] == "IF":
            operators = {
                            "==": lambda a,b: a == b,
                            ">=": lambda a,b: a >= b,
                            ">": lambda a,b: a > b,
                            "<=": lambda a,b: a <= b,
                            "<": lambda a,b: a < b,
                            "!=": lambda a,b: a != b
                        }
            for op in operators:
                if op in spl[1].replace("\\" + op, ""):
                    tempspl = spl[1].split(op)
                    opspl = ["", ""]
                    index = 0
                    for s in tempspl:
                        if s[-1] == "\\":
                            opspl[index] = opspl[index] + s[:-1] + op
                        else:
                            opspl[index] = opspl[index] + s
                            index += 1
                    v1 = opspl[0]
                    if v1.startswith("$"):
                        vspl = v1[1:].split("=")
                        vdef = vspl[0].split(" ")
                        raw_value = "=".join(vspl[1:])
                        v1 = _get_value(vdef, raw_value)
                    elif v1 in story["@vars"]:
                        v1 = story["@vars"][v1]
                    else:
                        raise IndexError

                    v2 = opspl[1]
                    if v2.startswith("$"):
                        vspl = v2[1:].split("=")
                        vdef = vspl[0].split(" ")
                        raw_value = "=".join(vspl[1:])
                        v2 = _get_value(vdef, raw_value)
                    elif v2 in story["@vars"]:
                        v2 = story["@vars"][v2]
                    else:
                        raise IndexError

                    if operators[op](v1,v2):
                        return _run_command(story, "@".join(spl[2:]))
                    break
    return None


def run_option(story, card, option):
    next_card = card
    if card in story and option in story[card]["options"]:
        for arg in story[card]["options"][option]["args"]:
            result = _run_command(story, arg)
            if result is not None:
                next_card = result
    return next_card


def _format_line(story, line):
    find = line.find("$")
    while find >= 0:
        if find < len(line):
            if line[find+1] == "(":
                start = find
                vname = ""
                find += 2
                while line[find] != ")":
                    vname += line[find]
                    find += 1
                var = str(story["@vars"][vname])
                line = line[:start] + var + line[find+1:]
                find = start + len(var)
            elif line[find+1] == "\\":
                line = line[:find+1] + line[find+2:]
        find = line.find("$", find)
    return line


def get_text(story, card, option=None):
    if option is not None:
        text = story[card]["options"][option]["text"]
        for i in range(len(text)):
            text[i] = _format_line(story, text[i])
        return text
    else:
        for line in story[card]["startup"]:
            _run_command(story, line)
        text = story[card]["text"][:]
        if story[card]["head"]:
            text = story["@head"] + text
        if story[card]["tail"]:
            text = text + story["@tail"]
        for i in range(len(text)):
            text[i] = _format_line(story, text[i])
        return text


#print(load("example.sty"))