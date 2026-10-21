# EC2 Health Check

A Python script that checks the status of EC2 instances in `eu-west-3` and prints them to the console every 5 seconds.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## Running

```bash
python ec2_health_check.py
```

The script checks immediately, then repeats every 5 seconds. Stop it with `Ctrl+C`.

## Configuration

The region and interval are set near the top of `ec2_health_check.py`.

## Example Output

```text
Instance i-0a1b2c3d4e5f67890 is running with instance status ok and system status ok
Instance i-0f9e8d7c6b5a43210 is stopped with instance status not-applicable and system status not-applicable
#############################
```