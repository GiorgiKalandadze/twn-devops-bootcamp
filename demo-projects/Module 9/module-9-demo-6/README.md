# Module 9 — AWS Services

## Demo Project: Interacting with AWS CLI

**Technologies:** AWS (EC2, IAM, VPC, Security Groups) · Linux

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Install and configure AWS CLI to connect to the AWS account
- Create EC2 infrastructure using CLI: Security Group, key pair, EC2 instance
- SSH into the newly created EC2 instance
- Create IAM resources using CLI: User, Group, Policy, add User to Group
- List and filter AWS resources using `--filter` and `--query` options
- Delete all created resources via CLI at the end

---

## Architecture

```
  Local Terminal (macOS)
  AWS CLI configured with admin IAM credentials
         │
         ├─── aws ec2 commands ───────────────────────────────────────▶  AWS EC2 (eu-north-1)
         │                                                                ┌──────────────────────┐
         │                                                                │  Security Group      │
         │                                                                │  Key Pair            │
         │                                                                │  EC2 Instance        │
         │                                                                │  (t3.micro)          │
         │                                                                └──────────────────────┘
         │                                                                         │
         ├─── ssh -i cli-demo-key.pem ────────────────────────────────▶  ec2-user@<PUBLIC_IP>
         │
         └─── aws iam commands ───────────────────────────────────────▶  AWS IAM
                                                                          ┌──────────────────────┐
                                                                          │  Group               │
                                                                          │  User                │
                                                                          │  Policy (EC2 RO)     │
                                                                          └──────────────────────┘

  No Jenkins · No Docker · Command-line only
```

---

## Steps

### Step 1 — Install AWS CLI v2 on Local Machine

Download and install the AWS CLI v2 package for macOS:

```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
aws --version
```

---

### Step 2 — Configure AWS CLI with Admin User Credentials

Run `aws configure` and enter the Access Key ID, Secret Access Key, default region (`eu-north-1`), and output format (`json`). Verify the connection:

```bash
aws configure
# prompts: Access Key ID, Secret Access Key, region: eu-north-1, output: json

aws iam get-user
```

---

### Step 3 — Create a Security Group via CLI

Look up the default VPC ID, create a Security Group, then add an SSH inbound rule restricted to your home IP:

```bash
aws ec2 describe-vpcs

aws ec2 create-security-group \
  --group-name cli-demo-sg \
  --description "CLI demo security group" \
  --vpc-id <VPC_ID>

aws ec2 authorize-security-group-ingress \
  --group-id <SG_ID> \
  --protocol tcp \
  --port 22 \
  --cidr <HOME_IP>/32
```

---

### Step 4 — Create an SSH Key Pair via CLI

Generate a key pair, save the private key to a `.pem` file, and lock down its permissions:

```bash
aws ec2 create-key-pair \
  --key-name cli-demo-key \
  --query 'KeyMaterial' \
  --output text > cli-demo-key.pem

chmod 400 cli-demo-key.pem
```

---

### Step 5 — Launch an EC2 Instance via CLI

Find a subnet, launch a `t3.micro` instance using the key pair and Security Group created above, then confirm it reaches the running state:

```bash
aws ec2 describe-subnets

aws ec2 run-instances \
  --image-id <AMI_ID> \
  --count 1 \
  --instance-type t3.micro \
  --key-name cli-demo-key \
  --security-group-ids <SG_ID> \
  --subnet-id <SUBNET_ID>

aws ec2 describe-instances --instance-ids <INSTANCE_ID>
```

---

### Step 6 — SSH into the New EC2 Instance

Use the private key to connect as `ec2-user`:

```bash
ssh -i cli-demo-key.pem ec2-user@<EC2_PUBLIC_IP>
```

---

### Step 7 — List and Filter EC2 Resources with `--filter` and `--query`

Retrieve only running instances and extract specific fields using JMESPath:

```bash
aws ec2 describe-instances \
  --filter "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].{ID:InstanceId,IP:PublicIpAddress,State:State.Name}"
```

---

### Step 8 — Create IAM Resources via CLI

Create a Group and User, add the User to the Group, attach an AWS-managed policy, and generate console and programmatic credentials:

```bash
aws iam create-group --group-name cli-demo-group
aws iam create-user --user-name cli-demo-user
aws iam add-user-to-group --user-name cli-demo-user --group-name cli-demo-group

# Find the managed policy ARN
aws iam list-policies \
  --query 'Policies[?PolicyName==`AmazonEC2ReadOnlyAccess`].{ARN:Arn}' \
  --output text

aws iam attach-group-policy \
  --group-name cli-demo-group \
  --policy-arn <POLICY_ARN>

aws iam create-login-profile \
  --user-name cli-demo-user \
  --password <PASSWORD> \
  --password-reset-required

aws iam create-access-key --user-name cli-demo-user
```

---

### Step 9 — Verify IAM User in AWS Console

Log into the AWS Console as `cli-demo-user` and confirm that EC2 read-only access works while write operations are denied.

---

### Step 10 — Delete All Resources via CLI

Clean up in the correct order — IAM dependencies must be removed before deleting the principal objects; the EC2 instance must be terminated before deleting the Security Group:

```bash
# IAM cleanup (order matters)
aws iam detach-group-policy --group-name cli-demo-group --policy-arn <POLICY_ARN>
aws iam remove-user-from-group --user-name cli-demo-user --group-name cli-demo-group
aws iam delete-login-profile --user-name cli-demo-user
aws iam delete-access-key --user-name cli-demo-user --access-key-id <KEY_ID>
aws iam delete-user --user-name cli-demo-user
aws iam delete-group --group-name cli-demo-group

# EC2 cleanup (order matters)
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
aws ec2 delete-key-pair --key-name cli-demo-key
aws ec2 delete-security-group --group-id <SG_ID>
```

---

## What I Learned

- AWS CLI is a full alternative to the console for creating and managing resources — every action available in the UI has a corresponding CLI command
- `--filter` narrows which resources the API returns (e.g. only instances in `running` state), reducing noise in the output
- `--query` uses JMESPath syntax to extract specific fields from JSON responses, making it easy to pull just the data you need (IDs, IPs, states)
- IAM resources must be deleted in a specific order: detach policies → remove user from group → delete login profile → delete access key → delete user → delete group; skipping steps causes dependency errors
- EC2 resources must also be deleted in order: terminate the instance first, then delete the key pair and Security Group — AWS blocks Security Group deletion while it is still associated with a running instance
- CLI-driven workflows are preferred in DevOps over manual console actions because they are repeatable, scriptable, and versionable — the same commands can be run in a pipeline or shared as a script

---

## Cleanup

All resources created in this demo were deleted as part of Step 10. Nothing remains running or billable after completing this demo.

---
