KillerQA - Keyword Driven Test Automation Framework

Overview
--------
KillerQA is a lightweight Python-based keyword-driven test automation framework. **This framework is still in development and in beta. Use with caution.**

Tests are defined in a simple steps file and executed by a Python test runner.
The framework supports file operations, log validation, and API testing.

You do not mark tests as passed or failed yourself. The runner infers
PASSED, FAILED, SKIPPED, or ERROR from what each keyword does and from
optional tags on the test title.


Features
--------
- Execute test steps from a text file
- Keyword-based test execution
- API testing with response validation
- JSON value verification
- Log file searching (no match is a failure)
- Optional parallel execution for independent tests
- Sequential execution support for dependent tests
- Inferred test verdicts: PASSED, FAILED, SKIPPED, ERROR
- Suite summary in the console and in results.txt
- Exit code 1 when any test FAILED or ERROR'd (skips do not fail the run)


Project Structure
-----------------
execute_steps.py   - Test execution engine
library.py         - Reusable test keywords/functions
steps.txt          - Test case definitions
results.txt        - Full output of the latest run (overwritten each time)
requirements.txt   - Python dependencies


Installation
------------
Install dependencies:

    pip install -r requirements.txt


Running Tests
-------------
Run tests sequentially:

    python execute_steps.py steps.txt


Run tests in parallel:

    python execute_steps.py steps.txt --parallel

    --parallel parameter in the KillerQA framework allows you to run multiple steps in parallel, which can significantly speed up the execution time for independent tests. Here's a more detailed explanation:

    Parallel Execution
    Parallel Execution: When you use the --parallel parameter with the execute_steps.py script, it allows the test engine to run steps in parallel. This means that if you have multiple independent tests or steps that can be executed concurrently, they will be run at the same time, rather than one after another.
    Independent Tests: For tests that do not depend on each other and can be executed in parallel, using --parallel can greatly reduce the overall test execution time. This is because the test engine can handle multiple test cases at the same time, rather than waiting for one test to complete before starting the next.
    Shared State: If tests share state (e.g., variables, headers, or saved variables), you should avoid using --parallel for those tests, as it can lead to race conditions or other unexpected behavior.

Run only some step numbers (applied to every test):

    python execute_steps.py --steps 1,2 steps.txt


Test Verdicts
-------------
Status is inferred. You do not add pass_test or fail_test keywords.

PASSED
    Every step finished. verify_* and search_log_* count as checks.
    If a test only has actions (for example open_file / write_to_file)
    it still PASSES, with a warning: no assertions.

FAILED
    A check raised AssertionError. Examples: wrong HTTP status, wrong
    JSON field, or search_log_today_date finding no matching lines.

SKIPPED
    The test was not meant to run, or a precondition failed:
    - Title tag [Skip]
    - Title tag [SkipUnless key=value] when the environment variable
      does not match (example: [SkipUnless env=staging])
    - require_reachable(...) when the host cannot be contacted
    - GET/POST returned 502, 503, or 504 (remaining steps are skipped)

ERROR
    Anything else: missing log file, network crash, invalid step, or
    a keyword exception that is not an assertion.

A test's status is the worst step: ERROR > FAILED > SKIPPED > PASSED.

Inside a test, the first FAIL, ERROR, or SKIP stops later steps and
marks them skipped (blocked by step N). Other tests in the file still
run, unless the failed test has [Must] on its title.


Title Tags
----------
Tags go on the Title line. You can combine them.

[NoParallel]
    Run this test's steps in order even if --parallel is set.
    Use this for API tests that share response/header state.

[Skip]
    Do not run the test. Always reported as SKIPPED.

[SkipUnless env=staging]
    Run only when environment variable env equals staging.
    The name before = is the variable name, so [SkipUnless CI=1]
    checks CI. If it does not match, the test is SKIPPED.

[Must]
    If this test FAILED or ERROR'd, skip the rest of the suite
    with reason aborted by [Must] test ...

[Parallel_Tests]
Force the test to run in parallel. [Parallel_Tests]
    Run this test's steps in parallel, ignoring the --parallel flag.
    Use this for tests that can be executed in parallel without shared state.
    When you run the script with the command python execute_steps.py --parallel steps.txt, the --parallel flag will override the [Parallel_Tests] tag for all tests, but it should still respect the [Parallel_Tests] tag for Example Test Case2 because it is not explicitly set to [NoParallel].


Gates and checks
----------------
Actions (get_api, post_api, write_to_file, set_header, ...) do work.
A crash in an action is ERROR, not FAILED.

Checks (verify_* and search_log_*) assert product truth.
A mismatch is FAILED.

Gates (require_*) are preconditions. If they are not met, the test
is SKIPPED instead of going red.

Skip the test when an API host is down:

    1. require_reachable("https://dummyjson.com")
    2. get_api("https://dummyjson.com/...")
    3. verify_status_code("200")


Example Test Steps
------------------
Title: API Test [NoParallel]

1. get_api("https://jsonplaceholder.typicode.com/posts/1")
2. verify_status_code("200")
3. verify_json_value("userId", "1")


Title: Manual skip example [Skip]

1. open_file("file1.txt")


Title: Staging only skip example [SkipUnless env=staging]

1. open_file("file1.txt")

Run the staging example with:

    env=staging python execute_steps.py steps.txt


Results
-------
Every run writes the same output you see in the terminal to results.txt
(overwritten each time). After the step log, a summary is printed:

    KillerQA  7 tests  4 passed  1 failed  2 skipped  0 error

    PASSED   Example Test Case
             warning: no assertions
    FAILED   Example Test Case3
             step 1  search_log_today_date(...)
             No lines matching 'ERROR' and date '...' in ./sample_log.log
    SKIPPED  Manual skip example [Skip]
             [Skip] tag

The process exit code is 0 only when nothing FAILED or ERROR'd.


Notes
-----
Parallel execution is recommended for independent tests.
Tests with shared state or dependencies should use the [NoParallel]
tag to ensure steps execute in order.

--parallel fans out steps inside a test, not whole tests. API cases
should stay [NoParallel] because they share the last response, headers,
and saved variables.


License
-------
Personal project / learning framework.