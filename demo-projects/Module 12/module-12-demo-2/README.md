# Module 12 — Demo 2: Modularize Project

## Technologies Used
* **Terraform** (Infrastructure as Code)
* **Amazon Web Services (AWS)** (VPC, Subnet, Route Table, Internet Gateway, EC2, Security Group)
* **Docker** (Nginx container runtime)
* **Linux** (Amazon Linux 2)
* **Git** (Version Control)

---

## Project Description
* Refactored the monolithic Terraform configuration from Demo 1 into clean, reusable child modules (`modules/subnet` and `modules/webserver`).
* Created input variable interfaces and output declarations for each module to pass dynamic attributes (such as Subnet ID and Security Group IDs) between module boundaries.
* Updated the root module (`main.tf`) to invoke child modules while maintaining explicit dependencies and variable scoping.
* Verified that provisioning infrastructure through child modules creates identical AWS networking and web server components with zero breaking changes.

---

## Key Concepts
* **Terraform Modules:** Encapsulating related infrastructure components into self-contained, re-usable building blocks (`modules/<name>`).
* **Module Inputs & Outputs:** Passing values into child modules via input variables and exporting attributes using `output` blocks for consumption by other modules or the root environment.
* **DRY Principle:** Reducing duplication across environments by parameterizing infrastructure code.
* **Module Scoping:** Managing resource references cleanly across parent and child module scopes.

---

## Architecture Diagram

```text
 +-----------------------------------------------------------------------+
 |                              Root Module                              |
 |                      (main.tf / variables.tf)                         |
 |                                                                       |
 |   +-------------------------------+   +---------------------------+   |
 |   |        modules/subnet         |   |     modules/webserver     |   |
 |   |                               |   |                           |   |
 |   | - Custom VPC                  |   | - Security Group          |   |
 |   | - Public Subnet               |   | - Key Pair                |   |
 |   | - Internet Gateway            |======> EC2 Instance           |   |
 |   | - Route Table & Association   |   |   (Nginx Docker via       |   |
 |   +-------------------------------+   |    user_data script)      |   |
 |                   |                   +---------------------------+   |
 |                   |                                                   |
 |                   +---> Exports: subnet.id & vpc.id ------------------+
 +-----------------------------------------------------------------------+
```

---

## Step-by-Step Implementation

### Step 1: Structure Subnet Module
* Created `modules/subnet/` containing `main.tf`, `variables.tf`, and `outputs.tf` to encapsulate the Custom VPC, Subnet, Internet Gateway, and Route Table.
* Exported `aws_subnet.myapp-subnet-1.id` and `aws_vpc.myapp-vpc.id` via `outputs.tf`.

### Step 2: Structure Webserver Module
* Created `modules/webserver/` containing `main.tf`, `variables.tf`, and `outputs.tf` to handle Security Groups, SSH Key Pair creation, and the EC2 Instance deployment.
* Parameterized the `subnet_id` input so it accepts the output exported by the subnet module.

### Step 3: Update Root Configuration & Apply
* Updated the root `main.tf` to call both modules and pass configuration parameters.
* Executed `terraform init` to initialize the child modules, followed by `terraform apply`.

---

## What I Learned
* How to break down a single large Terraform file into logical, reusable modules.
* How to chain module outputs into other module inputs to establish explicit dependencies.
* How `terraform init` installs and links local child modules before plan/apply execution.

---

## Cleanup
To destroy all provisioned modular resources, run:
```bash
terraform destroy