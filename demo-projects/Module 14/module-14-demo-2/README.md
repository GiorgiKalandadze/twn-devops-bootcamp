# Tag EC2 Instances

A Python script that adds an `environment` tag to all EC2 instances in two regions:

- `eu-central-1`: `environment=prod`
- `eu-west-3`: `environment=dev`

**Note:** The script overwrites an existing `environment` tag on any instance that already has one.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## Running

Preview without changing anything:

```bash
python tag_ec2_instances.py --dry-run
```

Apply the tags:

```bash
python tag_ec2_instances.py
```

## Configuration

The region-to-environment mapping is set near the top of `tag_ec2_instances.py`:

```python
REGION_ENVIRONMENTS = {"eu-central-1": "prod", "eu-west-3": "dev"}
```

## Example Output

```text
[DRY RUN] eu-central-1: would tag 2 instance(s) with environment=prod
[DRY RUN] eu-west-3: would tag 1 instance(s) with environment=dev
```

If a region has no instances, the script prints `No instances found in <region>` and continues.