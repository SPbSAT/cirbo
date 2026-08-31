name: init-benchmark-research-card
description: create a benchmark card that allows the history of work with the benchmark to be tracked

---------------------
Setup:
storage/workflow.db@benchmarks_library - database about benchmarks
storage/workflow.db@agents_schedule - agents schedule
storage/benchmarks_artifacts/{id}/benchmark_formats - folder with different extensions of the benchmark
formalization/INIT_BENCHMARK_WORKING_FORMAT_SKILL.md - skill for formalizing the benchmark format and saving it, returns CREATED/FAILED
db header - {id,function,format,description,storage_link,created_at} from storage/workflow.db@benchmarks_library
is MUTEX

---------------------
Input data:
* id(int)
* description(string)
* file(string): link to file

---------------------
Output data:
* id(int)
* status(string): FOUND/CREATED/FAILED
* info(string)
* reason(string)

---------------------
Algorithm:
If 'id' is not NULL, check presence in storage/workflow.db@benchmarks_library
    If exists
        Return [id: id; status: FOUND; info: db header; reason: NULL]
    Else
        Return [id: NULL; status: FAILED; reason: There is no such id among benchmarks]
Else
    If 'file' is not NULL
        If the file is in storage/workflow.db@benchmarks_library
            Return [id: id from db; FOUND; info: db header; reason: NULL]
        Else
            Find the list of 5 benchmarks most suitable by the name of 'file' and save their header
    Else
        If 'description' is not NULL:
            Find the list of 5 benchmarks most suitable by 'description' and save their header
    Go from the most likely to the least likely and ask the user whether this is the benchmark
    If yes
        Return [id: id from header; status: FOUND; info: db header; reason: NULL]
    If no
        If this was the fifth benchmark
            Say that the benchmark is not present, ask whether to create a new one
            If yes:
                Do everything in 'Creation'
            Else
                Return [id: NULL; status: FAILED; reason: failed to find a suitable benchmark, try to describe it in more detail or specify id/send the file]

---------------------
Creation:
Get the next sequential id from the benchmark (DO NOT CREATE AN OBJECT)
* storage
Run the skill for formalizing the benchmark format and saving it, passing id
If FAIL
    Return [id; NULL; status: FAILED; reason: {Reason from the skill}]
Else
    * db
    Add a new object to storage/workflow.db@benchmarks_library with the obtained id and the current time in created_at
    Write storage/benchmarks_artifacts/id/benchmark_formats to storage_link
    If 'description' is not NULL
        Fill description from storage/workflow.db@benchmarks_library with the current 'description'
    Else
        Request a benchmark description with the words "Please describe this benchmark so that it is easier to find in the future"
        Write the user's answer to description of storage/workflow.db@benchmarks_library
    Return [id; created id; status: CREATED; info: db header; reason: NULL]
