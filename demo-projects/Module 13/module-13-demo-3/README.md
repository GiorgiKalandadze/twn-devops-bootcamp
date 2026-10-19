# Module 13: Programming with Python - API Request to GitLab

## Demo Project

API Request to GitLab

## Technologies Used

- Python
- GitLab
- Git

## Project Description

- Write an application that talks to an API of an external application (GitLab) and lists all the public GitLab repositories for a specified user.

## Implementation Code

```python
import requests
response = requests.get("https://gitlab.com/api/v4/users/giorgikalandadze24/projects")
my_projects = response.json()

# print the whole objects list
print(my_projects)
print(type(my_projects))

# print just the names and urls
for project in my_projects:
    print(f"Project Name: {project['name']}\nProject Url: {project['http_url_to_repo']}\n")
```

## How the API Works

The script sends an HTTP GET request to the GitLab REST API endpoint for a user's projects. The API responds with JSON, which `response.json()` converts into a Python list of dictionaries, where each dictionary describes one project.

## Step-by-Step Implementation

### Step 1: Set Up the Environment

- Created a Python project in IntelliJ IDEA / PyCharm with a virtual environment.
- Installed the `requests` library for making HTTP calls.
- Initialized a Git repository for version control.

### Step 2: Send the API Request

- Called `requests.get()` on the GitLab endpoint `/api/v4/users/<username>/projects`.
- Stored the response object in `response`.

### Step 3: Parse the JSON Response

- Converted the response body to a Python object with `response.json()`.
- Printed the full list and its type to confirm the structure.

### Step 4: Extract and Display Project Details

- Looped through each project dictionary.
- Printed the `name` and `http_url_to_repo` fields for each project.

## Notes and Improvements

- The script does not check `response.status_code`. If the username does not exist, GitLab returns an error object instead of a list, and the loop will fail.
- The username is hardcoded. Reading it with `input()` would make the script reusable.
- GitLab returns 20 projects per page by default. Users with more projects need pagination (the `page` and `per_page` query parameters).

