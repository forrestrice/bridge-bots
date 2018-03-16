
class PlayerHand:
    def __init__(self, clubs, diamonds, hearts, spades):
        self.clubs = clubs
        self.diamonds = diamonds
        self.hearts = hearts
        self.spades =spades

    def __str__(self):
        return "Clubs:{}\nDiamonds:{}\nHearts:{}\nSpades:{}".format(self.clubs, self.diamonds, self.hearts, self.spades)


class Hand:
    def __init__(self, dealer, ns_vulnerable, ew_vulnerable, north_hand, east_hand, south_hand, west_hand):
        self.dealer = dealer
        self.ns_vulnerable = ns_vulnerable
        self.ew_vulnerable =ew_vulnerable
        self.north_hand = north_hand
        self.east_hand = east_hand
        self.south_hand = south_hand
        self.west_hand = west_hand

    def __str__(self):
        header = "{} Deals\nns_vuln:{}\new_vuln:{}\n".format(self.dealer, self.ns_vulnerable, self.ew_vulnerable)
        hands = "North:\n{}\nEast:\n{}\nSouth:\n{}\nWest:\n{}".format(self.north_hand, self.east_hand, self.west_hand, self.south_hand)
        return header + hands
