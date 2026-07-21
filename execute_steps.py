import threading
import argparse
from library import *

def execute_step(step):
    # Parse and execute a single step
    function_call = step.strip()
    function_name, arguments = function_call.split("(", 1)
    function_name = function_name.split('. ')[1].strip()  # Remove step number
    arguments = arguments.rstrip(")\n").split(", ")
    arguments = [arg.strip('"') for arg in arguments]

    # Execute function
    globals()[function_name](*arguments)


def run_steps(steps, parallel=False):
    threads = []
    for step in steps:
        if parallel:
            # Run in parallel using threads
            thread = threading.Thread(target=execute_step, args=(step,))
            threads.append(thread)
            thread.start()
        else:
            execute_step(step)

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute steps from a file, including an optional title.")
    parser.add_argument("--parallel", action="store_true", help="Run steps in parallel")
    parser.add_argument("--steps", type=str, help="Specify steps to run, separated by commas (e.g., --steps 1,2)")
    parser.add_argument("file", type=str, help="Path to the steps file")

    args = parser.parse_args()

    title = None
    steps = []

    # Read and parse the file
    with open(args.file, 'r') as file:
        for line in file:
            if line.startswith("Title:"):
                title = line.strip().split("Title:",1)[1].strip()
                no_parallel = "[NoParallel]" in title
                clean_title = (title.replace("[NoParallel]", "").strip()
                    )
            elif line.strip().isdigit() or ". " in line:
                steps.append(line.strip())

    # Print the title if it exists
    if title:
        print(f"Executing Test Case: {title}")

    # Filter steps if specific ones are requested
    if args.steps:
        selected_steps_numbers = set(map(int, args.steps.split(',')))
        selected_steps = [step for step in steps if int(step.split('.')[0]) in selected_steps_numbers]
    else:
        selected_steps = steps

    # Execute steps
    run_steps(selected_steps,parallel=args.parallel and not no_parallel)
