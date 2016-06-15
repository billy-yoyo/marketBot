import math
import traceback


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

    # internal method to find the square of the length of a vector
    #   x = the x value of the vector
    #   y = the y value of the vector
    @staticmethod
    def _sq_length(x, y):
        return math.pow(x, 2) + math.pow(y, 2)

    # internal method to find the length of a vector
    #   x = the x value of the vector
    #   y = the y value of the vector
    @staticmethod
    def _length(x, y):
        return math.sqrt(Art._sq_length(x, y))

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
    #    area = the area to create a copy of, if None then the area is the whole art, defaults to None
    def copy(self, area=None):
        if area is None:
            sx, sy, ex, ey = 0, 0, self.width, self.height
        elif len(area) == 2:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.width, self.height
        elif len(area) == 3:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[2])
        elif len(area) == 4:
            sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[3])
        else:
            return None

        art = Art(ex-sx, ey-sy)
        for y in range(sy, ey):
            art.grid[y-sy] = self.grid[y][sx:ex]
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
        return [self.clampy(y) for y in ys]

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

    # renders a gradient in to the area defined
    #    vs = the string of characters defining the gradient, must be at least one character
    #    start = the point [x, y] that defines the 'start' of the gradient line
    #    end = the point [x, y] that definds the 'end' of the gradient line
    #    area = the area to draw the gradient in, if None then it's the whole art. Defaults to None.
    def gradient(self, vs, start, end, area=None):
        if len(vs) > 0:
            if area is None:
                sx, sy, ex, ey = 0, 0, self.width, self.height
            elif len(area) == 2:
                sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.width, self.height
            elif len(area) == 3:
                sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[2])
            elif len(area) == 4:
                sx, sy, ex, ey = self.clampx(area[0]), self.clampy(area[1]), self.clampx(area[0] + area[2]), self.clampy(area[1] + area[3])
            else:
                return False

            # the square of the distance from the start to the end
            total_dist_sq = self._sq_length(*self._minus(start, end))
            total_dist = math.sqrt(total_dist_sq)
            dist_const = 0.5 * total_dist
            dist_const_2 = 2 * total_dist
            vslength = len(vs)
            for y in range(sy, ey):
                for x in range(sx, ex):
                    # square of the length from this point to the start
                    d1 = self._sq_length(*self._minus(start, [x, y]))
                    # square of the length from this point to the end
                    d2 = self._sq_length(*self._minus(end, [x, y]))
                    rtd1 = math.sqrt(d1)
                    rtd2 = math.sqrt(d2)
                    # first check if this point is 'behind' the start line
                    # if rtd1 == 0, [x, y] is the start point so set cosd1 = 0 to avoid division by zero errors
                    if rtd1 > 0:
                        # calculate the cosine of the angle between the gradient line and the line from the start to this point
                        cosd1 = (d1 + total_dist_sq - d2) / (2 * rtd1 * total_dist)
                    else:
                        cosd1 = 0
                    if cosd1 <= 0: #angle is greater than or equal to 90 degrees
                        # gradient is behind the start, so use the first value
                        self.set(x, y, vs[0])
                    else:
                        # now check if the point is 'behind' the end line
                        # if rtd2 == 0, [x, y] is the end point so set cosd2 = 0 to avoid division by zero errors
                        if rtd2 > 0:
                            # calculate the cosine of the angle between the gradient line and the line from the end to this point
                            cosd2 = (d2 + total_dist_sq - d1) / (2 * rtd2 * total_dist)
                        else:
                            cosd2 = 0
                        if cosd2 <= 0: # angle is greater than or equal to 90 degrees
                            # gradient is behind the end, so use the last value
                            self.set(x, y, vs[-1])
                        else:
                            # position is within the start and the end.
                            # calculate the perpendicular distance to the start line
                            dist = dist_const + ((d1 - d2) / dist_const_2)
                            # find the index based on the percentage of the total perpendicular distance this point is
                            index = min(vslength-1, max(0, math.floor((dist/total_dist) * vslength)))
                            self.set(x, y, vs[index])
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
        if art is not self:
            if area is None:
                sx, sy, ex, ey = 0, 0, art.width, art.height
            elif len(area) == 2:
                sx, sy, ex, ey = art.clampx(area[0]), art.clampy(area[1]), art.width, art.height
            elif len(area) == 3:
                sx, sy, ex, ey = art.clampx(area[0]), art.clampy(area[1]), art.clampx(area[0] + area[2]), art.clampy(area[1] + area[2])
            elif len(area) == 4:
                sx, sy, ex, ey = art.clampx(area[0]), art.clampy(area[1]), art.clampx(area[0] + area[2]), art.clampy(area[1] + area[3])
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

    # replaces all instances of 'old' with 'new', old and new must be the same length (unless bychar is True, in which case new can be length 1)
    #    old = the string to replace
    #    new = the string to replace the old string with
    #    area = the area of the art to perform the replaces in
    #    inplace = whether or not the replacement will create a new art object or edit this one (default to False, creating a new object)
    #    bychar = whether or not the replacement is done by character or replacing the whole of old with new
    #             replace('xyz', '123', bychar=True) is equivalent to replace('x', '1') replace('y', '2') replace('z', '3')
    #             if bychar is true then 'new' can be a single character, so
    #             replace('xyz', '1', bychar=True) is equivalent to replace('x', '1') replace('y', '1') replace('z' '1')
    #    cut = whether or not to cut out the area defined and just return that, or return the whole art with the swaps done in the area
    #          if true this overrides inplace
    def replace(self, old, new, area=None, inplace=False, bychar=False):
        if len(old) == len(new) or (len(new) == 1 and bychar):
            art = self.copy(area)
            for y in range(art.height):
                if bychar:
                    for i in range(len(old)):
                        if len(new) == 1:
                            newchar = new
                        else:
                            newchar = new[i]
                        art.grid[y] = art.grid[y].replace(old[i], newchar)
                else:
                    art.grid[y] = art.grid[y].replace(old, new)
            if inplace:
                pos = [0, 0]
                if area is not None:
                    pos = [area[0], area[1]]
                self.blit(art, pos)
                return self
            else:
                finalart = self.copy()
                pos = [0, 0]
                if area is not None:
                    pos = [area[0], area[1]]
                finalart.blit(art, pos)
                return finalart
        else:
            return None

    # swaps all instances of s1 and s2 in the art, s1 and s3 must be the same length
    #    s1 = the first string to find
    #    s2 = the second string to find
    #    area = the area of the art to perform the swaps in
    #    inplace = whether or not the replacement will create a new art object or edit this one (default to False, creating a new object)
    #    bychar = whether or not the swap is done by character or by the whole string,
    #             swap('xyz', '123', bychar=True) is equivalent to swap('x', '1') swap('y', '2') swap('z', '3')
    #    cut = whether or not to cut out the area defined and just return that, or return the whole art with the swaps done in the area
    #          if true this overrides inplace
    def swap(self, s1, s2, area=None, inplace=False, bychar=False, cut=False):
        if len(s1) == len(s2):
            art = self.copy(area)
            for y in range(art.height):
                newline = ""
                for x in range(art.width):
                    if x < len(newline):
                        continue
                    else:
                        if bychar:
                            substr = art.grid[y][x]
                            if substr in s1:
                                newline += s2[s1.find(substr)]
                            elif substr in s2:
                                newline += s1[s2.find(substr)]
                            else:
                                newline += substr
                        else:
                            substr = art.grid[y][x:x+len(s1)]
                            if substr == s1:
                                newline += s2
                            elif substr == s2:
                                newline += s1
                            else:
                                newline += art.grid[y][x]
                art.grid[y] = newline
            if cut:
                return art
            elif inplace:
                pos = [0, 0]
                if area is not None:
                    pos = [area[0], area[1]]
                self.blit(art, pos)
                return self
            else:
                finalart = self.copy()
                pos = [0, 0]
                if area is not None:
                    pos = [area[0], area[1]]
                finalart.blit(art, pos)
                return finalart
        else:
            return None

    # prints the lines in to the console
    def print(self):
        for line in self.grid:
            print(line)

    # returns the art object formatted for discord chat.
    def text(self, style=""):
        return "```" + style + "\n" + "\n".join(self.grid) + "\n```"


class ArtResult:
    def __init__(self, width, height):
        self.arts = {
            "main": Art(width, height)
        }
        self.rlog = []

    def get_log(self):
        return self.rlog

    def art(self):
        return self.arts["main"]

    def log(self, message):
        self.rlog.append(message)


# Runs some artscript code,
#   width, height is the width and height of the main artscript art object
#   lines is a list of strings representing the lines of the code
#
#   syntax and functions:
#       objectname.function(arg_0, arg_1, ...) - calls the function with that object
#       function(arg_0, arg_1, ...) - calls the function with the main art object
#   area style argument:
#       if *area is listed as an argument, this means x, y, [width, [height]]
#       where: if x, y are given the copy will be from (x, y) to the end of the art
#              if x, y, width are given the copy will be from (x, y) to (x + width, y + width)
#              if x, y, width, height are given the copy will be from (x, y) to (x + width, y + height)
#   functions: [] means optional arguments, don't include the []
#       new(objectname, width, height) - create a new art object
#       rename(objectname) - rename the object being called to 'objectname'
#       copy(objectname, [*area]) - copies the object being called and creates a new object with the copy named 'objectname'
#                                  area is the area to copy, if not given then it copies the whole object
#       rect(character, x, y, width, height, [border_width]) - draws a rect on to the art object, border_width defaults to 0 (filled)
#       square(character, x, y, size, [border_width]) - equivalent to rect(character, x, y, size, size, [border_width])
#       circle(character, x, y, radius, [border_width]) - draws a circle on to the art object, border_width defaults to 0 (filled)
#       line(character, x1, y1, x2, y2, [line_width]) - draws a line on to the art object, line_width defaults to 0
#       triangle(character, x1, y1, x2, y2, x3, y3, [border_width]) - draws a triangle on to the art object, border_width defaults to 0 (filled)
#       quad(character, x1, y1, x2, y2, x3, y3, x4, y4, [border_width]) - draws a quadrilateral on to the art object, border_width defaults to 0 (filled)
#       polygon(character, x1, y1, x2, y2, ..., [border_width]) - draws a polygon on to the art object, can be any number of pairs of coordinates in ...
#       lines(character, x1, y1, x2, y2, ..., line_width) - draws a series of lines on to the art object, can be any number of pairs of coordinates in ...
#                                                           this is equivalent to line(character, x1, y1, x2, y2, line_width) line(character, x2, y2, x3, y3, line_width) etc.
#       fill(character) - fills the art object with that character
#       set(character, x, y) - sets (x, y) to that character
#       gradient(char_gradient, x1, y1, x2, y2, [*area]) - renders a gradient on to the art, restricted to area if given
#                                                         x1, y1 is the start of the gradient line, x2 y2 is the end of the gradient line
#       replace(old, new, [*area], [bychar=True/False]) - replaces all instances of 'old' with 'new', restricted to area if given. old and new must be the same length
#                                                        if bychar=True then it does it on a character basis, so replace('xy', '12', bychar=True) is equivalent to:
#                                                        replace('x', '1') replace('y', '2')
#                                                        if bychar=True then 'new' can be a single character, in which case replace('xyz', '1', bychar=True) is equivalent to:
#                                                        replace('x', '1') replace('y', '1') replace('z', '1')
#       swap(s1, s2, [*area] [bychar=True/False]) - sets all instances of 's1' to 's2' and all instances of 's2' to 's1', restricted to area if given. s1 and s2 must be the same length
#                                                   if bychar=True then it does it on a character basis, so swap('xy', '12', bychar=True) is equivalent to:
#                                                   swap('x', '1') swap('y', '2')
#                                                   swap DOES NOT support the same functionality as replace and s1 and s2 must always be the same length.
#       blit(objectname, [x, y, [*area]], [alpha=chars]) - draws that object on to the art,
#                                                          x, y are the coordinates it gets rendered to, defaults to 0, 0
#                                                          *area is the area of the object to get rended on to the art, default to all of it
#                                                           alpha=chars, chars are the characters that will be ignored when drawing the object (won't be drawn)
def art_script(width, height, lines):
    result = ArtResult(width, height)
    for line in lines:
        try:
            if "(" in line and line[-1] == ")":
                art = result.arts["main"]
                artname = "main"
                if "." in line and line.find(".") < line.find("("):
                    artsplit = line.split(".")
                    line = artsplit[1].replace(" ", "")
                    artname = artsplit[0]
                    if artsplit[0] in result.arts:
                        art = result.arts[artsplit[0]]
                    else:
                        art = None
                if art is not None:
                    ind = line.find("(")
                    fname = line[:ind]
                    tempargs = line[ind + 1:-1].replace("..", " ").split(",")
                    args = [tempargs[0]]
                    for i in range(1, len(tempargs)):
                        if len(tempargs) > 0 and tempargs[i-1][-1] == "\\" and (len(tempargs) > 2 and (tempargs[i-1][-2] != "\\" or (len(tempargs) > 3 and tempargs[i-1][-2] == "\\" and tempargs[i-1][-3] == "\\"))):
                            args[-1] += "," + tempargs[i]
                        else:
                            args.append(tempargs[i])
                    args = [x.replace("\\,", ",").replace("\\\\", "\\") for x in args]
                    if len(args) > 0:
                        if args[0] == "":
                            args[0] = " "

                    if fname == "new":
                        if len(args) < 3:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            background = " "
                            if len(args) > 3:
                                background = args[3]
                            if len(background) > 1:
                                result.log("background must be a single character!")
                            else:
                                if "." in args[0] or "(" in args[0] or ")" in args[0] or "," in args[0] or "[" in args[0] or "]" in args[0]:
                                    result.log("invalid object name, cannot contain the characters: .,()")
                                else:
                                    result.arts[args[0]] = Art(int(args[1]), int(args[2]))
                    elif fname == "copy":
                        if len(args) < 1:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            if "." in args[0] or "(" in args[0] or ")" in args[0] or "," in args[0] or "[" in args[
                                0] or "]" in args[0]:
                                result.log("invalid object name, cannot contain the characters: .,()")
                            else:
                                area = None
                                if len(args) > 1:
                                    area = [int(x) for x in args[2:]]
                                result.arts[args[0]] = art.copy(area)
                    elif fname == "rename":
                        if len(args) < 1:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            if "." in args[0] or "(" in args[0] or ")" in args[0] or "," in args[0] or "[" in args[
                                0] or "]" in args[0]:
                                result.log("invalid object name, cannot contain the characters: .,(), line: '" + line + "'")
                            else:
                                if args[0] != artname:
                                    if artname != "main":
                                        result.arts[args[0]] = art
                                        del result.arts[artname]
                                    else:
                                        result.log("cannot rename the main object: '" + line + "'")
                                else:
                                    result.log("cannot rename an object to its own name: '" + line + "'")
                    elif fname == "rect":
                        if len(args) < 5:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) > 5:
                                border = float(args[5])
                            art.rect(args[0], [int(args[1]), int(args[2]), int(args[3]), int(args[4])], border)
                    elif fname == "square":
                        if len(args) < 4:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) > 4:
                                border = float(args[4])
                            art.square(args[0], [int(args[1]), int(args[2])], int(args[3]), border)
                    elif fname == "circle":
                        if len(args) < 4:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) > 4:
                                border = float(args[4])
                            art.circle(args[0], [int(args[1]), int(args[2])], int(args[3]), border)
                    elif fname == "line":
                        if len(args) < 5:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) > 5:
                                border = float(args[5])
                            art.line(args[0], [int(args[1]), int(args[2])], [int(args[3]), int(args[4])], border)
                    elif fname == "triangle":
                        if len(args) < 7:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) > 7:
                                border = float(args[7])
                            art.triangle(args[0], [int(args[1]), int(args[2])], [int(args[3]), int(args[4])],
                                         [int(args[5]), int(args[6])], border)
                    elif fname == "quad":
                        if len(args) < 9:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) > 9:
                                border = float(args[7])
                            art.quad(args[0], [int(args[1]), int(args[2])], [int(args[3]), int(args[4])],
                                     [int(args[5]), int(args[6])], [int(args[7]), int(args[8])], border)
                    elif fname == "polygon":
                        if len(args) < 3:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            border = 0
                            if len(args) % 2 == 0:
                                border = float(args[-1])
                                sec = args[1:-1]
                            else:
                                sec = args[1:]
                            rps = [int(x) for x in sec]
                            ps = []
                            for i in range(0, len(rps), 2):
                                ps.append([rps[i], rps[i + 1]])
                            art.polygon(args[0], ps, border)
                    elif fname == "lines":
                        if len(args) < 3:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            rps = [int(x) for x in sec]
                            ps = []
                            for i in range(0, len(rps), 2):
                                ps.append([rps[i], rps[i + 1]])
                            art.lines(args[0], ps, float(args[-1]))
                    elif fname == "fill":
                        if len(args) < 1:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            art.fill(args[0])
                    elif fname == "set":
                        if len(args) < 3:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            art.set(int(args[1]), int(args[2]), args[0])
                    elif fname == "gradient":
                        if len(args) < 5:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            area = None
                            if len(args) > 5:
                                area = [int(x) for x in args[5:]]
                            art.gradient(args[0], [int(args[1]), int(args[2])], [int(args[3]), int(args[4])], area)
                    elif fname == "replace":
                        if len(args) < 2:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            bychar = False
                            if args[-1].startswith("bychar="):
                                bychar = bool(args[-1][7:])
                                args = args[:-1]
                            area = None
                            if len(args) > 2:
                                area = [int(x) for x in args[2:]]
                            art.replace(args[0], args[1], area, bychar=bychar)
                    elif fname == "swap":
                        if len(args) < 2:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            bychar = False
                            if args[-1].startswith("bychar="):
                                bychar = bool(args[-1][7:])
                                args = args[:-1]
                            area = None
                            if len(args) > 2:
                                area = [int(x) for x in args[2:]]
                            art.swap(args[0], args[1], area, bychar=bychar)
                    elif fname == "blit":
                        if len(args) < 1:
                            result.log("not enough arguments: '" + line + "'")
                        else:
                            if args[0] in result.arts:
                                if args[0] != artname:
                                    dest = [0, 0]
                                    area = None
                                    alpha = " "
                                    if args[-1].startswith("alpha="):
                                        alpha = args[-1][6:]
                                        args = args[:-1]
                                    if len(args) > 2:
                                        dest = [int(args[1]), int(args[2])]
                                    if len(args) > 3:
                                        area = [int(x) for x in args[3:]]
                                    art.blit(result.arts[args[0]], dest, area, alpha)
                                else:
                                    result.log("cannot blit an object on to itself: '" + line + "'")
                            else:
                                result.log("invalid object name: '" + line + "'")
                    elif fname == "log":
                        result.log(line[line.find("(")+1:line.rfind(")")])
                    else:
                        result.log("unrecognized function '" + fname + "' on line '" + line + "'")
                else:
                    result.log("invalid art object '" + artname + "' on line '" + line + "'")
            else:
                result.log("invalid syntax: '" + line + '"')
        except:
            result.log("error encountered on line '" + line + "'")
            traceback.print_exc()
    return result

