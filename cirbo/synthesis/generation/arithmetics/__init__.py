"""Subpackage defines plenty of methods useful for generation of small arithmetic
circuits by several methods."""

from .div_mod import (
    add_div_mod,
    add_div_predefined,
    add_mod_predefined,
    generate_div_mod,
)
from .equality import add_equal, generate_equal
from .multiplication import (
    add_mul,
    add_mul_alter,
    add_mul_constant,
    add_mul_dadda,
    add_mul_karatsuba,
    add_mul_karatsuba_with_efficient_sum,
    add_mul_log_depth_sum,
    add_mul_pow2_m1,
    add_mul_wallace,
    add_smul_dadda,
    add_smul_wallace,
    generate_mul,
    MulMode,
)
from .sqrt import add_sqrt, generate_sqrt
from .square import (
    add_square,
    add_square_dadda,
    add_square_pow2_m1,
    generate_square,
    SquareMode,
)
from .subtraction import (
    add_sub2,
    add_sub3,
    add_sub_two_numbers,
    add_sub_two_numbers_log_depth,
    add_subtract_with_compare,
    add_subtract_with_compare_log_depth,
    generate_sub_two_numbers,
)
from .summation import (
    add_sum2,
    add_sum3,
    add_sum_n_bits,
    add_sum_n_bits_easy,
    add_sum_n_weighted_bits,
    add_sum_n_weighted_bits_log_depth,
    add_sum_n_weighted_bits_naive,
    add_sum_pow2_m1,
    add_sum_two_numbers,
    add_sum_two_numbers_log_depth,
    add_sum_two_numbers_log_depth_brent_kung,
    add_sum_two_numbers_log_depth_krapchenko,
    add_sum_two_numbers_with_shift,
    generate_sum_n_bits,
    generate_sum_weighted_bits_efficient,
    generate_sum_weighted_bits_naive,
    mdfa_sum_weighted_bits,
)


__all__ = [
    # div_mod.py
    'generate_div_mod',
    'add_div_mod',
    'add_div_predefined',
    'add_mod_predefined',
    # equality.py
    'add_equal',
    'generate_equal',
    # multiplication.py
    'add_mul',
    'add_mul_karatsuba_with_efficient_sum',
    'add_mul_karatsuba',
    'add_mul_log_depth_sum',
    'add_mul_alter',
    'add_mul_dadda',
    'add_mul_wallace',
    'add_mul_pow2_m1',
    'add_smul_dadda',
    'add_smul_wallace',
    'add_mul_constant',
    'generate_mul',
    'MulMode',
    # sqrt.py
    'generate_sqrt',
    'add_sqrt',
    # square.py
    'add_square',
    'add_square_pow2_m1',
    'add_square_dadda',
    'generate_square',
    'SquareMode',
    # subtraction.py
    'add_sub2',
    'add_sub3',
    'add_sub_two_numbers',
    'add_sub_two_numbers_log_depth',
    'add_subtract_with_compare',
    'add_subtract_with_compare_log_depth',
    'generate_sub_two_numbers',
    # summation.py
    'generate_sum_n_bits',
    'add_sum2',
    'add_sum3',
    'add_sum_n_bits',
    'add_sum_n_bits_easy',
    'add_sum_pow2_m1',
    'add_sum_two_numbers',
    'add_sum_two_numbers_log_depth',
    'add_sum_two_numbers_log_depth_brent_kung',
    'add_sum_two_numbers_log_depth_krapchenko',
    'add_sum_two_numbers_with_shift',
    'add_sum_n_weighted_bits',
    'add_sum_n_weighted_bits_log_depth',
    'add_sum_n_weighted_bits_naive',
    'generate_sum_weighted_bits_efficient',
    "generate_sum_weighted_bits_naive",
    'mdfa_sum_weighted_bits',
]
