# EC2 Volume Backups

A Python script that creates snapshots of all EC2 volumes tagged `Name=prod` in `eu-central-1`. The backup runs once every day.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## Running

```bash
python volume_backups.py
```

The script keeps running and creates new snapshots every day. Stop it with `Ctrl+C`.

## Configuration

The region is set near the top of `volume_backups.py`:

```python
ec2_client = boto3.client('ec2', region_name="eu-central-1")
```

The volumes to back up are selected by tag. Change the filter to target other volumes:

```python
Filters=[{'Name': 'tag:Name', 'Values': ['prod']}]
```

The schedule is set at the bottom of the file:

```python
schedule.every().day.do(create_volume_snapshots)
```

## Example Output

```text
{'Description': '', 'Encrypted': False, 'OwnerId': '123456789012', 'Progress': '', 'SnapshotId': 'snap-0a1b2c3d4e5f67890', 'StartTime': datetime.datetime(2026, 10, 21, 16, 0, 0), 'State': 'pending', 'VolumeId': 'vol-0123456789abcdef0', 'VolumeSize': 8}
```

One line is printed for each volume that was backed up.