# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Every release requires a `## [X.Y.Z] - YYYY-MM-DD` section here: release
workflow uses it as GitHub Release notes (see "Release" in `README_DEV.md`).

## [Unreleased]

### Added

- Log-depth circuit generation over AIG basis: sum (#133), subtraction (#136),
  multiplication (#138), square (#143) and square root (#144).
- Preparata-Muller (1971) decomposition for synthesis (#131).
- Metaheuristics for circuit minimization (#125).
- Python 3.14 wheels.

### Changed

- Updated `ABC` version, fixed `abc_wrapper` module (#135).
- Updated `python-sat` version (#128) and unpinned it (#145).
- Updated `pybind11` to 3.0.4.
- Wheels are built and published to PyPI by the `Release` GitHub Actions workflow.

## [1.0.0] - 2026-02-08

First release with prebuilt wheels on PyPI (CPython 3.9-3.13, manylinux,
musllinux, macOS x86_64 and arm64).
