# EKS Cluster Info

A Python script that fetches and displays the status, endpoint, and version of all EKS clusters in a region (default: `eu-central-1`).

## Setup

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

## Running

Use the default region:

```bash
python eks_cluster_info.py
```

Use a different region:

```bash
python eks_cluster_info.py --region eu-west-3
```

## Configuration

The default region is set near the top of `eks_cluster_info.py`:

```python
REGION = "eu-central-1"
```

## Example Output

```text
Cluster demo-cluster status is ACTIVE
Cluster endpoint: https://ABCDEF1234567890.gr7.eu-central-1.eks.amazonaws.com
Cluster version: 1.30
```

If the region has no clusters, the script prints `No EKS clusters found in <region>`.