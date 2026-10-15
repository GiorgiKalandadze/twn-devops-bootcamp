# Module 12 — Demo 5: Complete CI/CD with Terraform

## Demo Project
Complete CI/CD with Terraform

## Technologies Used
* **Terraform** (Infrastructure as Code & Remote S3 State Backend)
* **Jenkins** (CI/CD Automation Server & Declarative Pipelines)
* **Docker & Docker Hub** (Containerization & Registry)
* **Amazon Web Services (AWS)** (EC2, VPC, Subnets, Security Groups, S3)
* **Linux** (Amazon Linux 2 environment)
* **Git & GitLab** (Version Control & Shared Pipeline Library)

## Project Description
* Integrated an automated infrastructure provisioning stage into a complete Jenkins CI/CD pipeline to dynamically spin up cloud servers on-demand rather than deploying to static environments.
* Configured secure AWS credentials and SSH key pairs (`twn-key-pair` / `server-ssh-key`) inside Jenkins.
* Stored Terraform state remotely in an AWS S3 bucket (`myapp-tf-s3-bucket`) to maintain a single source of truth across pipeline runs.
* Updated the declarative `Jenkinsfile` to execute building application code, containerizing and pushing images to Docker Hub, initializing/applying Terraform configurations, and automatically deploying applications onto newly provisioned EC2 instances via Docker Compose.

## Key Concepts
* **Dynamic Server Provisioning in CI/CD:** Using Terraform inside pipeline stages to create fresh cloud infrastructure per build cycle.
* **Remote S3 State Management:** Decoupling state files from local runner storage and storing them securely in AWS S3 with locking capability.
* **Pipeline Orchestration with Shared Libraries:** Leveraging modularized Groovy pipeline steps to build, push, provision, and deploy smoothly.
* **Automated Secure Deployment:** Copying configuration files (`server-cmds.sh`, `docker-compose.yaml`) over SSH and executing secure remote logins to run containers.

## Step-by-Step Implementation

### Step 1: Set Up Credentials and AWS Key Pair
* Created an AWS EC2 Key Pair (`twn-key-pair`) for remote host access.
* Added AWS access keys and SSH credentials securely into Jenkins.

### Step 2: Configure Terraform Infrastructure & S3 Backend
* Configured `terraform` blocks with an S3 backend for state tracking.
* Defined VPCs, public subnets, internet gateways, route tables, and security groups with dynamic CIDR inputs.
* Configured the Amazon Linux 2 AMI data source and tied user data bootstrapping scripts.

### Step 3: Configure Declarative Pipeline (`Jenkinsfile`)
* Defined multi-stage pipeline (`build app`, `build image`, `provision server`, `deploy`).
* Extracted the dynamic `EC2_PUBLIC_IP` from Terraform outputs to target deployment commands.


### Step 4:  Configure Shared Remote S3 State & Terraform Infrastructure

* Configured the Terraform block with an S3 backend to store state centrally:
```
terraform {
  required_version = ">= 0.12"
  backend "s3" {
    bucket = "myapp-tf-s3-bucket"
    key    = "myapp/state.tfstate"
    region = "eu-central-1"
  }
}
```

## What I Learned
* How to combine Infrastructure as Code with CI/CD automation pipelines.
* How to securely manage Terraform state files in production using remote S3 backends.
* How to orchestrate remote server setup, authentication, and Docker Compose deployment dynamically.

## Cleanup
To destroy all provisioned infrastructure resources and prevent ongoing costs, run:
```bash
terraform destroy