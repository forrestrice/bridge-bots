# Bridgebots Core
This package contains the core components of the bridgebots library. The main focus is representing Contract Bridge concepts such as suits, ranks, cards, deals, bids, alerts, and scores. Data processing utilities such as a PBN parser are also included.

### Installation
`pip install bridgebots`

### Requirements
This package will attempt to maintain an extremely minimal set of external dependencies. As of this writing there are zero.


## Building, Testing, and Contributing
Bridgebots uses [Poetry](https://python-poetry.org/) to manage building, testing, and publishing.

### Build
`poetry install` to install dependencies.

`poetry build` to build a wheel file.

### Test
`poetry run pytest` to run all unit tests.

### Contribute
Feel free to create issues or fork the repository and submit a pull-request. This is a hobby project, so they may not be addressed immediately.

### Style
Format all Python code using [Black](https://github.com/psf/black) with `--line-length 120`.

Use type-hints wherever possible.

Any added functionality should include unit tests.

## Examples
### Deal
Construct a deal manually
```python
hands = {
    Direction.NORTH: PlayerHand.from_string_lists(
        ["9", "8", "6", "4"], ["K", "Q", "7", "6", "3"], ["A", "K"], ["7", "3"]
    ),
    Direction.SOUTH: PlayerHand.from_string_lists(
        ["A", "K", "Q", "5"], ["A", "9", "4"], ["J", "5", "2"], ["K", "8", "4"]
    ),
    Direction.EAST: PlayerHand.from_string_lists(
        ["2"], ["J", "10", "8", "5", "2"], ["Q", "8", "7", "4", "3"], ["A", "10"]
    ),
    Direction.WEST: PlayerHand.from_string_lists(
        ["J", "10", "7", "3"], [], ["10", "9", "6"], ["Q", "J", "9", "6", "5", "2"]
    ),
}
deal = Deal(dealer=Direction.EAST, ns_vulnerable=True, ew_vulnerable=False, hands=hands)
```

Construct a deal from a PBN style string
```python
deal = deal_utils.from_pbn_deal("N", "EW", "W:Q8652.875.943.AT J97.AJ2.AKQ2.Q87 AK.QT943.87.9632 T43.K6.JT65.KJ54")
```

Interact with a Bridgebots deal
```pycon
>>> len(deal.hands[Direction.NORTH].suits[Suit.SPADES])
3

>>> deal.dealer, deal.ns_vulnerable, deal.ew_vulnerable
(NORTH, False, True)

>>> card = Card(Suit.DIAMONDS, Rank.KING)
>>> card in deal.player_cards[Direction.NORTH], card in deal.player_cards[Direction.SOUTH]
(True, False)

>>> card in deal.hands[Direction.NORTH].cards
True
```

### PBN
Parse a Version 1.0 PBN file into Bridgebots Deal and BoardRecord objects.
```pycon
>>> pbn_path = Path("bridgebots/tests/sample.pbn")
>>> results: List[Tuple[Deal, BoardRecord]] = parse_pbn(pbn_path)
```
