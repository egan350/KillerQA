import threading
import argparse
import library
import ast
import sys
import os
import re
import traceback


RANK = {
    "PASSED": 0,
    "SKIPPED": 1,
    "FAILED": 2,
    "ERROR": 3,
}


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


class StepResult:
    def __init__(self, step, status, reason=""):
        self.step = step
        self.status = status
        self.reason = reason


class TestResult:
    def __init__(self, title, status, reason="", warning=""):
        self.title = title
        self.status = status
        self.reason = reason
        self.warning = warning


def parse_title(title):
    tags = re.findall(r"\[([^\]]+)\]", title)

    skip_unless = []
    for tag in tags:
        if tag.startswith("SkipUnless "):
            skip_unless.append(tag[len("SkipUnless "):].strip())

    return {
        "title": title,
        "steps": [],
        "no_parallel": "NoParallel" in tags,
        "skip": "Skip" in tags,
        "must": "Must" in tags,
        "skip_unless": skip_unless,
    }


def skip_unless_reason(conditions):
    for condition in conditions:
        key, _, value = condition.partition("=")
        key = key.strip()
        value = value.strip()
        actual = os.environ.get(key)

        if actual != value:
            got = repr(actual) if actual is not None else "unset"
            return f"SkipUnless {key}={value} (got {got})"

    return None


def parse_step(step):
    step = step.strip()
    _, function_call = step.split(". ", 1)
    expr = ast.parse(function_call, mode="eval").body

    if not isinstance(expr, ast.Call):
        raise ValueError(f"Invalid step: {step}")

    function_name = expr.func.id
    args = [ast.literal_eval(arg) for arg in expr.args]
    kwargs = {
        kw.arg: ast.literal_eval(kw.value)
        for kw in expr.keywords
    }

    return function_name, args, kwargs


def is_check_step(step):
    try:
        function_name, _, _ = parse_step(step)
    except (ValueError, SyntaxError, AttributeError):
        return False

    return function_name.startswith("verify_") or function_name.startswith("search_log_")


def step_label(step):
    stripped = step.strip()
    number, _, rest = stripped.partition(". ")
    return number, rest


def execute_step(step):
    step = step.strip()

    if not step:
        return StepResult(step, "PASSED")

    try:
        function_name, args, kwargs = parse_step(step)
        getattr(library, function_name)(*args, **kwargs)
        return StepResult(step, "PASSED")
    except library.Skip as e:
        print(f"SKIPPED: {e}")
        return StepResult(step, "SKIPPED", str(e))
    except AssertionError as e:
        print(f"FAILED: {e}")
        return StepResult(step, "FAILED", str(e))
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return StepResult(step, "ERROR", f"{type(e).__name__}: {e}")


def run_steps(steps, parallel=False):
    if not steps:
        return []

    if parallel:
        results = [None] * len(steps)

        def worker(index, step):
            results[index] = execute_step(step)

        threads = []
        for index, step in enumerate(steps):
            thread = threading.Thread(target=worker, args=(index, step))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return results

    results = []
    blocked_reason = None

    for step in steps:
        number, call = step_label(step)

        if blocked_reason:
            results.append(StepResult(
                step,
                "SKIPPED",
                blocked_reason,
            ))
            print(f"SKIPPED step {number}: {blocked_reason}")
            continue

        result = execute_step(step)
        results.append(result)

        if result.status in ("FAILED", "ERROR", "SKIPPED"):
            blocked_reason = f"blocked by step {number} {call}"

    return results


def rollup_status(step_results):
    if not step_results:
        return "SKIPPED"

    return max(step_results, key=lambda result: RANK[result.status]).status


def test_reason(step_results, status):
    if status == "PASSED":
        return ""

    for result in step_results:
        if result.status == status:
            number, call = step_label(result.step)
            detail = result.reason
            if number:
                line = f"step {number}  {call}"
            else:
                line = call or result.step
            if detail:
                return f"{line}\n{detail}"
            return line

    return ""


def print_test_verdict(result):
    print(f"{result.status}  {result.title}")
    if result.reason:
        for line in result.reason.splitlines():
            print(f"         {line}")
    if result.warning:
        print(f"         warning: {result.warning}")


def print_summary(suite):
    counts = {"PASSED": 0, "FAILED": 0, "SKIPPED": 0, "ERROR": 0}
    for result in suite:
        counts[result.status] += 1

    total = len(suite)
    print()
    print("=" * 64)
    print(
        f"KillerQA  {total} tests  "
        f"{counts['PASSED']} passed  "
        f"{counts['FAILED']} failed  "
        f"{counts['SKIPPED']} skipped  "
        f"{counts['ERROR']} error"
    )
    print()

    for result in suite:
        print(f"{result.status:<8} {result.title}")
        if result.reason:
            for line in result.reason.splitlines():
                print(f"         {line}")
        if result.warning:
            print(f"         warning: {result.warning}")

    print("=" * 64)


def _run_tests(args):
    tests = []
    current_test = None

    with open(args.file, "r") as file:
        for line in file:
            line = line.strip()

            if line.startswith("Title:"):
                if current_test:
                    tests.append(current_test)

                title = line.replace("Title:", "").strip()
                current_test = parse_title(title)

            elif ". " in line and current_test:
                current_test["steps"].append(line)

        if current_test:
            tests.append(current_test)

    suite = []
    abort_reason = None

    for test in tests:
        print()
        print(f"Executing Test Case: {test['title']}")

        if abort_reason:
            result = TestResult(test["title"], "SKIPPED", abort_reason)
            suite.append(result)
            print_test_verdict(result)
            continue

        if test["skip"]:
            result = TestResult(test["title"], "SKIPPED", "[Skip] tag")
            suite.append(result)
            print_test_verdict(result)
            continue

        unless_reason = skip_unless_reason(test["skip_unless"])
        if unless_reason:
            result = TestResult(test["title"], "SKIPPED", unless_reason)
            suite.append(result)
            print_test_verdict(result)
            continue

        selected_steps = test["steps"]

        if args.steps:
            selected_numbers = set(map(int, args.steps.split(",")))
            selected_steps = [
                step
                for step in selected_steps
                if int(step.split(".")[0]) in selected_numbers
            ]

        if not selected_steps:
            result = TestResult(test["title"], "SKIPPED", "no matching steps")
            suite.append(result)
            print_test_verdict(result)
            continue

        step_results = run_steps(
            selected_steps,
            parallel=args.parallel and not test["no_parallel"],
        )

        status = rollup_status(step_results)
        reason = test_reason(step_results, status)
        warning = ""

        if status == "PASSED" and not any(is_check_step(step) for step in selected_steps):
            warning = "no assertions"

        result = TestResult(test["title"], status, reason, warning)
        suite.append(result)
        print_test_verdict(result)

        if test["must"] and status in ("FAILED", "ERROR"):
            abort_reason = f"aborted by [Must] test {test['title']}"

    print_summary(suite)

    return any(result.status in ("FAILED", "ERROR") for result in suite)


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

    failed = False
    try:
        failed = _run_tests(args)
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        results_file.close()

    sys.exit(1 if failed else 0)
