# Changelog

## [0.0.5] - 2023-03-03
### Changed
- Fixed a bug in the practice tool that caused headers to be written to the csv in append mode

## [0.0.4] - 2022-11-11
### Changed
- Added all csv report output fields to the deal practice tool

## [0.0.3] - 2022-4-03
### Added
- New tool `compare_contracts_csv_report` for comparing sets of contracts' performance.
- New tool `practice_deals` for creating sets of practice deals as a LIN file with accompanying links to see how it was played by others. 
- New fields in csv output. `deal_hash` uniquely identifies a deal, `trump_fit` and `trump_hcp` provide information about trump strength.
### Changed
- Refactored much of the logic in `csv_report` to be shared with `compare_contracts_csv_report`

## [0.0.2] - 2022-2-10
### Added
- Scores for declarer and defender. HCP and Shape for declarer, dummy, lho, and rho.
### Changed
- CSV writer now ignores extra keys. This means output columns can now be reduced by commenting out lines in the `_CSV_HEADERS` list.

## [0.0.1] - 2022-1-29
### Added
- First release of bridgebots_tools. Created csv_report which can covert files or directories of LIN and PBN records into a CSV report. See the [Readme](README.md) for details.