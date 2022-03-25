# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [2022.3.0]

### Changed
- A factor of -1 was incorporated into the `_set_position` method to correct

### Added
- NDInterp daemon to do N-dimensional interpolation of complicated offsets

## [2022.2.0]

## Added
- wright-fuyu-linear daemon for the customized FUYU linear stage
- 'Y' home feature for arduino INO for homing towards upper limits


## [2021.4.0]

## Added
- test script for viewing wright-ingaas spectra is now included in repo
- wright-aerotech daemon for the customized aerotech translation stage

## Changed
- `wright-ingaas` now uses `has-mapping` trait to map spectral axis
- `wright-ingaas` daemon can query spectrometer for position
- update is-sensor trait

## [2021.1.0]

### Added
- conda-forge as installation source

### Fixed
- rerendered avprs based on recent traits change
- avoid byte order problems in the InGaAs array

### Changed
- use new parent classes from upstream core

## [2020.10.1]

### Added
- CI upload to PyPI

### Fixed
- Metadata URLs

## [2020.10.0]

### Added
- initial release

[Unreleased]: https://github.com/wright-group/yaqd-wright/compare/v2022.3.0...HEAD
[2022.3.0]: https://github.com/wright-group/yaqd-wright/compare/v2022.2.0...v2022.3.0
[2022.2.0]: https://github.com/wright-group/yaqd-wright/compare/v2021.4.0...v2022.2.0
[2021.4.0]: https://github.com/wright-group/yaqd-wright/compare/v2021.1.0...v2021.4.0
[2021.1.0]: https://github.com/wright-group/yaqd-wright/compare/v2020.10.1...v2021.1.0
[2020.10.1]: https://github.com/wright-group/yaqd-wright/compare/v2020.10.0...v2020.10.1
[2020.10.0]: https://github.com/wright-group/yaqd-wright/releases/tag/v2020.10.0
