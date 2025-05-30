"""Subpackage defines plenty of methods useful for generation of small arithmetic
circuits by several methods."""

from .div_mod import add_div_mod, generate_div_mod
from .equality import add_equal, generate_equal
from .multiplication import (
    add_mul,
    add_mul_alter,
    add_mul_dadda,
    add_mul_karatsuba_with_efficient_sum,
    add_mul_pow2_m1,
    add_mul_wallace,
    generate_mul,
    MulMode,
)
from .sqrt import add_sqrt, generate_sqrt
from .square import add_square, add_square_pow2_m1, generate_square, SquareMode
from .subtraction import (
    add_sub2,
    add_sub3,
    add_sub_two_numbers,
    add_subtract_with_compare,
    generate_sub_two_numbers,
)
from .summation import (
    add_sum2,
    add_sum3,
    add_sum_n_bits,
    add_sum_n_bits_easy,
    add_sum_n_power_bits,
    add_sum_pow2_m1,
    add_sum_two_numbers,
    add_sum_two_numbers_with_shift,
    generate_sum_n_bits,
    generate_sum_weighted_bits_efficient,
    generate_sum_weighted_bits_naive,
)


__all__ = [
    # div_mod.py
    'generate_div_mod',
    'add_div_mod',
    # equality.py
    'add_equal',
    'generate_equal',
    # multiplication.py
    'add_mul',
    'add_mul_karatsuba_with_efficient_sum',
    'add_mul_alter',
    'add_mul_dadda',
    'add_mul_wallace',
    'add_mul_pow2_m1',
    'generate_mul',
    'MulMode',
    # sqrt.py
    'generate_sqrt',
    'add_sqrt',
    # square.py
    'add_square',
    'add_square_pow2_m1',
    'generate_square',
    'SquareMode',
    # subtraction.py
    'add_sub2',
    'add_sub3',
    'add_sub_two_numbers',
    'add_subtract_with_compare',
    'generate_sub_two_numbers',
    # summation.py
    'generate_sum_n_bits',
    'add_sum2',
    'add_sum3',
    'add_sum_n_bits',
    'add_sum_n_bits_easy',
    'add_sum_pow2_m1',
    'add_sum_two_numbers',
    'add_sum_two_numbers_with_shift',
    'add_sum_n_power_bits',
    'generate_sum_weighted_bits_efficient',
    "generate_sum_weighted_bits_naive",
]
