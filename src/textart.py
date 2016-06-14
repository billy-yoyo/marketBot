import math, random


class Art:

    # internal method to help calculate if a point is inside a triangle
    #   p1, p2, p3 = points [x, y]
    @staticmethod
    def _sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

    # internal method to calculate whether or not a point is inside a triangle
    #   p = the point [x, y] to check
    #   p1, p2, p3 = the points [x, y] that define the triangle
    @staticmethod
    def _is_in_triangle(p, p1, p2, p3):
        b1 = Art._sign(p, p1, p2) <= 0
        b2 = Art._sign(p, p2, p3) <= 0
        b3 = Art._sign(p, p3, p1) <= 0

        return (b1 == b2) and (b2 == b3)

    # internal method to find the length of a vector
    #   x = the x value of the vector
    #   y = the y value of the vector
    @staticmethod
    def _length(x, y):
        return math.sqrt(math.pow(x, 2) + math.pow(y, 2))

    # internal method to convert a point to a unit (length 1)
    #   p = a point [x, y]
    @staticmethod
    def _unit(p):
        length = Art._length(p[0], p[1])
        return [p[0] / length, p[1] / length]

    # internal method to add two points together
    #   p1 = the point [x, y] to add
    #   p2 = the point [x, y] to add
    @staticmethod
    def _add(p1, p2):
        return [p1[0] + p2[0], p1[1] + p2[1]]

    # internal method to minus one point from another
    #   p1 = the point [x, y] to subtract from
    #   p2 = the point [x, y] to subtract
    @staticmethod
    def _minus(p1, p2):
        return [p1[0] - p2[0], p1[1] - p2[1]]

    # initializer:
    #   width = the width of the art
    #   height = the height of the art
    #   background = the character to fill the art with, defaults to " "
    def __init__(self, width, height, background=" "):
        self.width = width
        self.height = height

        self.grid = [background * width] * height

    # creates a copy of this art object
    def copy(self):
        art = Art(self.width, self.height)
        for y in range(len(self.grid)):
            art.grid[y] = self.grid[y]
        return art

    # clamps that x value so that it lies inside the art grid
    def clampx(self, x):
        return min(self.width, max(0, x))

    # clamps that list of x values so they all lie inside the art grid
    def clampxs(self, xs):
        return [self.clampx(x) for x in xs]

    # clamp that y value so that it lies inside the art grid
    def clampy(self, y):
        return min(self.height, max(0, y))

    # clamp that list of y values so they all lie inside the art grid
    def clampys(self, ys):
        return [self.clampy[y] for y in ys]

    # set [x, y] to v
    def set(self, x, y, v):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y] = self.grid[y][:x] + v + self.grid[y][x+1:]
        return self

    # get the value at [x, y]
    def get(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return " "

    def fill(self, v):
        for y in range(self.height):
            self.grid[y] = v * self.width

    # draw a rectangle on to art
    #   v = the character to draw, must be a single character
    #   rect = a list [x, y, width, height] describing the rectangle
    #   border = the width of the border, 0 means filled in (defaults to 0)
    def rect(self, v, rect, border=0):
        if len(v) == 1:
            border = math.floor(border)
            sx, sy, width, height = rect[0], rect[1], rect[2], rect[3]
            lx, ly = self.clampx(sx), self.clampy(sy)
            hx, hy = self.clampx(sx + width), self.clampy(sy + height)
            if border == 0:
                xline = v * (hx - lx)
                for y in range(ly, hy):
                    self.grid[y] = self.grid[y][:lx] + xline + self.grid[y][hx:]
                return True
            else:
                if border < math.ceil(width/2):
                    xline = v * (hx - lx)
                    bline = v * border
                    lhs = self.clampx(lx + border)
                    rhs = self.clampy(lx  + width - border)
                    for y in range(ly, hy):
                        if y < ly+border or y > sy+height-border-1:
                            self.grid[y] = self.grid[y][:lx] + xline + self.grid[y][hx:]
                        else:
                            self.grid[y] = self.grid[y][:lx] + bline + self.grid[y][lhs:rhs]
                            if rhs < self.width:
                                self.grid[y] += bline + self.grid[y][hx:]
                    return True
        return False

    # draws a square on to the art
    # this is equivelant to doing rect(v, [p[0], p[1], size, size], border)
    #   v = the character to draw, must be a single character
    #   p = the top-left corner of the square [x, y]
    #   size = the width and height of the square
    #   border = the width of the border, 0 means filled in (defaults to 0)
    def square(self, v, p, size, border=0):
        return self.rect(v, [p[0], p[1], size, size], border)

    # draws a circle on to the art
    #   v = the character to draw, must be a single character
    #   cp = the centre of the circle [x, y]
    #   radius = the radius of the circle
    #   border = the width of the border, 0 means filled in (defaults to 0)
    def circle(self, v, cp, radius, border=0):
        if len(v) == 1:
            cx, cy = cp[0], cp[1]
            for x in range(self.clampx(cx-radius), self.clampx(cx+radius+1)):
                for y in range(self.clampy(cy-radius), self.clampy(cy+radius+1)):
                    dist = Art._length(cx-x, cy-y)
                    if (dist <= radius and border == 0) or (radius >= dist >= radius-border and border > 0):
                        self.set(x, y, v)
            return True
        return False

    # draws a line on to the art
    #    v = the character to draw, must be a single character
    #    p1, p2 = the ends of the line [x, y]
    #    border = the width of the line, 0 means 1px line (defaults to 0)
    def line(self, v, p1, p2, border=0):
        if len(v) == 1:
            x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
            if x1 == x2:
                return self.rect(v, [x1-border, min(y1, y2), (border*2) + 1, abs(y2-y1) + 1])
            elif y1 == y2:
                return self.rect(v, [min(x1, x2), y1-border, abs(x2-x1) + 1, (border*2) + 1])
            else:
                width, height = x2-x1, y2-y1
                y_step, x_step, steps = 1, 1, 0
                if abs(height) < abs(width):
                    y_step = height / abs(width)
                    if width < 0:
                        x_step = -1
                    steps = abs(width) + 1
                else:
                    x_step = width / abs(height)
                    if height < 0:
                        y_step = -1
                    steps = abs(height) + 1
                x, y = x1, y1
                for i in range(steps):
                    self.square(v, [math.floor(x-border), math.floor(y-border)], math.floor(border*2)+1)
                    x += x_step
                    y += y_step
                return True
        return False

    # draws a collection of lines in a row
    # this is equivelant to doing art.line(v, p0, p1, border) art.line(v, p1, p2, border) etc...
    # where ps = [ p0, p1, p2, ... ]
    #    v = the character to draw, must be a single character
    #    ps = the list of points to draw
    #    border = same as in line
    def lines(self, v, ps, border=0):
        if len(v) == 1:
            if len(ps) > 1:
                last = ps[0]
                for i in range(1, len(ps)):
                    cur = ps[i]
                    self.line(v, last, cur, border)
                    last = cur
                return True
        return False

    # draws a triangle on to the art
    #    v = the character to draw, must be a single character
    #    p1, p2, p3 = the points [x, y] of the triangle
    #    border = the width of the border, 0 means filled in (defaults to 0)
    def triangle(self, v, p1, p2, p3, border=0):
        if len(v) == 1:
            if border == 0:
                centre = [(p1[0] + p2[0] + p3[0]) / 3, (p1[1] + p2[1] + p3[1]) / 3]
                v1 = Art._unit([p1[0] - centre[0], p1[1] - centre[1]])
                v2 = Art._unit([p2[0] - centre[0], p2[1] - centre[1]])
                v3 = Art._unit([p3[0] - centre[0], p3[1] - centre[1]])
                op1, op2, op3 = Art._add(p1, v1), Art._add(p2, v2), Art._add(p3, v3)
                for x in range(self.clampx(min(p1[0], p2[0], p3[0])), self.clampx(max(p1[0], p2[0], p3[0]) + 1)):
                    for y in range(self.clampy(min(p1[1], p2[1], p3[1])), self.clampy(max(p1[1], p2[1], p3[1]) + 1)):
                        if Art._is_in_triangle([x, y], op1, op2, op3):
                            self.set(x, y, v)
                return True
            else:
                return self.line(v, p1, p2, border) and self.line(v, p1, p3, border) and self.line(v, p2, p3, border)
        return False

    # draws a quadrilateral
    # this is equivalent to doing art.triangle(v, p1, p2, p3, border) art.triangle(v, p1, p4, p3, border)
    #    v = the character to draw, must be a single character
    #    p1, p2, p3, p4 = the points [x, y] of the quad
    #    border = the width of the border, 0 means filled in (defaults to 0)
    def quad(self, v, p1, p2, p3, p4, border=0):
        return self.triangle(v, p1, p2, p3, border) and self.triangle(v, p1, p4, p3, border)

    # draws a polygon
    #    v = the character to draw, must be a single character
    #    ps = a list of points [x, y] that define the polygon
    #    border = the width of the border, 0 means filled in (defaults to 0)
    def polygon(self, v, ps, border=0):
        if len(v) == 1:
            if border == 0:
                if len(ps) == 3:
                    self.triangle(v, *ps)
                    return True
                elif len(ps) == 4:
                    self.quad(v, *ps)
                elif len(ps) > 4:
                    i = 0
                    next_poly = []
                    while i < len(ps):
                        next_poly.append(ps[i])
                        self.triangle(v, ps[i%len(ps)], ps[(i+1)%len(ps)], ps[(i+2)%len(ps)])
                        i += 2
                    return self.polygon(v, next_poly)
            elif len(ps) > 2:
                last = ps[0]
                for i in range(1, len(ps) + 1):
                    if i == len(ps):
                        cur = ps[0]
                    else:
                        cur = ps[i]
                    self.line(v, last, cur, border)
                    last = cur
                return True
        return False

    # runs a batch of functions
    #    batch is a dictionary with the format:
    #         { "function-name": [ args ], ... }
    #    for example,
    #         art.batch({ "rect": ["*", [1, 1, 3, 3]], "line": ["*" , [0, 0], [5, 5]] })
    #    is equivalent to:
    #         art.rect("*", [1, 1, 3, 3])
    #         art.line("*", [0, 0], [5, 5])
    def batch(self, batch):
        for f in batch:
            if hasattr(self, f):
                getattr(self, f)(*batch[f])

    # blits another art on to this one
    #    art = the art to draw on to this one (the source art)
    #    dest = the destination to draw the art on to (top-left corner [x, y]) defaults to [0, 0]
    #    area = the area of the source art to draw [x, y, width, height], if None then draws the whole thing (defaults to None)
    #    alpha = the collection of characters which won't get drawn (defaults to " ", can be any amount of chars, e.g. "*,."
    def blit(self, art, dest=[0,0], area=None, alpha=" "):
        if area is None:
            sx, sy, ex, ey = 0, 0, art.width, art.height
        elif len(area) == 2:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), art.width, art.height
        elif len(area) == 3:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[2])
        elif len(area) == 4:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[3])
        else:
            return False
        for x in range(sx, ex):
            for y in range(sy, ey):
                if art.grid[y][x] not in alpha:
                    self.set(x+dest[0]-sx, y+dest[1]-sy, art.grid[y][x])

    # filters the art
    #    func = the function used to filter, one of:
    #               func(art, line) : returns new-line
    #           or  func(art, char) : returns new-char
    #    area = the area to pass the filter, None means the whole area (defaults to None)
    #    bychar = whether or not a line or a character will be passed to the function, passing a line is quicker. (defaults to False, passing a line)
    def filter(self, func, area=None, bychar=False):
        if area is None:
            sx, sy, ex, ey = 0, 0, self.width, self.height
        elif len(area) == 2:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.width, self.height
        elif len(area) == 3:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(
                area[1] + area[2])
        elif len(area) == 4:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(
                area[1] + area[3])
        else:
            return False
        for y in range(sy, ey):
            if bychar:
                nline = self.grid[y][:sx]
                for i in range(sx, ex):
                    nline += func(self, self.grid[y][i])
                self.grid[y] = nline + self.grid[y][ex:]
            else:
                self.grid[y] = self.grid[y][:sx] + func(self, self.grid[y][sx:ex]) + self.grid[y][ex:]

    # replaces all instances of 'old' with 'new', old and new must be the same length
    #    old = the string to replace
    #    new = the string to replace the old string with
    #    inplace = whether or not the replacement will create a new art object or edit this one (default to False, creating a new object)
    def replace(self, old, new, inplace=False):
        if len(old) == len(new):
            if inplace:
                art = self
            else:
                art = self.copy()
            for i in range(len(art.grid)):
                art.grid[i] = art.grid[i].replace(old, new)
            return art
        else:
            return None

    # returns a new art object containing a section of this one
    #     area = the area to cut out, [x, y, width, height] if None this function just returns copy()
    def cut(self, area):
        if area is None:
            return self.copy()
        else:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[3])
            art = Art(area[2], area[3])
            for y in range(sy, ey):
                art.grid[y-sy] = self.grid[y][sx:ex]
            return art

    # prints the lines in to the console
    def print(self):
        for line in self.grid:
            print(line)

    # returns the art object formatted for discord chat.
    def text(self, style=""):
        return "```" + style + "\n" + "\n".join(self.grid) + "\n```"


#def random_filt(art, line):
#    chars = ""
#    for i in range(len(line)):
#        chars += random.choice("+=-%#@*")
#    return chars
#
#art = Art(9, 9)
#art.filter(random_filt, bychar=True)
#print(art.text())
#p1 = [random.randint(0, 8), random.randint(0, 8)]
#p2 = [random.randint(0, 8), random.randint(0, 8)]
#p3 = [random.randint(0, 8), random.randint(0, 8)]
#print(p1)
#print(p2)
#art.lines("*", [[2, 2], [4, 2], [5, 5], [3, 7], [1, 5]])
#art.square("*", [4, 4], 1)
#print(art.text())
#art2 = art.cut([1, 1, 3, 3])
#print(art2.text())
#art.blit(art2, [4, 1])
#print(art.text())
#art3 = art.replace("5", " ")
#print(art3.text())