# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Every release requires a `## [X.Y.Z] - YYYY-MM-DD` section here: release
workflow uses it as GitHub Release notes (see "Release" in `README_DEV.md`).

## [Unreleased]

## [1.1.0rc1] - 2026-10-13

### Added

#### Synthesis

- Added depth-oriented synthesis of Boolean functions by Preparata and Muller (1971):
  `generate_circuit_pm1971` (#131).
- Added logarithmic-depth adders (Kogge-Stone, Brent-Kung, Krapchenko) and a
  logarithmic-depth sum of weighted bits: `add_sum_two_numbers_log_depth`,
  `add_sum_two_numbers_log_depth_brent_kung`,
  `add_sum_two_numbers_log_depth_krapchenko`, `add_sum_n_weighted_bits_log_depth`,
  `mdfa_sum_weighted_bits` (#133).
- Added logarithmic-depth subtraction: `add_sub_two_numbers_log_depth` and
  `add_subtract_with_compare_log_depth` (#136).
- Added new multiplication algorithms: logarithmic-depth, Karatsuba variants, signed
  Dadda and Wallace, and multiplication by a constant (`add_mul_log_depth_sum`,
  `add_simple_karatsuba`, `add_dadda_karatsuba`, `add_smul_dadda`, `add_smul_wallace`,
  `add_mul_constant`) (#138).
- Added Dadda squaring: `SquareMode.DADDA` and `add_square_dadda` (#143).
- Added division with remainder by a constant: `add_div_mod_by_const` (#146).
- Added `zero_div` option to `add_div_mod` and `generate_div_mod` (division by zero
  returns the dividend instead of zero) and support of a divisor shorter than the
  dividend (#146).
- Added number reconstruction from residues by the Chinese remainder theorem:
  `add_crt`, `add_crt_calc` and `modular_inverse` (#147).
- Added AIG basis (`basis="AIG"`) for summation, subtraction, multiplication,
  squaring, square root, division with remainder and CRT (#133, #136, #138, #143,
  #144, #146, #147). Karatsuba and Alter multiplication and default squaring still
  support only XAIG.

#### Core, SAT and integrations

- Added `Circuit.get_depth`. By default negations and identity gates (`NOT`, `LNOT`,
  `RNOT`, `IFF`, `LIFF`, `RIFF`) do not add to depth; pass `exclusion_list=()` to
  count every gate (#133, #125).
- Added `check_circuits_equivalence` which checks equivalence of two circuits with
  a SAT solver (#125).
- Added `cirbo.integrations.abc` with `abc_transform` and `ABCCommand` for composing
  ABC commands with `>>` (#125).

#### Circuit minimization

- Added metaheuristic search for circuit minimization: `optimize`, search
  strategies, custom mutations and Pareto frontiers of circuit size and depth (#125).
- Added mutations based on ABC command scripts: `ABCHeavyMutation` (#125).
- Added IWLS 2026 `ex215` benchmark circuits to the package data (about 300 KiB)
  (#125).

### Changed

- Changed `MulMode.DADDA` and `MulMode.WALLACE` to use a logarithmic-depth final
  adder by default: circuits have more gates, but much lower depth. Pass
  `sum_func=add_sum_two_numbers` to get the previous circuits (#138).
- Made `add_sum_n_bits` circuits shallower and `add_sum_n_weighted_bits` circuits (and so default and Karatsuba
  multiplication) slightly smaller and shallower (#133).
  Size / depth of 32x32 multipliers:

| `generate_mul(32, 32, type=...)` | Before     | After      |
|----------------------------------|------------|------------|
| `MulMode.DADDA`                  | 5952 / 185 | 6760 / 37  |
| `MulMode.WALLACE`                | 6207 / 127 | 6906 / 38  |
| `MulMode.DEFAULT`                | 5503 / 710 | 5487 / 655 |

- Moved `abc_transform` from `extensions.abc_wrapper.src.abc` to
  `cirbo.integrations.abc` (#125).
- Stopped silently ignoring errors of ABC commands (#135).
- Parser progress is now logged at `DEBUG` instead of `INFO` level (#125).
- Raised minimal `python-sat` version to `1.9.dev7` and updated bundled ABC (#128, #135).

### Fixed

- Fixed wrong result of `add_subtract_with_compare` with `big_endian=True` and
  operands of different lengths (#136).
- Fixed `add_sum_two_numbers_with_shift` failing when the shift is larger than the
  first operand (#138).
- Fixed `add_sum_n_weighted_bits_naive` ignoring `basis="AIG"` passed as a string (#133).
- Fixed truncation of circuits larger than 4 MiB in the ABC wrapper (#135).

### Build and release

- Added wheels for Python 3.14.
- Added `Release` GitHub Actions workflow which publishes wheels to TestPyPI and PyPI
  and creates a GitHub Release.

## [1.0.0] - 2026-02-08

First release with prebuilt wheels on PyPI (CPython 3.9-3.13, manylinux, musllinux,
macOS x86_64 and arm64).
