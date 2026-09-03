Preparata--Muller 1971 synthesis
================================

``generate_circuit_pm1971`` synthesizes a fully defined Boolean function
without invoking a SAT solver. It is suited to applications that prefer a
depth-oriented, deterministic construction and can accept the potentially large
circuit produced from a truth table.

For a function of ``n`` inputs of a practical size (up to ``2**8 + 8`` inputs),
the construction's worst-case logic depth is ``n + 1``. Larger functions use a
fallback construction for which this bound is not guaranteed. Simpler functions can
produce shallower circuits. This depth convention treats input negation as a
complemented edge and counts the longest path of two-input ``AND`` and ``OR`` gates,
which is the convention used for AIG depth.

Input and result
----------------

Pass any object implementing Cirbo's ``Function`` protocol, such as ``TruthTable``,
``PyFunction``, or ``Circuit``. The function must be fully defined: models containing
don't-care values must be defined before synthesis.

The result is a ``Circuit`` with:

* the same number and ordering of inputs;
* the same number and ordering of outputs;
* the same value for every input assignment;
* two-input ``AND`` and ``OR`` gates, with ``NOT`` gates applied to inputs; and
* constant gates only when the source function has no inputs.

The result does not retain input or output names from the source object. Position is
the interface: source input zero corresponds to generated input zero, and the same
rule applies to outputs.

Usage
-----

.. code-block:: python

   from cirbo.core import TruthTable
   from cirbo.synthesis.generation import generate_circuit_pm1971

   parity = TruthTable([[False, True, True, False]])
   circuit = generate_circuit_pm1971(parity)

   assert circuit.evaluate([False, False]) == [False]
   assert circuit.evaluate([False, True]) == [True]
   assert circuit.evaluate([True, False]) == [True]
   assert circuit.evaluate([True, True]) == [False]

Multi-output functions use one row per output, following the standard Cirbo truth-table
layout:

.. code-block:: python

   function = TruthTable([
       [False, True, False, True],
       [False, False, True, True],
   ])
   circuit = generate_circuit_pm1971(function)

   assert circuit.evaluate([True, False]) == [False, True]
   assert circuit.evaluate([False, True]) == [True, False]

Tutorial
--------

The complete tutorial module below synthesizes parity and displays the resulting
circuit with Graphviz.

.. literalinclude:: ../tutorial/synthesizing_preparata_muller.py
   :language: python

Choosing this generator
-----------------------

This method is a direct construction and therefore has predictable behavior without
solver selection, timeouts, or a circuit database. It targets depth rather than gate
count. Use SAT-based synthesis when minimizing a small circuit is the primary goal,
and use arithmetic or logical generators when the required function already has a
specialized Cirbo generator.

Both the input truth table and the possible output circuit grow exponentially with the
number of inputs. The method is consequently most practical when a complete truth table
already exists and the input count is moderate.

Implementation details
----------------------

The implementation represents small truth tables as integer bit masks and enumerates a
per-synthesis database of expressions by exact gate depth. For small cofactors it first
searches this database for an exact expression.

For larger functions, it chooses a tail size ``s`` satisfying ``n <= 2**s + s`` and
expands the function over assignments to the other variables. Each resulting tail
cofactor is synthesized exactly when possible and otherwise via a balanced DNF or CNF.
Tails of up to eight variables are handled directly. For larger inputs, one additional
recursive split is attempted; beyond ``2**8 + 8`` inputs the implementation falls back
to a balanced normal form, so the ``n + 1`` depth guarantee no longer applies.

Reference
---------

The construction is based on F. P. Preparata and D. E. Muller, "On the Delay Required
to Realize Boolean Functions," *IEEE Transactions on Computers*, C-20(4), 459--461,
1971. A public technical-report version is available from the `University of Illinois
IDEALS repository <https://www.ideals.illinois.edu/items/100224>`_.
