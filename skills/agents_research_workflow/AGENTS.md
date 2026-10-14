name: research-workflow
description: instruction for working in the research system

---------------------
Setup:
formalization - folder with skills for formalizing data into a form convenient for work
information - folder with additional information
storage - folder for storing results and the history of work with benchmarks
migrations - folder with db migrations
methods - folder with skills for circuit improvements
.configuration - configuration of the current work
MUTEX - WAIT WHILE THE PROCESS IS OCCUPIED BY ANOTHER AGENT, CHECK THE AGENTS SCHEDULE FOR THIS SKILL BEING BUSY EVERY MINUTE UNTIL IT IS FREE. AT THE START OF WORK ATOMICALLY OCCUPY THE TASK (ADD TO SCHEDULE THE TASK {agent_id; skill_name}). AT THE END OF THE TASK FREE THE TASK REGARDLESS OF THE RESULT (DELETE FROM SCHEDULE {agent_id; skill_name}) AFTER COMPLETION

---------------------
Input:
Ask the user whether to enable research workflow
* On - Set Root permissions in .configuration to [WRITE]
* Off - Set Root permissions in .configuration to [READ]

CAREFULLY LOOK AT Root IN configuration. ALL AGENTS HAVE ACCESS TO THIS WORKFLOW ONLY AS SPECIFIED THERE. IF Read IS SET, BLOCK ANY ACTIONS THAT CHANGE ANYTHING IN THE ENTIRE agents_research_workflow FOLDER, INCLUDING THOSE DESCRIBED FURTHER IN Input

Before starting work, check git status. If changed files are not committed now, suggest that the user do it

Before starting work, ask the user in which mode he wants to work:
* Manual - all questions are asked directly to the user
* Autonomous - all questions are asked to the agent and it also answers them (the AGENT becomes the user)
* Hybrid - all questions are asked to the agent, but if it thinks that the question is important and directly affects all further work, then the question is asked directly to the user
Update the set mode in Mode in .configuration

Ask which development process is selected:
* Single agent - HERE AND FURTHER MUTEXES ARE IGNORED
* Multi-agent system - warn the user that multi-agent development may be unstable due to race condition and that he accepts the risk. ONCE during work initialization, clear storage/workflow.db@agents_schedule and when creating an agent give it the sequential id under which it works and is marked in storage/workflow.db@agents_schedule when it takes MUTEX tasks

Update the set mode in System in .configuration

---------------------
Process:
If Root permission in .configuration is [READ]
    End here and use agents_research_workflow only for reading and methods running

Apply missing SQL migrations from migrations/
If it was not possible to determine exactly whether the benchmark being worked on is in Current benchmarks in the configuration, run formalization/INIT_BENCHMARK_CARD_SKILL.md
If the skill returned FAILED
    Finish the work indicating reason from the skill
Else
    Add info from the skill to Current benchmarks
