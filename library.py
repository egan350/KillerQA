import datetime
import requests
import json

_headers = {}
_variables = {}
current_date = datetime.datetime.now()
formatted_date = current_date.strftime('%Y-%m-%d')
_last_response = None
_SKIP_HTTP_STATUSES = {502, 503, 504}


class Skip(Exception):
    """Precondition not met; the test or remaining steps should be skipped."""


def _raise_if_unavailable(url, response):
    if response.status_code in _SKIP_HTTP_STATUSES:
        raise Skip(f"HTTP {response.status_code} from {url}")


def require_reachable(url, timeout=5):
    try:
        requests.head(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        try:
            requests.get(url, timeout=timeout)
        except requests.RequestException as e:
            raise Skip(f"host not reachable: {url} ({e})") from e

    print(f"Reachable: {url}")

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
    _raise_if_unavailable(url, _last_response)

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

    print(f"Time '{formatted_date}'")
    keyword2 = formatted_date
    matches = 0

    with open(file_path, 'r') as file:
        search_keyword1 = keyword1 if case_sensitive else keyword1.lower()
        search_keyword2 = keyword2 if case_sensitive else keyword2.lower()

        for line_number, line in enumerate(file, 1):
            line_content = line if case_sensitive else line.lower()

            if search_keyword1 in line_content and search_keyword2 in line_content:
                matches += 1
                print(f"Line {line_number}: {line.strip()}")

    if matches != 0:
        raise AssertionError(
            f"ERROR lines matching '{keyword1}' and date '{keyword2}' in {file_path}"
        )

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
    _raise_if_unavailable(url, _last_response)

import datetime
import requests


def search_log_today_date_ai(file_path: str, keyword: str) -> None:
    formatted_date = datetime.datetime.now().strftime("%Y-%m-%d")

    with open(file_path, "r", encoding="utf-8") as file:
        log_contents = file.read()

    question = f"""
Check the log content below for occurrences of the keyword "{keyword}"
on the date {formatted_date}.

Respond with exactly one of these values:
ERRORS_FOUND
NO_ERRORS

Log content:
{log_contents}
""".strip()

    response = requests.post(
        "http://localhost:8080/v1/chat/completions",
        json={
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ],
            "temperature": 0.0,
            "max_tokens": 20,
            "stream": False,
        },
        timeout=600,
    )

    response.raise_for_status()

    data = response.json()

    try:
        result = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected model response: {data}") from exc

    print("\n===== Llama.cpp =====")
    print(result)
    print("=====================\n")

    if result == "NO_ERRORS":
        print(f"AI found no errors for {formatted_date}.")
        return

    if result == "ERRORS_FOUND":
        raise AssertionError(
            f"Keyword {keyword!r} found in {file_path} for {formatted_date}."
        )

    raise ValueError(f"Unexpected model result: {result!r}")
