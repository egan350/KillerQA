KillerQA - Keyword Driven Test Automation Framework

Overview
--------
KillerQA is a lightweight Python-based keyword-driven test automation framework.

Tests are defined in a simple steps file and executed by a Python test runner.
The framework supports file operations, log validation, and API testing.

Features
--------
- Execute test steps from a text file
- Keyword-based test execution
- API testing with response validation
- JSON value verification
- Log file searching
- Optional parallel execution for independent tests
- Sequential execution support for dependent tests

Project Structure
-----------------
execute_steps.py   - Test execution engine
library.py         - Reusable test keywords/functions
steps.txt          - Test case definitions
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


Example Test Steps
------------------
Title: API Test [NoParallel]

get_api("https://jsonplaceholder.typicode.com/posts/1")
verify_status_code("200")
verify_json_value("userId", "1")


Notes
-----
Parallel execution is recommended for independent tests.
Tests with shared state or dependencies should use the [NoParallel]
tag to ensure steps execute in order.

License
-------
Personal project / learning framework.
