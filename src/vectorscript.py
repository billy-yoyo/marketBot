import math, pygame, sys, _io, os
from pygame import Surface

pygame.init()

#
# Made a long time ago. Bad code.
#
#
class ValueFinder:
    def __init__(self, colours, texts, varis):
        self.colours = colours
        self.texts = texts
        self.varis = varis

    def getColour(self, var):
        if len(var) == 0:
            return None
        if var[0] == "[":
            var = var[1:-1]
            split = var.split(",")
            if len(split) == 3:
                return pygame.Color(self.getInt(split[0]), self.getInt(split[1]), self.getInt(split[2]))
            elif len(split) == 4:
                return pygame.Color(self.getInt(split[0]), self.getInt(split[1]), self.getInt(split[2]),
                                    self.getInt(split[3]))
        else:
            return self.colours[var]
        return None

    def getString(self, var):
        var = str(var)
        if len(var) == 0:
            return None
        if var[0] == "$":
            var = var[1:]
            if var in self.texts.keys():
                return self.texts[var]
            elif var in self.varis.keys():
                return str(self.varis[var])
            else:
                return "$" + var
        return var

    def getFloat(self, var):
        if len(var) == 0:
            return None
        if var[0] == "$":
            var = var[1:]
            if var in self.texts.keys():
                try:
                    return float(self.texts[var])
                except ValueError:
                    pass
            if var in self.varis.keys():
                try:
                    return float(self.varis[var])
                except (ValueError, TypeError):
                    pass
            return None
        else:
            try:
                return float(var)
            except ValueError:
                return None

    def getInt(self, var):
        if var != None:
            return int(self.getFloat(var))
        return 0

    def getBool(self, var):
        var = self.getString(var)
        if var != None:
            if var.lower() == "true":
                return True
            elif var.lower() == "false":
                return False
        return None


def render(vf, line, screen):
    width, height = screen.get_width(), screen.get_height()
    parts = line.split(" ")
    name = parts[0].upper()
    if name == "RECT":
        x, y, w, h, colour = vf.getFloat(parts[1]) * width, vf.getFloat(parts[2]) * height, vf.getFloat(
            parts[3]) * width, vf.getFloat(parts[4]) * height, vf.getColour(parts[5])
        border = 0
        if len(parts) > 6:
            border = vf.getInt(parts[6])
        pygame.draw.rect(screen, colour, [int(x), int(y), int(w), int(h)], border)
    elif name == "CIRC":
        x, y, radius, colour = vf.getFloat(parts[1]) * width, vf.getFloat(parts[2]) * height, vf.getFloat(
            parts[3]) * width, vf.getColour(parts[4])
        border = 0
        if len(parts) > 5:
            border = vf.getInt(parts[5])
        pygame.draw.circle(screen, colour, [int(x), int(y)], int(radius), border)
    elif name == "ELIP":
        x, y, w, h, colour = vf.getFloat(parts[1]) * width, vf.getFloat(parts[2]) * height, vf.getFloat(
            parts[3]) * width, vf.getFloat(parts[4]) * height, vf.getColour(parts[5])
        border = 0
        if len(parts) > 6:
            border = vf.getInt(parts[6])
        pygame.draw.ellipse(screen, colour, [int(x), int(y), int(w), int(h)], border)
    elif name == "LINE":
        x0, y0, x1, y1, colour = vf.getFloat(parts[1]) * width, vf.getFloat(parts[2]) * height, vf.getFloat(
            parts[3]) * width, vf.getFloat(parts[4]) * height, vf.getColour(parts[5])
        border = 1
        if len(parts) > 6:
            border = vf.getInt(parts[6])
        if border < 1:
            border = 1
        pygame.draw.line(screen, colour, [int(x0), int(y0)], [int(x1), int(y1)], border)
    elif name == "FILL":
        colour = vf.getColour(parts[1])
        screen.fill(colour)
    elif name == "TEXT":
        x, y, fontname, fontsize, colour = vf.getFloat(parts[1]) * width, vf.getFloat(parts[2]) * height, vf.getString(
            parts[3]).lower(), vf.getFloat(parts[4]) * width, vf.getColour(parts[5])
        text = ""
        for i in range(6, len(parts)):
            text = text + vf.getString(parts[i])
            if i != len(parts) - 1:
                text = text + " "
        font = pygame.font.SysFont(fontname, int(fontsize))
        label = font.render(text, 10, colour)
        screen.blit(label, [int(x), int(y)])
    elif name == "POLY":
        colour = vf.getColour(parts[1])
        points = []
        n = 2
        while n < len(parts) - 1:
            x, y = vf.getFloat(parts[n]) * width, vf.getFloat(parts[n + 1]) * height
            points.append([int(x), int(y)])
            n += 2
        border = 0
        if len(parts) % 2 != 0:
            border = vf.getInt(parts[len(parts) - 1])

        pygame.draw.polygon(screen, colour, points, border)
    elif name == "PRINT":
        text = ""
        for i in range(1, len(parts)):
            text = text + vf.getString(parts[i])
            if i != len(parts) - 1:
                text = text + " "
        print(text)


def render_file(file, width, height, args):
    surf = Surface((width, height))
    surf.fill([0, 0, 0, 0])
    islist = False
    f = None
    count, maxcount = 0, 1
    line = ""

    if type(file) is list:
        islist = True
    else:
        if type(file) == _io.TextIOWrapper:
            f = file
        else:
            f = open(file, "r")

    colours = {}
    texts = {}
    varis = {}

    if islist:
        line = file[count]
        maxcount = len(file)
        count += 1
    else:
        line = f.readline()

    lines = []
    block = False
    while (line != '' and islist == False) or (count <= maxcount and islist == True):
        lines.append(line)
        if line != '\n':
            line = line.replace("\n", "")
            nospace = line.replace(' ', '')
            if block:
                if nospace[len(nospace) - 1] == "}":
                    block = False
            elif len(nospace) > 0:
                if nospace[len(nospace) - 1] == "}":
                    removed = ''
                    while removed != '}':
                        removed = line[len(line) - 1]
                        line = line[:-1]
                    nospace = line.replace(' ', '')
                if len(nospace) > 0:
                    vf = ValueFinder(colours, texts, varis)
                    if nospace[0] == '&':
                        line = nospace
                        line = line.replace('&', '', 1)
                        split1 = line.split("=")
                        name = split1[0]
                        colour = vf.getColour(split1[1])
                        colours[name] = colour
                    elif nospace[0] == '*':
                        line = line.replace('*', '', 1)
                        split1 = line.split("=")
                        split2 = split1[1].split(" ")
                        text = ""
                        for i in range(len(split2)):
                            text = text + vf.getString(split2[i])
                            if i != len(split2) - 1:
                                text = text + " "
                        texts[split1[0]] = text
                    elif nospace[0] == '$':
                        line = nospace
                        line = line.replace('$', '', 1)
                        split1 = line.split("=")
                        name = split1[0]
                        index = vf.getInt(split1[1])
                        if len(args) > index:
                            varis[name] = args[index]
                    elif nospace[0] == '!':
                        line = nospace
                        line = line.replace('!', '', 1)
                        split1 = line.split("=")
                        name = split1[0]
                        arg = vf.getString(split1[1])
                        varis[name] = arg
                    elif nospace[len(nospace) - 2:] == "){" and nospace[0] == "(":
                        line = nospace[1:-2]
                        if "==" in line:
                            split = line.split("==")
                            if vf.getString(split[0]) != vf.getString(split[1]):
                                block = True
                        else:
                            foo = vf.getBool(line)
                            if foo == False or foo == None:
                                block = True
                                # elif foo == None:
                                # foo = vf.getFloat(line)
                                # if foo == None:
                                #        foo = vf.getString(line)
                                #        print(foo, ":", line)
                                #        if foo == line or foo == None:
                                #            block = True
                    else:
                        render(vf, line, surf)
        if islist:
            if count < maxcount:
                line = file[count]
            count += 1
        else:
            line = f.readline()

    return surf
