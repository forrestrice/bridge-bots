from functools import partial
from typing import Callable, Optional

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


_FIRST_TRICK_VALUE = {
    BiddingSuit.NO_TRUMP: 40,
    BiddingSuit.SPADES: 30,
    BiddingSuit.HEARTS: 30,
    BiddingSuit.DIAMONDS: 20,
    BiddingSuit.CLUBS: 20,
}
_TRICK_VALUE = {
    BiddingSuit.NO_TRUMP: 30,
    BiddingSuit.SPADES: 30,
    BiddingSuit.HEARTS: 30,
    BiddingSuit.DIAMONDS: 20,
    BiddingSuit.CLUBS: 20,
}


def _calculate_bonus(
    level: int, suit: BiddingSuit, doubled: int, vulnerable: bool, contracted_trick_score: int, overtricks: int
) -> int:
    score = 0
    # Slam bonus
    if level == 7:
        score += 1500 if vulnerable else 1000
    elif level == 6:
        score += 750 if vulnerable else 500

    # Game / part-score
    if contracted_trick_score >= 100:
        score += 500 if vulnerable else 300
    else:
        score += 50

    # Overtricks
    if doubled == 0:
        score += overtricks * _TRICK_VALUE[suit]
    elif doubled == 1:
        score += 50
        score += overtricks * (200 if vulnerable else 100)
    elif doubled == 2:
        score += 100
        score += overtricks * (400 if vulnerable else 200)
    return score


_FIRST_UNDERTRICK_VALUE = {
    (False, 0): 50,
    (False, 1): 100,
    (False, 2): 200,
    (True, 0): 100,
    (True, 1): 200,
    (True, 2): 400,
}

_SECOND_THIRD_UNDERTRICK_VALUE = {
    (False, 0): 50,
    (False, 1): 200,
    (False, 2): 400,
    (True, 0): 100,
    (True, 1): 300,
    (True, 2): 600,
}

_SUBSEQUENT_UNDERTRICK_VALUE = {
    (False, 0): 50,
    (False, 1): 300,
    (False, 2): 600,
    (True, 0): 100,
    (True, 1): 300,
    (True, 2): 600,
}


def calculate_score(level: int, suit: Optional[BiddingSuit], doubled: int, tricks: int, vulnerable: bool) -> int:
    """
    :param level: contract level (4 in 4S)
    :param suit: contract bidding suit
    :param doubled: 0=undoubled, 1=doubled, 2=redoubled
    :param tricks: tricks taken by declarer
    :param vulnerable: vulnerability of declarer
    :return: declarer's score
    """
    if level == 0:  # Pass Out
        return 0
    scoring_tricks = tricks - 6
    if scoring_tricks >= level:
        double_multiplier = pow(2, doubled)
        first_trick_score = _FIRST_TRICK_VALUE[suit] * double_multiplier
        subsequent_tricks_score = _TRICK_VALUE[suit] * double_multiplier * (level - 1)
        bonus = _calculate_bonus(
            level, suit, doubled, vulnerable, first_trick_score + subsequent_tricks_score, scoring_tricks - level
        )
        return first_trick_score + subsequent_tricks_score + bonus
    else:
        undertricks = level + 6 - tricks
        score_key = (vulnerable, doubled)
        score = 0
        for i in range(0, undertricks):
            score_dict = (
                _FIRST_UNDERTRICK_VALUE
                if i == 0
                else _SECOND_THIRD_UNDERTRICK_VALUE
                if 0 < i < 3
                else _SUBSEQUENT_UNDERTRICK_VALUE
            )
            score -= score_dict[score_key]
        return score
