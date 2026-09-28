# Create AWS EKS Cluster with a Node Group

## Technologies Used
Kubernetes, AWS EKS, AWS EC2, AWS IAM, AWS CloudFormation

## Project Description
- Provisioned a managed Kubernetes cluster on AWS using Elastic Kubernetes Service (EKS)
- Configured the IAM Roles required for the EKS control plane and for the worker nodes
- Created a dedicated VPC with public and private subnets using the AWS-provided CloudFormation template
- Created a Node Group of EC2 instances as worker nodes and attached it to the EKS cluster
- Connected kubectl locally to the EKS cluster via kubeconfig
- Configured Cluster Autoscaler so worker nodes scale automatically with pod demand
- Deployed a sample nginx application and scaled it to trigger autoscaling

### Key Concepts

**EKS = managed Kubernetes.** AWS runs and replicates the Control Plane across multiple Availability Zones for high availability. You are only responsible for the Worker Nodes (the Compute Fleet).

**Two IAM Roles are required, and they are not the same thing:**
1. **EKS Cluster Role** — lets AWS create and manage cluster components (the Control Plane) on your behalf
2. **Node Group Role** — lets kubelet running on each worker node authenticate to other AWS services (ECR, EC2, the CNI plugin)

**Why a custom VPC:** EKS needs specific networking and firewall configuration for Control Plane ↔ Worker Node communication. Best practice is to configure both a public and a private subnet, then give the IAM Role permission to adjust VPC configuration on K8s' behalf.

**Node Group = "semi-managed" workers.** Compared to EKS with plain EC2 (fully self-managed) or EKS with Fargate (fully managed), a Node Group sits in the middle: AWS creates and deletes the EC2 instances for you and pre-installs the required worker processes (container runtime, kubelet, kube-proxy), but you still configure the group yourself.

**Cluster Autoscaler** runs as a Pod inside the cluster. It watches for Pods that can't be scheduled due to insufficient resources and automatically adds new worker nodes. Rather than attaching autoscaling permissions directly to the Node Group Role (which would give every node in the group unnecessarily broad access), the autoscaler is granted permissions via **IRSA (IAM Roles for Service Accounts)**: an OIDC identity provider is registered for the cluster, a dedicated IAM Role is created that trusts that identity provider ("web identity"), a custom Auto-Scaling policy is attached to that role, and the `cluster-autoscaler` Pod's Kubernetes Service Account is annotated with the role's ARN. This follows the principle of least privilege — only the autoscaler Pod itself gets the permission, not the whole node.

## Architecture

```
                         AWS Managed Account
                  ┌─────────────────────────────────┐
                  │        EKS Control Plane          │
                  │   (replicated across 3 AZs)       │
                  └────────────────┬───────────────────┘
                                   │
                      Control Plane <-> Worker
                      communication (via VPC)
                                   │
                     Your AWS Account (custom VPC)
        ┌──────────────────────────┴───────────────────────────┐
        │                                                        │
  Public Subnet                                          Private Subnet
        │                                                        │
 ┌──────▼───────┐                                    ┌───────────▼──────────┐
 │  Elastic Load │                                    │      Node Group       │
 │   Balancer    │◄───────────────────────────────────│  (EC2 Worker Nodes)   │
 │ (LoadBalancer │                                    │                       │
 │   Services)   │                                    │  kubelet, kube-proxy, │
 └───────────────┘                                    │  container runtime    │
                                                        │                       │
                                                        │  ┌─────────────────┐  │
                                                        │  │cluster-autoscaler│  │
                                                        │  │      Pod          │  │
                                                        │  └─────────────────┘  │
                                                        └───────────────────────┘
                                   ▲
                                   │
                        kubectl (via kubeconfig)
                                   │
                            Local Machine
```

## Steps

1. **Create the EKS Cluster IAM Role**
   Create an IAM Role in the AWS account and attach the `AmazonEKSClusterPolicy`. This allows AWS to create and manage EKS components on your behalf.

2. **Create the VPC for Worker Nodes**
   Use the official AWS CloudFormation template to create a VPC with a public and private subnet configuration purpose-built for EKS.
   Reference: https://docs.aws.amazon.com/eks/latest/userguide/create-public-private-vpc.html

3. **Create the EKS Cluster (Control Plane Nodes)**
   In the AWS Console, create the EKS cluster and attach the Cluster IAM Role and the VPC created above.
   📸 `screenshot-01` — EKS cluster status showing `Active`

4. **Connect kubectl Locally**
   ```bash
   aws eks update-kubeconfig --name <CLUSTER_NAME> --region eu-north-1
   kubectl get svc
   ```
5. **Create the EC2 IAM Role for the Node Group**
   Attach these policies:
   - `AmazonEKSWorkerNodePolicy`
   - `AmazonEC2ContainerRegistryReadOnly`
   - `AmazonEKS_CNI_Policy`

   Kubelet is the main worker process — it schedules/manages Pods and communicates with other AWS services, so it needs this permission.

6. **Create the Node Group and Attach it to the Cluster**
   Create a Node Group of EC2 instances (Worker Nodes) and attach it to the EKS cluster.
   ```bash
   kubectl get nodes
   ```
   📸 `screenshot-02` — worker nodes showing `Ready`

7. **Configure Auto-Scaling (via IRSA)**
   a. Create a custom IAM Policy granting Auto-Scaling permissions (describe/set desired capacity on Auto Scaling Groups)
   b. Associate an IAM OIDC Identity Provider with the EKS cluster (if not already associated)
   c. Create an IAM Role trusting that OIDC provider ("web identity") — this is the IRSA role
   d. Attach the custom Auto-Scaling policy to that IRSA role
   e. Deploy the Cluster Autoscaler component into the cluster using the official manifest, edited to reference the correct cluster name and a matching image version, and annotate its Service Account with the IRSA role ARN:
   ```bash
   kubectl apply -f cluster-autoscaler-autodiscover.yaml
   kubectl annotate serviceaccount cluster-autoscaler -n kube-system \
     eks.amazonaws.com/role-arn=arn:aws:iam::<ACCOUNT_ID>:role/<IRSA_ROLE_NAME>
   ```
   Reference: https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html

8. **Verify the Autoscaler is Running**
   ```bash
   kubectl get pods -n kube-system
   ```
   📸 `screenshot-03` — `cluster-autoscaler` Pod Running

9. **Deploy a Sample Application**
   ```bash
   kubectl apply -f nginx-deployment.yaml
   ```

10. **Scale Beyond Current Node Capacity**
    ```bash
    kubectl scale deployment nginx --replicas=20
    ```

11. **Watch Autoscaling in Action**
    Pods initially show `Pending` due to insufficient node resources; the Cluster Autoscaler detects this and provisions new EC2 worker nodes automatically.
    ```bash
    kubectl get nodes
    kubectl get pods
    kubectl logs -n kube-system <cluster-autoscaler-pod>
    ```

## What I Learned
- The clear division of responsibility in EKS: AWS manages the Control Plane, you manage the Worker Nodes
- Why two separate IAM Roles are required and exactly what each one authorizes
- Why EKS requires a purpose-built VPC with public and private subnets, and why this is a security best practice
- How a Node Group differs from fully self-managed EC2 workers and from AWS Fargate
- How Cluster Autoscaler detects unschedulable Pods and reacts by adding nodes
- How IRSA (IAM Roles for Service Accounts) grants fine-grained AWS permissions to a specific Pod via OIDC, instead of over-granting permissions to the entire Node Group Role
- How to connect kubectl to a remote managed cluster using `aws eks update-kubeconfig`
- Cost awareness: the EKS Control Plane bills hourly regardless of usage, and worker nodes bill as standard EC2 instances

## Cleanup
Delete resources in reverse order of creation to avoid orphaned, still-billed AWS resources:

```bash
# 1. Remove the sample app (also removes any provisioned Load Balancer)
kubectl delete deployment nginx
kubectl delete svc nginx

# 2. Delete the Node Group (terminates the EC2 worker nodes)
# via EKS Console

# 3. Delete the EKS cluster
# via EKS Console

# 4. Delete the VPC CloudFormation stack
# via CloudFormation Console

# 5. Delete the IAM Roles and the custom Auto-Scaling policy
# via IAM Console
```

Afterward, verify in the AWS Console that no EC2 instances, Load Balancers, or NAT Gateways remain, to avoid unexpected charges.

## Screenshots

| # | Description |
|---|---|
| screenshot-01 | EKS cluster status `Active` in the AWS Console |
| screenshot-02 | Worker nodes showing `Ready` (`kubectl get nodes`) |
| screenshot-03 | `cluster-autoscaler` Pod running in `kube-system` |
| screenshot-04 | Nginx app working 