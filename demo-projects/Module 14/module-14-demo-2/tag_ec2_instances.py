import boto3

REGION_ENV = {
    "eu-central-1": "prod", 
    "eu-west-3": "dev",      
}


def tag_instances(region, environment):
    ec2 = boto3.client("ec2", region_name=region)

    instance_ids = [
        instance["InstanceId"]
        for reservation in ec2.describe_instances()["Reservations"]
        for instance in reservation["Instances"]
    ]

    if not instance_ids:  
        return

    ec2.create_tags(
        Resources=instance_ids,
        Tags=[{"Key": "environment", "Value": environment}],
    )


for region, environment in REGION_ENV.items():
    tag_instances(region, environment)