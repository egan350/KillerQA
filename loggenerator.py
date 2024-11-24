import random
import datetime

def generate_log_file(file_path, num_lines=100):
    log_levels = ["INFO", "ERROR", "WARNING", "DEBUG"]
    messages = [
        "System started successfully",
        "Failed to connect to the database",
        "User login successful",
        "Timeout occurred while processing request",
        "Disk space running low",
        "Error writing to file",
        "User logged out",
        "Memory allocation error"
    ]

    with open(file_path, 'w') as file:
        for _ in range(num_lines):
            # Generate a random timestamp
            timestamp = datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 365))
            log_level = random.choice(log_levels)
            message = random.choice(messages)
            # Write a log entry with a timestamp, log level, and message
            file.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{log_level}] {message}\n")

# Example usage:
# Generate a log file with 100 lines
generate_log_file('sample_log.log', num_lines=100)
