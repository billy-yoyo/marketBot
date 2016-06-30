
card_order = "23456789TJQKA"
card_amt = 13

n_scores = [0] * 10
suit_order = "HDSC"

players = [None, None]
scores = [0, 0]


def resolve(player1, player2):
    for player in range(2):
        cards = player1
        if player == 1:
            cards = player2
        print(cards)
        n_suits = [0, 0, 0, 0]
        n_cards = [0] * 13
        highest = 0
        for index in range(len(cards)):
            card = cards[index]
            ci, si = card_order.find(card[0]), suit_order.find(card[1])
            score = 0
            if ci > highest:
                highest = ci
            if n_cards[ci] == 1:
                if scores[player] == 1: # two pairs
                    score = 2
                else: # one pair
                    score = 1
            elif n_cards[ci] == 2: # three of a kind
                score = 3
            elif n_cards[ci] == 3: # four of a kind
                score = 7

            if score > scores[player]:
                scores[player] = score

            n_cards[ci] += 1
            n_suits[si] += 1

        has_straight = False
        if "11111" in "".join([str(x) for x in n_cards]): # straight
            has_straight = True
            if scores[player] < 4:
                scores[player] = 4

        print(n_suits)
        #print(n_cards)
        if max(*n_suits) == 5: # flush
            if has_straight and highest == len(card_order)-1: # royal flush
                scores[player] = 9
            elif scores[player] < 4: # normal flush
                scores[player] = 5
            elif scores[player] == 4: # straight flush:
                scores[player] = 8

        if scores[player] < 7 and max(*n_cards) == 3 and max(x for x in n_cards if x != 3) == 2: # full house
            scores[player] = 6

        players[player] = n_cards

        n_scores[scores[player]] += 1

    # conclude winner
    if scores[0] == scores[1]: # tie, look for highest card
        index = 12
        if scores[0] == 1: # look for highest pair
            if players[0].index(2) > players[1].index(2):
                return [1, scores[0], scores[1]]
        elif scores[0] == 2: # look for highest pair
            p11 = players[0].index(2)
            p12 = players[0].index(2, p11+1)
            p21 = players[1].index(2)
            p22 = players[1].index(2, p21+1)
            if p22 == p12: # highest pairs are the same
                if p11 > p21: # player 1's lowest pair is higher
                    return [1, scores[0], scores[1]]
            elif p12 > p22: # player 1's highest pair is higher
                return [1, scores[0], scores[1]]
        elif scores[0] == 3: # look for triplet
            if players[0].index(3) > players[1].index(3):
                return [1, scores[0], scores[1]]
        elif scores[0] == 4: # look for quad
            if players[0].index(4) > players[1].index(4):
                return [1, scores[0], scores[1]]
        else:
            while players[0][index] == players[1][index] and index >= 0:
                index -= 1
            if index >= 0 and players[0][index] == 1: # player 1 has highest card, so they win
                return [1, scores[0], scores[1]]
    elif scores[0] > scores[1]: # player 1 wins
        return [1, scores[0], scores[1]]
    return [2, scores[0], scores[1]]

#print(resolve("QH 8C JH 3D 8H 2H TH".split(" "), "KD 5C JH 3D 8H 2H TH".split(" ")))