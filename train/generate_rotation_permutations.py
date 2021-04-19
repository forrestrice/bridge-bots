import itertools
from typing import List

from bridge import Card
from bridge import Direction, Rank, Suit


class RotationPermutation:
    def __init__(self, suits: List[Suit]):
        self.suits = suits
        self.sorted_deck = [Card(suit, rank) for suit in suits for rank in Rank]
        self.suit_ranks = {suit: suits.index(suit) for suit in suits}

    def sort_hand(self, cards: List[Card]):
        return sorted(cards, key=lambda card: (self.suit_ranks[card.suit], card.rank))

    def build_deck_mask(self, cards: List[Card]):
        deck_data = []
        sorted_hand = self.sort_hand(cards)
        sorted_hand_index = 0
        for card in self.sorted_deck:
            if sorted_hand_index < len(sorted_hand) and card == sorted_hand[sorted_hand_index]:
                sorted_hand_index += 1
                deck_data.append(1)
            else:
                deck_data.append(0)
        return deck_data


all_suit_permutations = [
    RotationPermutation(list(suit_permutation)) for suit_permutation in itertools.permutations([suit for suit in Suit])
]

clockwise_directions = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
all_rotations = [[clockwise_directions[(i + j) % 4] for j in range(0, 4)] for i in range(0, 4)]

RotationPermutation.all_suit_permutations = all_suit_permutations
RotationPermutation.all_rotations = all_rotations
