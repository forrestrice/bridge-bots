# Changelog

## [0.0.9] - 2022-1-16
### Added
- `parse_pbn` now handles files which used shared deals for multiple board records.
- `parse_pbn` now handles files that end with a single newline.

## [0.0.8] - 2022-1-15
### Added
- `Direction.offset` Can be used to get the Direction an arbitrary number of steps away.
### Changed
- Bridgebots now supports python 3.7! Several small backwards compatibility changes were made.
- Fixed several edge case bugs for LIN parsing. Improved error messages.
- `BiddingSuit.NO_TRUMP.abbreviation()` now returns `NT` by default. `N` can be returned by setting the flag `verbose_no_trump=False`.

## [0.0.7] - 2021-11-27
### Added
- Utility method `calculate_score` to compute the scoring of a hand.
- `Contract` dataclass for programmatic interaction with contracts [Issue #6](https://github.com/forrestrice/bridge-bots/issues/6).
### Changed
- Methods which take each suit as an argument specify arguments in descending suit order (Spades, Hearts, Diamonds, Clubs) to match common convention. [Issue #7](https://github.com/forrestrice/bridge-bots/issues/7).
- Consolidated all submodule imports under `__init__.py`. Users can now simply `import bridgebots`. [Issue #8](https://github.com/forrestrice/bridge-bots/issues/8).
- All Record classes (BoardRecord, DealRecord, etc) now implemented as [dataclasses](https://docs.python.org/3/library/dataclasses.html). [Issue #9](https://github.com/forrestrice/bridge-bots/issues/9).


## [0.0.6] - 2021-09-06
### Changed
- BoardRecord and BoardRecord schema have better handling of missing commentary or bidding metadata.

## [0.0.5] - 2021-09-06
### Changed
- BoardRecord now represents player names as a Direction:String dictionary.

## [0.0.4] - 2021-08-29
### Added
- Support for parsing and creating LIN files.
- Marshmallow schemas for marshalling to/from JSON.
- Support for parsing PBN commentary, notes, and alerts.
- Readme with examples.

### Changed

- \_\_repr\_\_ for most Bridgebots Core classes updated to be more explanatory and/or less verbose.