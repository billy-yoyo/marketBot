import math
import time

class Colour:
    @staticmethod
    def _clamp(v):
        return min(255, max(0, v))

    def __init__(self, r, g, b, a):
       self.r = r
       self.g = g
       self.b = b
       self.a = a

    def clamp(self):
        self.r = Colour._clamp(int(self.r))
        self.g = Colour._clamp(int(self.g))
        self.b = Colour._clamp(int(self.b))
        self.a = Colour._clamp(int(self.a))
        return self

    def __mul__(self, other):
        return Colour(self.r * other, self.g * other, self.b * other, self.a * other)

    def __add__(self, other):
        return Colour(self.r + other.r, self.g + other.g, self.b + other.b, self.a + other.a)

    def __sub__(self, other):
        return Colour(self.r - other.r, self.g - other.g, self.b - other.b, self.a - other.a)

    def get_bytes(self):
        return bytearray([self.r, self.g, self.b, self.a])

    def __str__(self):
        return "(" + str(self.r) + "," + str(self.g) + "," + str(self.b) + "," + str(self.a) + ")"


class InvalidGrid(Exception):
    pass


class Kernal:
    def __init__(self, grid, coef=0):
        self.height = len(grid)
        if self.height > 0:
            self.width = len(grid[0])
            for row in grid:
                if len(row) != self.width:
                    raise InvalidGrid
            if self.height % 2 == 1 and self.width % 2 == 1:
                self.grid = grid
                self.cx = math.ceil(self.width / 2)
                self.cy = math.ceil(self.height / 2)
                self.coef = coef
                if coef == 0:
                    for i in range(self.height):
                        for j in range(self.width):
                            self.coef += grid[i][j]
                if self.coef == 0:
                    self.coef = 1
                else:
                    self.coef = 1 / self.coef
                self.changes = []
                for i in range(self.height):
                    for j in range(self.width):
                        if grid[i][j] != 0:
                            self.changes.append([i - self.cx, j - self.cy, grid[i][j] * self.coef])
            else:
                raise InvalidGrid
        else:
            raise InvalidGrid

    def eval(self, grid, cx, cy):
        total = Colour(0, 0, 0, 0)
        for change in self.changes:
            total += grid[change[1]+cy][change[0]+cx] * change[2]
        result = total.clamp()
        return result

    def apply(self, grid, doprint):
        width, height = len(grid[0]), len(grid)
        new_grid = [[grid[j][i] for i in range(width)] for j in range(height)]

        for y in range(self.cy, height-self.cy):
            for x in range(self.cx, width-self.cx):
                new_grid[y][x] = self.eval(grid, x, y)
            if doprint and y % 50 == 0:
                print("done " + str(y) + " rows out of " + str(height))

        return new_grid


def run(file_in, file_out, ker, doprint=True):

    file = open(file_in, "rb")
    data = file.read()
    file.close()

    def geti(bytes):
        return int.from_bytes(bytes, byteorder="little")

    header = {
        "type": data[0:2],
        "size": geti(data[2:6]),
        "offset": geti(data[10:14])
    }


    bminfo = {
        "info-size": geti(data[14:18]),
        "width": geti(data[18:22]),
        "height": geti(data[22:26]),
        "bits": geti(data[28:30]),
        "gridsize": 0
    }
    bminfo["rowsize"] = math.floor(((bminfo["bits"] * bminfo["width"]) + 31) / 32 ) * 4


    def load():
        grid = [ [None] * bminfo["width"] for x in range(bminfo["height"])]

        row = 0
        index = header["offset"]
        d_i = 1
        while row < bminfo["height"]:
            for x in range(bminfo["width"]):
                grid[row][x] = Colour(data[index], data[index+1], data[index+2], data[index+3])
                index += 4
            if doprint and index - header["offset"] > 1000000 * d_i:
                d_i += 1
                print("loaded " + str(index-header["offset"]) + " bytes")
            row += 1
        bminfo["gridsize"] = index
        return grid


    def save(filename):
        grid_data = [0] * (bminfo["gridsize"] - header["offset"])
        curi = 0
        cd_i = 1
        for row in grid:
            for c in row:
                grid_data[curi] = c.r
                grid_data[curi+1] = c.g
                grid_data[curi+2] = c.b
                grid_data[curi+3] = c.a
                curi += 4
            if doprint and curi > 1000000*cd_i:
                cd_i += 1
                print("saved " + str(curi) + " bytes")
        save_data = data[:header["offset"]] + bytearray(grid_data) + data[(bminfo["gridsize"]+1):]
        file = open(filename, "wb")
        file.write(save_data)
        file.close()


    def get(x, y):
        if 0 <= x < bminfo["width"] and 0 <= y < bminfo["height"]:
            return grid[y][x]
        return None

    if doprint: print("header info:")
    if doprint: print(header)
    if doprint: print(bminfo)
    if doprint: print("")
    if doprint: print("loading...")
    start = time.time()
    grid = load()
    end = time.time()
    if doprint: print("loaded, took " + str(end-start) + " seconds")
    if doprint: print("")
    if doprint: print("editing...")

    if doprint: print("coef = " + str(ker.coef))
    start = time.time()
    grid = ker.apply(grid, doprint)
    end = time.time()
    if doprint: print("done, took " + str(end-start) + " seconds")
    if doprint: print("")
    if doprint: print("saving...")
    start = time.time()
    save(file_out)
    end = time.time()
    if doprint: print("saved, took " + str(end-start) + " seconds")

#template = Kernal([
#    [ 0, 0, 0, 0, 0],
#    [ 0, 0, 0, 0, 0],
#    [ 0, 0, 0, 0, 0],
#    [ 0, 0, 0, 0, 0],
#    [ 0, 0, 0, 0, 0]
#], coef=0)
#ker = Kernal([
#    [1 , 0 , 2],
#    [0 , -5, 0],
#    [2 , 0 , 1]
#], coef=0)
#ker = Kernal([
#    [0, 0, 0, 2, 0],
#    [0, 0, 1, 0, 3],
#    [0, 0, -20, 0, 0],
#    [0, 0, 6, 0, 4],
#    [0, 0, 0, 5, 0]
#], coef=0)
#ker = Kernal([
#    [-1, 0, 3, 0,-1],
#    [ 0,-1, 0,-1, 0],
#    [ 3, 0,-3, 0, 3],
#    [ 0,-1, 0,-1, 0],
#    [-1, 0, 3, 0,-1]
#], coef=0)
#ker = Kernal([
#    [-3,-1, 5,-1,-3],
#    [-1, 0, 0, 0,-1],
#    [ 5, 0, 0, 0, 5],
#    [-1, 0, 0, 0,-1],
#    [-3,-1, 5,-1,-3]
#], coef=0)
#ker = Kernal([
#    [ 1, 0,-1],
#    [ 0, 0, 0],
#    [-1, 0, 1]
#], coef=0)
