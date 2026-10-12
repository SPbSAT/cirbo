# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Every release requires a `## [X.Y.Z] - YYYY-MM-DD` section here: release
workflow uses it as GitHub Release notes (see "Release" in `README_DEV.md`).

## [Unreleased]

### Added

#### Synthesis

- `generate_circuit_pm1971`: solver-free synthesis by Preparata and Muller (1971),
  depth at most `n + 1` for up to `2**8 + 8` inputs (#131).
- Log-depth summation (#133): `add_sum_two_numbers_log_depth` (Kogge-Stone),
  `..._brent_kung`, `..._krapchenko`, `add_sum_n_weighted_bits_log_depth`,
  `mdfa_sum_weighted_bits` (XAIG only), helper `xor_two_bits`.
- Log-depth subtraction: `add_sub_two_numbers_log_depth`,
  `add_subtract_with_compare_log_depth` (#136).
- Multiplication (#138): `add_mul_log_depth_sum`, `add_simple_karatsuba`,
  `add_dadda_karatsuba`, signed `add_smul_dadda` / `add_smul_wallace`,
  `add_mul_constant`; functions with a final adder accept `sum_func`.
- `SquareMode.DADDA` / `add_square_dadda` (#143).
- AIG basis (`basis="AIG"`) for summation, subtraction, multiplication (`DEFAULT`, `DADDA`, `WALLACE`, `POW2_M1`),
  squaring (`POW2_M1`, `DADDA`) and
  square root (#133, #136, #138, #143, #144). Other combinations (`MulMode.KARATSUBA`, `MulMode.ALTER`,
  `SquareMode.DEFAULT`) raise `BadBasisError`.

#### Core, SAT and integrations

- `Circuit.get_depth(exclusion_list=...)`. Only effective operands count (`LNOT`/`LIFF` use the first one, `RNOT`/`RIFF`
  the second), constants have
  depth 0, and by default `NOT`, `LNOT`, `RNOT`, `IFF`, `LIFF`, `RIFF` do not add
  to depth; pass `exclusion_list=()` to count every gate (#133, #125).
- `cirbo.sat.check_circuits_equivalence` (#125).
- `cirbo.integrations.abc`: `abc_transform`, `ABCCommand` (composable with `>>`),
  `ABCUnavailableError` (#125).

#### Circuit minimization

- Metaheuristic search in `cirbo.minimization`: `optimize`, `SearchConfig`,
  `MultiStartRandomWalk`, custom mutations (`CircuitMutation`,
  `TransformerMutation`) and Pareto frontiers (`InstanceFrontier`,
  `ParetoFrontier`) (#125).
- `ABCHeavyMutation` and `ABC_HEAVY_COMMANDS`: mutations based on ABC scripts (#125).
- IWLS 2026 `ex215` benchmarks (MIT) in `cirbo/data/ex215_frontier` (~300 KiB)
  and tutorials for the features above (#125).

### Changed

- **`MulMode.DADDA` / `MulMode.WALLACE` use a log-depth final adder by default**:
  more gates, much lower depth (32x32 size/depth: Dadda 5952/185 -> 6760/37,
  Wallace 6207/127 -> 6906/38). Pass `sum_func=add_sum_two_numbers` for the
  previous ripple-carry adder (#138).
- `add_sum_n_bits` circuits are shallower at the same size (128 bits: depth
  134 -> 128); `add_sum_n_weighted_bits`, and so `MulMode.DEFAULT` and Karatsuba,
  are slightly smaller and shallower (32x32 default: 5503 -> 5487 gates, depth
  710 -> 655) (#133).
- `abc_transform` moved from `extensions.abc_wrapper.src.abc` to
  `cirbo.integrations.abc`; raises `ABCUnavailableError` if ABC is not built (#125).
- `abc_wrapper.run_abc_commands_c` raises `RuntimeError` when the network cannot
  be read or an ABC command fails (errors were ignored before) (#135).
- Parser progress is logged at `DEBUG` instead of `INFO`; `Circuit.save_to_file`
  and `resolve_default_data_path` accept `str` and path-like objects (#125).
- Dependencies: `python-sat >= 1.9.dev7` (was `>= 1.8.dev26`) (#128, #145),
  updated `ABC` (#135) and `pybind11` 3.0.4.

### Fixed

- `add_subtract_with_compare` gave wrong results with `big_endian=True` and
  operands of different lengths (#136).
- `add_sum_two_numbers_with_shift` raised `CircuitValidationError` when `shift`
  was larger than the first operand (#138).
- `add_sum_n_weighted_bits_naive` ignored `basis="AIG"` passed as a string and
  generated XAIG gates (#133).
- `abc_wrapper`: circuits larger than the internal 4 MiB buffer were truncated,
  buffers were leaked, and ABC's `-fno-exceptions` leaked into the wrapper (#135).
- `python-sat` was pinned to an exact version by mistake (#145).

### Build and release

- Python 3.14 wheels (pybind11 >= 3.0).
- `build.py` passes `Python_EXECUTABLE`: pybind11 >= 3.0 ignores
  `PYTHON_EXECUTABLE` and could pick another interpreter from `PATH`.
- Wheel builds reuse ABC objects between Python versions (ccache) and no longer
  download `googletest`.
- Release is done by the `Release` GitHub Actions workflow: TestPyPI, PyPI and
  GitHub Release instead of manual upload.

## [1.0.0] - 2026-02-08

First release with prebuilt wheels on PyPI (CPython 3.9-3.13, manylinux,
musllinux, macOS x86_64 and arm64).
