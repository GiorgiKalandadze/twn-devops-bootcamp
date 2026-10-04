# CD - Deploy to LKE Cluster from Jenkins Pipeline (Bonus)

## Technologies Used
Kubernetes, Jenkins, Linode LKE, Docker, Linux

## Project Description
- Created a managed Kubernetes cluster on Linode Kubernetes Engine (LKE)
- Stored the LKE kubeconfig as a Jenkins Secret file credential
- Installed the Jenkins **Kubernetes CLI Plugin**, which executes `kubectl` commands directly against a kubeconfig credential — no manual AWS-style authenticator setup required
- Adjusted the existing Jenkinsfile to use the plugin and deploy to the LKE cluster

## Key Concepts

**Reusing `kubectl` from the EKS demo.** Jenkins already had `kubectl` installed inside its container from the previous EKS demo — no need to install it again. What's different this time is *how* Jenkins authenticates against the cluster.

**Why LKE is simpler than EKS here.** EKS required installing a separate `aws-iam-authenticator` binary, because EKS authentication isn't just "a kubeconfig" — it delegates to AWS IAM and generates short-lived tokens at request time. LKE's kubeconfig, by contrast, is **self-contained**: it embeds a client certificate and key directly, so anything holding the file can authenticate immediately. No extra authenticator binary, no AWS SDK calls, no IAM mapping step.

**The Kubernetes CLI Plugin replaces manual `docker cp` + `KUBECONFIG` juggling.** Instead of manually copying a kubeconfig file into the Jenkins container and exporting `KUBECONFIG` by hand (as in the EKS demo), the **Kubernetes CLI Plugin** provides a `withKubeConfig` pipeline step. Given a Jenkins credential ID, it writes out the kubeconfig to a temp location and points `kubectl` at it automatically for the duration of the step — cleaner and less error-prone than manual file copying.

## Architecture

```
Linode Cloud Manager
       │
       │ provision
       ▼
  LKE Cluster  ──── kubeconfig downloaded (self-contained: embeds client cert + key)
       │                        │
       │                        ▼
       │              Jenkins credential
       │              (Secret file: lke-credentials)
       │                        │
       │                        ▼
       │         Jenkinsfile "deploy" stage
       │           withKubeConfig(credentialsId: 'lke-credentials') {
       │             kubectl get nodes / kubectl create deployment ...
       │           }
       │                        │
       └────────────────────────┘
          kubectl talks directly to LKE using the embedded cert — no external
          authenticator binary or IAM step needed (contrast with the EKS demo)
```

## Steps

1. **Create the LKE Cluster**
   Provisioned a new Kubernetes cluster via the Linode Cloud Manager. Downloaded the kubeconfig file and verified connectivity locally:
   ```bash
   kubectl --kubeconfig ./lke-kubeconfig.yaml get nodes
   ```


2. **Confirm kubectl Is Already Available in Jenkins**
   `kubectl` was already installed inside the Jenkins container during the EKS demo — nothing further needed here.

3. **Install the Kubernetes CLI Plugin in Jenkins**
   Manage Jenkins → Plugins → installed the **Kubernetes CLI Plugin**, which provides the `withKubeConfig` pipeline step used to run `kubectl` commands against a stored kubeconfig credential, without manually exporting `KUBECONFIG` or copying files into the container.

4. **Add the LKE kubeconfig as a Jenkins Credential**
   Added the downloaded kubeconfig file as a Jenkins credential of kind **Secret file**, with ID `lke-credentials`.

5. **Adjust the Jenkinsfile to Deploy via the Plugin**
   ```groovy
   stage('deploy') {
       steps {
           script {
               echo 'deploying docker image...'
               withKubeConfig([
                   credentialsId: 'lke-credentials',
                   serverUrl: 'https://<LKE_CLUSTER_ID>.<region>.linodelke.net'
               ]) {
                   sh 'kubectl create deployment nginx-deployment --image=nginx'
               }
           }
       }
   }
   ```
   `withKubeConfig` handles writing out the credential and pointing `kubectl` at it for the duration of the block — no manual file handling required, unlike the EKS pipeline.

   **Is `serverUrl` actually needed here?** No — not functionally. Since `lke-credentials` is a full kubeconfig file (Secret file credential), the server address is already embedded in it, and the plugin uses that as-is. `serverUrl`, when supplied alongside a full kubeconfig credential, is used purely as a **validation check**: the plugin confirms it matches the server already in the kubeconfig and skips validation entirely if omitted. It's a safety net against pointing at the wrong cluster, not a requirement — but worth keeping, since it costs nothing and catches a stale/wrong credential early. Find the real value for `<LKE_CLUSTER_ID>` under `clusters[].cluster.server` in the downloaded kubeconfig file.

6. **Run the Pipeline and Verify**
   Triggered the `deploy-to-lke` branch of the multibranch pipeline and confirmed the deployment landed on the LKE cluster via `kubectl get pods`.

## What I Learned
- LKE's kubeconfig is self-contained (embedded client cert/key) — no external authenticator binary is needed, unlike EKS's IAM-based token authentication
- The Jenkins **Kubernetes CLI Plugin** and its `withKubeConfig` step remove the need to manually copy kubeconfig files into the Jenkins container or export `KUBECONFIG` by hand
- `kubectl` itself only needs to be installed once in the Jenkins container — it's reusable across different clusters/pipelines, only the credential changes
- Comparing this demo directly against the EKS one highlights how much authentication complexity comes specifically from AWS IAM's model, not from Kubernetes or Jenkins themselves
- Managed Kubernetes offerings can differ significantly in how they handle cluster authentication, which has real implications for how much CI/CD tooling you need to install and maintain
- `withKubeConfig`'s `serverUrl` parameter behaves differently depending on credential type: **required** when the credential is a bare token/username-password/certificate (no embedded server address), but purely an **optional validation check** when the credential is already a full kubeconfig file

## Cleanup
```bash
# Remove the deployed application from the LKE cluster
kubectl --kubeconfig ./lke-kubeconfig.yaml delete deployment nginx-deployment

# Remove the lke-credentials Secret file credential via the Jenkins UI

# Delete the LKE cluster via the Linode Cloud Manager to avoid ongoing charges
```

