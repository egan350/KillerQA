import threading
import argparse
import library
import shlex
import ast
import sys


class Tee:
    def __init__(self, *streams):
        self.streams = streams
        self._lock = threading.Lock()

    def write(self, data):
        with self._lock:
            for stream in self.streams:
                stream.write(data)
                stream.flush()

    def flush(self):
        with self._lock:
            for stream in self.streams:
                stream.flush()


def execute_step(step):
    step = step.strip()

    if not step:
        return

    # Remove step number (e.g. "1. ")
    _, function_call = step.split(". ", 1)

    # Parse the function call
    expr = ast.parse(function_call, mode="eval").body

    if not isinstance(expr, ast.Call):
        raise ValueError(f"Invalid step: {step}")

    function_name = expr.func.id

    # Positional arguments
    args = [
        ast.literal_eval(arg)
        for arg in expr.args
    ]

    # Keyword arguments
    kwargs = {
        kw.arg: ast.literal_eval(kw.value)
        for kw in expr.keywords
    }

    # Execute
    getattr(library, function_name)(*args, **kwargs)


def run_steps(steps, parallel=False):
    threads = []

    for step in steps:

        if parallel:
            # Run in parallel using threads
            thread = threading.Thread(
                target=execute_step,
                args=(step,)
            )

            threads.append(thread)
            thread.start()

        else:
            execute_step(step)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


def _run_tests(args):
    # Parse test cases
    tests = []
    current_test = None


    with open(args.file, "r") as file:

        for line in file:

            line = line.strip()

            if line.startswith("Title:"):

                # Save previous test case
                if current_test:
                    tests.append(current_test)


                title = line.replace("Title:", "").strip()

                current_test = {
                    "title": title,
                    "steps": [],
                    "no_parallel": "[NoParallel]" in title
                }


            elif ". " in line and current_test:

                current_test["steps"].append(line)


        # Add final test case
        if current_test:
            tests.append(current_test)



    # Execute test cases
    for test in tests:

        print()
        print(f"Executing Test Case: {test['title']}")

        selected_steps = test["steps"]


        # Filter steps if requested
        if args.steps:

            selected_numbers = set(
                map(int, args.steps.split(","))
            )

            selected_steps = [
                step
                for step in selected_steps
                if int(step.split(".")[0]) in selected_numbers
            ]


        run_steps(
            selected_steps,
            parallel=args.parallel and not test["no_parallel"]
        )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Execute test cases from a steps file"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run steps in parallel"
    )

    parser.add_argument(
        "--steps",
        type=str,
        help="Specify step numbers to run (example: --steps 1,2)"
    )

    parser.add_argument(
        "file",
        type=str,
        help="Path to the steps file"
    )


    args = parser.parse_args()

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    results_file = open("results.txt", "w", encoding="utf-8")
    tee = Tee(original_stdout, results_file)
    sys.stdout = tee
    sys.stderr = tee

    try:
        _run_tests(args)
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        results_file.close()