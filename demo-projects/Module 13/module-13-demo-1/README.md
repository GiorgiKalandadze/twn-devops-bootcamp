# Module 13: Demo 1 - Write Countdown Application

## Demo Project

### Write Countdown Application

### Technologies Used

- Python (Programming Language)
- IntelliJ IDEA / PyCharm (IDE)
- Git (Version Control)

### Project Description

- Built a CLI-based Python application that accepts user input containing a goal and a target deadline date.
- Parsed and calculated the remaining time (days and hours) from the current moment until the target deadline using Python's built-in `datetime` module.
- Formatted the calculated output to display clear, human-readable countdown information to the user.

### Key Concepts

- **User Input Parsing:** Splitting user inputs (`goal:dd.mm.yyyy`) using Python string methods to extract discrete target values.
- **Date & Time Manipulation:** Working with `datetime.datetime.strptime()` to convert user-provided date strings into standard Python `datetime` objects.
- **Datetime Arithmetic:** Subtracting the current timestamp (`datetime.now()`) from a future `datetime` object to compute time differences via `timedelta`.

## Implementation Code (`time-till-deadline.py`)

```python
from datetime import datetime

# Accept user input for goal and deadline separated by a colon
user_input = input("Enter your goal with a deadline separated by colon (e.g., learn python:20.12.2026):\n")

# Split the input into goal and deadline date string
input_list = user_input.split(":")
goal = input_list[0]
deadline = input_list[1]

# Convert deadline string into datetime object
deadline_date = datetime.strptime(deadline, "%d.%m.%Y")

# Get current datetime
today_date = datetime.now()

# Calculate remaining time
time_till = deadline_date - today_date

hours_till = int(time_till.total_seconds() / 60 / 60)

print(f"Dear user, time remaining for your goal '{goal}' is {time_till.days} days (or {hours_till} hours).")
```

## Step-by-Step Implementation

### Step 1: Initialize Project & Working Environment

- Configured a Python virtual environment and set up the project repository in IntelliJ / PyCharm with Git initialized.

### Step 2: Accept and Parse Input

- Prompted the user for interactive input in the format `<goal>:<deadline>`.
- Separated the input string using Python's `.split(":")` method to isolate the goal description and target date.

### Step 3: Date Calculations

- Imported Python's `datetime` module.
- Converted the user's string into a valid date object via `datetime.strptime(deadline, "%d.%m.%Y")`.
- Subtracted `datetime.now()` from `deadline_date` to generate a `timedelta` object.

### Step 4: Display Countdown

- Extracted total days (`.days`) and computed total remaining hours (`.total_seconds() / 3600`).
- Output a formatted string with the remaining time details to stdout.

