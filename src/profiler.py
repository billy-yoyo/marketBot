
#
#    THIS FUNCTIONALITY IS DISABLED UNTIL I CAN GET PYGAME TO WORK
#        I'm struggling to get pygame to install correctly on my server so until then I've had to disable the profile command.
#        I will try and install pygame again at some point but I'm going to prioritise other things first.
#


import os
import pygame
import math
from os import listdir
from os.path import isfile, join

pygame.init()

def get_avatar_fn(user, worth):
    avatar = user.avatar
    avatar_url = user.avatar_url
    if avatar is None:
        avatar = user.default_avatar
        avatar_url = user.default_avatar_url
    return [user.id + "__" + avatar + ".png", avatar_url, user.id + "__" + avatar +  "__" + str(worth) + ".png"]


def download_avatar(bot, avt):
    filename = "avatars/" + avt[0]
    if not os.path.exists(filename):
        resp = yield from bot.client.session.get(avt[1])
        data = yield from resp.read()
        f = open(filename, "wb")
        f.write(data)
        f.close()


def get_avater_image(avt):
    filename = "avatars/" + avt[0]
    if os.path.exists(filename):
        return pygame.image.load(filename)
    return None


def has_card(avt):
    return os.path.exists("cards/" + avt[2])


def get_n_str(n):
    prefix = ""
    if n == 0:
        return "0"
    if n < 0:
        prefix = "-"
        n = -n
    if n < 1000:
        return prefix + str(n)
    else:
        suffs = "kmbTGP?"
        text = str(n)[:3]
        rest = str(n)[3:]
        point = len(rest) % 3
        if point == 1:
            text = text[0] + "." + text[1:]
        if point == 2:
            text = text[:2] + "." + text[2]
        return prefix + text + suffs[min(len(suffs)-1, math.ceil(len(rest)/3)-1)]


#def setup_card(bot, user):
#    if not os.path.exists("avatars/"):
#        os.makedirs("avatars/")
#    if not os.path.exists("cards/"):
#        os.makedirs("cards/")
#    avt = get_avatar_fn(user)
#    if not os.path.exists("avatars/" + avt[0]):
#        yield from download_avatar(bot, avt)


def get_card(bot, user):
    worth = bot.market.get_worth(user.id)
    avt = get_avatar_fn(user, worth)
    if not has_card(avt):
        yield from download_avatar(bot, avt)
        surf = get_avater_image(avt)
        if surf is not None:
            surf = pygame.transform.smoothscale(surf, [64, 64])
            font_large = pygame.font.Font("card_img/LeelawUI.ttf", 18)
            font_small = pygame.font.Font("card_img/LeelawUI.ttf", 14)
            #font_surf = font.render("hello world", 2, [0,0,0])
            # name : [120, 40]
            # factory : [ 139, 97 ]
            # inventory : [ 217, 97 ]
            # money : [ 389, 97 ]
            tester = bot.imgs["test_profile"]
            final = pygame.Surface(tester.get_size())
            final.blit(surf, [42, 42])
            final.blit(tester, [0, 0])
            final.blit(font_large.render(user.name, 4, [50, 50, 50]), [120, 40])

            final.blit(font_small.render(get_n_str(bot.market.get_factory_amount(user.id)), 4, [50, 50, 50]), [136, 94])
            final.blit(font_small.render(get_n_str(bot.market.get_inventory_amount(user.id)), 4, [50, 50, 50]), [210, 94])
            final.blit(font_small.render(get_n_str(bot.market.get_money(user.id)), 4, [50, 50, 50]), [287, 94])
            #final.blit(font_surf, [10, 10])
            pygame.image.save(final, "cards/" + avt[2])
            return "cards/" + avt[2]
        else:
            return None
    return "cards/" + avt[2]


def cleanup(bot):
    n = 0
    onlyfiles = [f for f in listdir("cards/") if isfile(join("cards/", f))]
    for filename in onlyfiles:
        if filename.endswith(".png"):
            spl = filename[:-4].split("__")
            if bot.market.get_worth(spl[0]) != int(spl[2]):
                os.remove("cards/" + filename)
                n += 1
    return n
