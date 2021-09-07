# Changelog

## [0.0.6] - 2021-09-06
### Changed
- BoardRecord and BoardRecord schema have better handling of missing commentary or bidding metadata

## [0.0.5] - 2021-09-06
### Changed
- BoardRecord now represents player names as a Direction:String dictionary

## [0.0.4] - 2021-08-29
### Added
- Support for parsing and creating LIN files
- Marshmallow schemas for marshalling to/from JSON
- Support for parsing PBN commentary, notes, and alerts
- Readme with examples

### Changed

- \_\_repr\_\_ for most Bridgebots Core classes updated to be more explanatory and/or less verbose