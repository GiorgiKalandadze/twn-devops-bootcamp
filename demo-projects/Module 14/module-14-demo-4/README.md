# EC2 Volume Backup & Restore

Three Python scripts that automate backing up, cleaning up, and restoring EC2 volumes in `eu-central-1`.

| Script | What it does |
|--------|--------------|
| `volume_backups.py` | Creates a snapshot of every volume tagged `Name=prod`, once a day |
| `cleanup_snapshots.py` | Deletes old snapshots and keeps the 2 most recent per volume |
| `restore_volume.py` | Creates a new volume from the latest snapshot and attaches it to an instance |

**Note:** `cleanup_snapshots.py` permanently deletes snapshots.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## Running

### 1. Create backups

```bash
python volume_backups.py
```

The script keeps running and creates new snapshots every day. Stop it with `Ctrl+C`.

### 2. Clean up old snapshots

```bash
python cleanup_snapshots.py
```

For each volume tagged `Name=prod`, snapshots are sorted by date and everything except the 2 newest is deleted. The script runs once and exits.

### 3. Restore a volume

```bash
python restore_volume.py
```

The script finds the volume attached to the instance, picks its latest snapshot, creates a new volume from it, waits until the volume is `available`, and attaches it to the instance as `/dev/xvdb`. The script runs once and exits.

## Configuration

Region, tag filter, and schedule (`volume_backups.py`):

```python
ec2_client = boto3.client('ec2', region_name="eu-central-1")
Filters=[{'Name': 'tag:Name', 'Values': ['prod']}]
schedule.every().day.do(create_volume_snapshots)
```

Number of snapshots to keep (`cleanup_snapshots.py`). Change `2` to keep more or fewer:

```python
for snap in sorted_by_date[2:]:
```

Instance, availability zone, and device name (`restore_volume.py`):

```python
instance_id = "i-0671d0fe02906a969"
AvailabilityZone="eu-central-1a"
Device='/dev/xvdb'
```

The availability zone must match the zone of the instance.

## Example Output

Backup:

```text
{'SnapshotId': 'snap-0a1b2c3d4e5f67890', 'State': 'pending', 'VolumeId': 'vol-0123456789abcdef0', ...}
```

Cleanup (one response is printed for each deleted snapshot):

```text
{'ResponseMetadata': {'HTTPStatusCode': 200, ...}}
```

Restore:

```text
2026-10-21 16:00:00+00:00
creating
creating
available
```

The first line is the start time of the snapshot used for the restore. The following lines show the state of the new volume until it is `available`, at which point it is attached.