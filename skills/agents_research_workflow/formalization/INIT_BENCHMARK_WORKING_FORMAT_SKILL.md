name: init-benchmark-working-format.md
description: Processing the benchmark in a format suitable for further improvements

---------------------
Setup:
storage/benchmarks_artifacts/{id}/benchmark_formats - folder with different extensions of the benchmark
storage/workflow.db@agents_schedule - agents schedule
information/file_extension_formats.csv - list of formats allowed for work
is MUTEX

---------------------
Input data:
* id(int)
* file(string): link to file

---------------------
Output data:
* status(string): CREATED/FAILED
* reason(string)

---------------------
Algorithm
If 'file' is NULL
    Request 'file' from the user
If 'file' is not found on the device
    Return [status: FAILED; reason: Failed to detect file {file}]
If extension of 'file' is in the list of formats
    Check whether the file is correct by format
    If not
        Return [status: FAILED; reason: The contents of file {file} do not match the format]
    Save a copy of 'file' to storage/benchmarks_artifacts/{id}/benchmark_formats
    Return [status: CREATED; reason: NULL]
Else
    Tell the user that such a format is not in the list and ask whether he wants to add it
    If yes
        Ask the user for the most detailed description of the format - how inputs -> output is encoded and in what bit-width order
        Add the format to the list of allowed formats with the description from the user
        Save a copy of 'file' to storage/benchmarks_artifacts/{id}/benchmark_formats
        Return [status: CREATED; reason: NULL]
    Else
        Return [status: FAILED; reason: Unsupported format for skills to work]
        
