name: piecewise-residual-circuit-synthesis
description: the method is used to obtain smaller area by partitioning the input value domain into groups around a pivot with subsequent application of the residual from it

---------------------
Setup:
information/file_extension_formats.csv - list of formats allowed for work

---------------------
Input data:
benchmark(string)
function(string)
expected_area(int)
attempts(int)
folder_to_save(string)

---------------------
Output data:
circuit(string)
status: FAILED; COMPLETED
reason(string)
area(int)
delta(int)

---------------------
Variables:
characteristic(list<string>)

---------------------
Notation:
F(input) -> reference output of the benchmark for this input

---------------------
Algorithm:
If 'benchmark' is NULL 
	Return [circuit: NULL; status: FAILED; reason: Benchmark is not specified; area: NULL; delta: NULL]
If extension of 'benchmark' is not in the list of formats allowed for work
	Return [circuit: NULL; status: FAILED; reason: Unsupported format; area: NULL; delta: NULL]
CAREFULLY READ THE DESCRIPTION OF THE EXTENSION OF 'benchmark' IN THE LIST OF ALLOWED FORMATS
If 'function' is not NULL
	Add to characteristic the function properties from STORAGE (will be added later, for now consider it the internet) related to symmetry and function growth
Look at the truth table and, taking into account characteristic(list<string>), partition the input value domain into G_i = (set-of-inputs_i; pivot_i; residual_i(input)), where set-of-inputs cover all input data and are pairwise disjoint, and residual(input) is the correction with which reconstructor obtains F(input) from pivot_i; pivot is the structure from which residual is computed in the group so that 

total_area = sum_i(G_i<area>) + area(selector) + sum_j(reconstructor_j<area>) + area(final_mux)

is as small as possible where G_i<area> = area(pivot_i) + area(residual_i), selector(x) determines which group x belongs to - it must be common for all groups (even if internally it can separate them), reconstructor_j(pivot, residual) receives pivot_i, residual_i(input), selector(input), and input, and assembles the exact output = F(input), selector must be single for the whole input value domain, and by default reconstructor should be searched for as common (j = 1), final_mux selects the output of one of reconstructor_j if there are several reconstructors, and its area is 0 if reconstructor is common. This structure can be multi-level. That is, when we have a set of pivot_i, it is worth trying to apply the same partitioning into groups to it as well.
After constructing the partition, synthesize the full circuit, save it to {folder_to_save}/{skill-name}_{unique_id}_{delay}_{area}.bench and validate it through CHECKER (will be added later, for now consider it -cec/bitwise match) and obtain its (area; delay) through VALIDATOR (will be added later, for now consider it through ABC)
If CHECKER is false or VALIDATOR said that the circuit is invalid
	Find the reason and rebuild
If area <= expected_area
	Return [circuit: {folder_to_save}/{skill-name}_{unique_id}_{delay}_{area}.bench; status: COMPLETED; reason: Requested area has been reached; area: area; delta; area - expected_area]
Else
	attempt -= 1
	If attempt is less than 0
		Exit
	Check that the construction matches expectations and has no bugs and try to rebuild the groups using another combination from characteristic
Take the circuit with the minimum size for which CHECKER is true and VALIDATOR says that the circuit is correct
If there is no such circuit
	Return [circuit: NULL; status: FAILED; reason: Failed to build a correct circuit; area: NULL; delta: NULL]
Return [circuit: path to circuit with the smallest size; status: COMPLETED; reason: Attempts are exhausted; area: min_area; delta: min_area - expected_area]
