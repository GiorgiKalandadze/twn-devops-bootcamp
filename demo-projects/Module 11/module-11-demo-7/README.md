# Complete CI/CD Pipeline with EKS and AWS ECR

## Technologies Used

Kubernetes, Jenkins, AWS EKS, AWS ECR, Java, Maven, Linux, Docker, Git

## Project Description

* Created a private AWS ECR repository (`java-maven-app`) to host application Docker images securely within AWS infrastructure
* Updated Kubernetes deployment manifests to target the ECR registry URI and referenced image pull secrets configured for AWS authentication
* Updated the Jenkins CI pipeline to authenticate with AWS ECR using stored AWS credentials, build the Java application container image, and push versioned tags directly to ECR
* Integrated end-to-end Kubernetes deployment into the pipeline, applying manifests using dynamic value replacement (`envsubst`) and verifying cluster status
* Configured and executed the end-to-end CI/CD workflow containing:
a. CI step: Increment version using Maven
b. CI step: Build application artifact (`.jar`) with Maven
c. CI step: Build and push Docker image to AWS ECR
d. CD step: Deploy the new application version to the AWS EKS cluster
e. CD step: Commit and push the updated `pom.xml` version back to GitLab

---

## Architecture

```
GitLab (java-maven-app, branch: main)
       │
       ▼
┌─────────────────────────── Jenkins Pipeline ───────────────────────────┐
│                                                                          │
│  1) increment version   — mvn versions:set, IMAGE_NAME = version-BUILD# │
│  2) build app           — mvn clean package                            │
│  3) build & push image  — aws ecr get-login-password, docker build,    │
│                           docker push <AWS_ACCOUNT>.dkr.ecr.<REGION>.  │
│                           amazonaws.com/java-maven-app:IMAGE_NAME        │
│  4) deploy               — envsubst kubernetes/deployment.yaml          │
│                            envsubst kubernetes/service.yaml             │
│                            kubectl apply -f -   (against EKS)           │
│  5) commit version update — push pom.xml bump back to GitLab            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
       │                                          │
       ▼                                          ▼
   AWS ECR (private: java-maven-app)          EKS Cluster (demo-cluster)
       ▲                                          │
       │                                          ▼
       └──── pulled using imagePullSecrets ──  java-maven-app Pod
             (Secret: aws-registry-key,           Running
              kubernetes.io/dockerconfigjson)

```

---

## Steps

1. **Create the Private AWS ECR Repository**
Created the private repository `java-maven-app` in AWS ECR under the region `eu-central-1` to store versioned application images.


📸 **Screenshot 1** — Private AWS ECR repository `java-maven-app` successfully created


2. **Configure ECR Credentials in Jenkins**
Added the required AWS credentials (`ecr-credentials`) alongside existing AWS and GitLab credentials inside the Jenkins Credentials Manager to authorize image builds and deployment actions[cite: 2].
📸 **Screenshot 2** — `ecr-credentials` configured in Jenkins Credentials Store[cite: 2]
[cite: 2]
3. **Create the ECR Image Pull Secret on the EKS Cluster**
Generated an ECR authorization token using the AWS CLI and created a `docker-registry` Secret (`aws-registry-key`) in Kubernetes so EKS node kubelets can pull private images from ECR[cite: 3]:
```bash
aws ecr get-login-password --region eu-central-1 | kubectl create secret docker-registry aws-registry-key \
  --docker-server=252324673517.dkr.ecr.eu-central-1.amazonaws.com \
  --docker-username=AWS \
  --docker-password-stdin

```


Verified secret creation with `kubectl get secret`[cite: 3]:
```bash
kubectl get secret

```


📸 **Screenshot 3** — `aws-registry-key` Secret created alongside existing registry keys on EKS[cite: 3]
[cite: 3]
4. **Update Jenkinsfile for ECR Build, Push, and Deployment**
Configured the pipeline stages in `Jenkinsfile`:
* Auth to ECR using `aws ecr get-login-password`
* Tagged image with format `${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}[.amazonaws.com/java-maven-app:$](https://.amazonaws.com/java-maven-app:$){IMAGE_NAME}`
* Substituted variables (`envsubst`) into `deployment.yaml` and `service.yaml`, pointing to `aws-registry-key` under `imagePullSecrets`
* Executed `kubectl apply -f -` against the EKS cluster


5. **Run the Complete CI/CD Pipeline**
Triggered the Jenkins build to run through versioning, building, image publishing to ECR, deploying to EKS, and committing code changes back to GitLab[cite: 5].
📸 **Screenshot 4** — Pipeline console output confirming successful completion (`Finished: SUCCESS`) and Git version commit push[cite: 5]
[cite: 5]
6. **Verify Application Deployment and Pod Image Source on EKS**
Checked pod deployment status on the cluster[cite: 4]:
```bash
kubectl get pods

```


📸 **Screenshot 5** — Application Pods in `Running` status on EKS[cite: 4]
[cite: 4]
Inspected pod details to confirm image pulling directly from AWS ECR[cite: 6]:
```bash
kubectl describe pod java-maven-app-8f98778c-9zxhn

```


📸 **Screenshot 6** — `kubectl describe pod` output confirming image pulled from AWS ECR repository (`[252324673517.dkr.ecr.eu-central-1.amazonaws.com/java-maven-app:1.1.12-15](https://252324673517.dkr.ecr.eu-central-1.amazonaws.com/java-maven-app:1.1.12-15)`)[cite: 6]
[cite: 6]

---

## What I Learned

* AWS ECR integration requires temporary Docker authentication tokens generated via `aws ecr get-login-password` rather than standard persistent password strings
* How to configure Kubernetes `imagePullSecrets` with `aws-registry-key` so EKS nodes pull images securely from private AWS ECR registries[cite: 3, 6]
* Structuring seamless CI/CD execution by centralizing build dependencies (Java/Maven), container execution (Docker/ECR), and orchestration (Kubernetes/EKS) inside a single Jenkins pipeline[cite: 2, 4, 5]
* Verifying container runtime specifications using `kubectl describe pod` to confirm precise image registry URIs and image digests deployed on EKS[cite: 6]

---

## Cleanup

```bash
# Delete the application deployment and service from EKS
kubectl delete -f kubernetes/service.yaml
kubectl delete -f kubernetes/deployment.yaml

# Remove the ECR image pull secret from the cluster
kubectl delete secret aws-registry-key

# Delete the ECR repository and its images via AWS CLI
aws ecr delete-repository --repository-name java-maven-app --region eu-central-1 --force

```

---

