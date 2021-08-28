from functools import partial
from typing import Callable

from bridgebots.deal import Card
from bridgebots.deal_enums import BiddingSuit, Suit


def _evaluate_card(trump_suit: BiddingSuit, suit_led: Suit, card: Card) -> int:
    """
    Score a card on its ability to win a trick given the trump suit and the suit that was led to the trick
    :return: the card's score
    """
    score = card.rank.value[0]
    if card.suit == trump_suit.to_suit():
        score += 100
    elif card.suit != suit_led:
        score -= 100
    return score


def trick_evaluator(trump_suit: BiddingSuit, suit_led: Suit) -> Callable:
    """
    :return: a partial which takes a Card as an argument and returns an ordering score within the context of a trick in
    progress
    """
    return partial(_evaluate_card, trump_suit, suit_led)
