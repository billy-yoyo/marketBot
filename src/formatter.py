
f1 = open("words.txt", "r")
f2 = open("words_new.txt", "w")
for line in f1:
    add = None
    if " " in line:
        add = line[:line.index(" ")]
        if "." in add or len(add) < 4 or "-" in add or "," in add:
            add = None
    if add is not None:
        f2.write(add + ";")
f1.close()
f2.close()