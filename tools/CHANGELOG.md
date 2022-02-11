# Changelog

## [0.0.2] - 2022-2-10
### Added
- Scores for declarer and defender. HCP and Shape for declarer, dummy, lho, and rho.
### Changed
- CSV writer now ignores extra keys. This means output columns can now be reduced by commenting out lines in the `_CSV_HEADERS` list.

## [0.0.1] - 2022-1-29
### Added
- First release of bridgebots_tools. Created csv_report which can covert files or directories of LIN and PBN records into a CSV report. See the [Readme](README.md) for details.