import datetime
import requests
import json

_headers = {}
_variables = {}
current_date = datetime.datetime.now()
formatted_date = current_date.strftime('%Y-%m-%d')
_last_response = None

def open_file(filename):
    print(f"Opening file: {filename}")


def write_to_file(filename, text):
    with open(filename, "a") as f:
        f.write(text)
    print(f"Wrote '{text}' to {filename}")

def get_api(url):
    global _last_response

    _last_response = requests.get(
        url,
        headers=_headers
    )

    print(f"GET {url}")
    print(f"Status Code: {_last_response.status_code}")

def verify_status_code(expected):
    global _last_response

    if _last_response is None:
        raise RuntimeError("No API response available.")

    actual = _last_response.status_code

    if actual != int(expected):
        raise AssertionError(
            f"Expected status {expected}, got {actual}"
        )

    print(f"Verified status code {expected}")

def verify_json_value(field, expected):
    global _last_response

    if _last_response is None:
        raise RuntimeError("No API response available.")

    value = _last_response.json()

    for key in field.split("."):
        if not isinstance(value, dict) or key not in value:
            raise AssertionError(
                f"Field '{field}' not found"
            )

        value = value[key]

    if str(value) != expected:
        raise AssertionError(
            f"{field}: expected '{expected}', got '{value}'"
        )

    print(f"Verified {field} = {expected}")

def search_log_today_date(file_path, keyword1, keyword2=None, case_sensitive=True):
    if not file_path or not keyword1:
        raise TypeError("Both 'file_path' and 'keyword1' are required parameters.")

    try:
        print(f"Time '{formatted_date}'")
        keyword2=formatted_date
        with open(file_path, 'r') as file:
            # Convert keywords to lowercase if case-insensitive search is selected
            search_keyword1 = keyword1 if case_sensitive else keyword1.lower()
            search_keyword2 = keyword2 if case_sensitive else (keyword2.lower() if keyword2 else None)

            # Iterate through each line in the log file
            for line_number, line in enumerate(file, 1):
                # Apply case-sensitivity as needed
                line_content = line if case_sensitive else line.lower()

                # Check if the line contains keyword1 and, if provided, keyword2
                if (search_keyword1 in line_content) and (search_keyword2 in line_content if search_keyword2 else True):
                    # Print the line with the line number
                    print(f"Line {line_number}: {line.strip()}")
    except FileNotFoundError:
        # Handle the error by printing a message and not raising it
        print(f"The file '{file_path}' does not exist.")
    except Exception as e:
        # Handle other types of errors and report them
        print(f"An error occurred: {e}")

def save_json_value(field, variable):
    global _last_response
    global _variables

    if _last_response is None:
        raise RuntimeError("No API response available.")

    value = _last_response.json().get(field)

    if value is None:
        raise AssertionError(
            f"Could not find '{field}' in response"
        )

    _variables[variable] = value

    print(f"Saved {field} as {variable}")

def set_header(name, value):
    global _headers
    global _variables

    for key, val in _variables.items():
        value = value.replace("${"+key+"}", str(val))

    _headers[name] = value

    print(f"Header set {name}")


def post_api(url, body):
    global _last_response

    body = json.loads(body)

    _last_response = requests.post(
        url,
        json=body,
        headers=_headers
    )

    print(f"POST {url}")
    print(f"Status Code: {_last_response.status_code}")
