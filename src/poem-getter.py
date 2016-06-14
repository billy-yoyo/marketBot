import requests, json
from bs4 import BeautifulSoup

poems = {}

print("loading poems...")
for p in range(20):
    response = requests.get("http://www.poemhunter.com/p/m/l.asp?a=0&l=top500&order=title&p=" + str(p+1))
    soup = BeautifulSoup(response.content, 'html.parser')

    titles = [x for x in soup.find_all("td") if "title" in x.attrs["class"]]
    for title in titles:
        tempsoup = title.find("a")
        if tempsoup is not None and "title" in tempsoup.attrs and "href" in tempsoup.attrs:
            url = "http://www.poemhunter.com" + tempsoup["href"]
            poem_title = tempsoup["title"].replace(" ", "+")
            if len(poem_title) == 0:
                poem_title = "+"
            while poem_title in poems:
                poem_title += "+"
            print(poem_title + " : " + url)
            response = requests.get(url)
            psoup = BeautifulSoup(response.content, 'html.parser')
            raw_poem_lines = psoup.find("div", class_="KonaBody").find("p").contents
            poem_lines = []
            for line in raw_poem_lines:
                line = str(line)
                if line != "<br/>" and line is not None:
                    eline = line.replace("\r", "")
                    eline = eline.replace("\n", "")
                    eline = eline.replace("<br/>", "")
                    while len(eline) > 0 and eline[0] == " ":
                        eline = eline[1:]
                    while len(eline) > 0 and eline[-1] == " ":
                        eline = eline[:-1]
                    if len(eline) > 0:
                        poem_lines.append(eline)
            poems[poem_title] = poem_lines
    print("loaded page " + str(p+1) + " of 20")

print("dumping poems to file...")

f = open("poems.txt", "w")
json.dump(poems, f)
if not f.closed:
    f.close()

print("finished.")
