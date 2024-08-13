"""Subpackage defines plenty of methods useful for generation of small arithmetic
circuits by several methods."""

from .div_mod import add_div_mod
from .equality import add_equal
from .multiplication import (
    add_mul,
    add_mul_alter,
    add_mul_dadda,
    add_mul_karatsuba,
    add_mul_pow2_m1,
    add_mul_wallace,
)
from .sqrt import add_sqrt
from .square import add_square, add_square_pow2_m1
from .subtraction import (
    add_sub2,
    add_sub3,
    add_sub_two_numbers,
    add_subtract_with_compare,
)
from .summation import (
    add_sum2,
    add_sum3,
    add_sum_n_bits,
    add_sum_n_bits_easy,
    add_sum_pow2_m1,
    add_sum_two_numbers,
    add_sum_two_numbers_with_shift,
)


__all__ = [
    # div_mod.py
    'add_div_mod',
    # equality.py
    'add_equal',
    # multiplication.py
    'add_mul',
    'add_mul_karatsuba',
    'add_mul_alter',
    'add_mul_dadda',
    'add_mul_wallace',
    'add_mul_pow2_m1',
    # sqrt.py
    'add_sqrt',
    # square.py
    'add_square',
    'add_square_pow2_m1',
    # subtraction.py
    'add_sub2',
    'add_sub3',
    'add_sub_two_numbers',
    'add_subtract_with_compare',
    # summation.py
    'add_sum2',
    'add_sum3',
    'add_sum_n_bits',
    'add_sum_n_bits_easy',
    'add_sum_pow2_m1',
    'add_sum_two_numbers',
    'add_sum_two_numbers_with_shift',
]
