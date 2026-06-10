# Module 8 — CI/CD with Jenkins

## Demo Project: Trigger Jenkins Pipeline with GitLab Webhook

**Technologies:** Jenkins · GitLab · Docker · Linux · Git · Java · Maven

**Application source:** [twn-java-maven-app](https://gitlab.com/giorgikalandadze24/twn-java-maven-app)

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Install the **GitLab** plugin (for single Pipeline jobs) and the **Multibranch Scan Webhook Trigger** plugin (required for Multibranch Pipeline jobs) in Jenkins
- Configure a GitLab API connection in Jenkins using a Personal Access Token
- Enable the "Scan by webhook" trigger on the Multibranch Pipeline job with a named token
- Register the webhook in the GitLab app repo using the Multibranch Scan Webhook Trigger URL
- Push a commit and verify Jenkins triggers automatically — no manual builds, no polling delays
- Confirm both `main` and `dev` branches trigger independent pipeline runs

---

## Architecture

```
  Developer
      │
      │  git push
      ▼
  GitLab — twn-java-maven-app
      │
      │  POST webhook
      │  http://<DROPLET_IP>:8080/multibranch-webhook-trigger/invoke?token=gitlabtoken
      ▼
  Jenkins (Droplet :8080)
  └── java-maven-multibranch (Multibranch Pipeline)
        │  scans repo, builds the branch that changed
        │
        ├── main branch pipeline
        │     ├── build jar   → buildJar()
        │     ├── build image → buildImage('kala24/java-maven-app:1.0')
        │     └── deploy      → echo deploying  ✓ runs
        │
        └── dev branch pipeline
              ├── build jar   → buildJar()
              ├── build image → buildImage('kala24/java-maven-app:1.0')
              └── deploy      → skipped (BRANCH_NAME != 'main')
                    │
                    ▼
            DockerHub  kala24/java-maven-app:1.0
```

---

## Steps

### Step 1 — Install GitLab Plugin

**Manage Jenkins → Plugins → Available plugins** → search `gitlab` → select **GitLab** → **Install without restart**.

This plugin adds webhook trigger support for standard Pipeline jobs and enables the GitLab API connection configured in Step 3.

---

### Step 2 — Install Multibranch Scan Webhook Trigger Plugin

**Manage Jenkins → Plugins → Available plugins** → search `multibranch scan` → select **Multibranch Scan Webhook Trigger** → **Install without restart**.

The GitLab plugin alone does not support Multibranch Pipeline jobs. This separate plugin exposes the `/multibranch-webhook-trigger/invoke?token=<token>` endpoint used in this demo.

---

### Step 3 — Configure GitLab API Connection in Jenkins

**Manage Jenkins → System → GitLab → Add**

| Field            | Value                  |
|------------------|------------------------|
| Connection name  | `gitlab-conn`          |
| GitLab host URL  | `https://gitlab.com`   |
| Credentials      | `gitlab-api-token` (add below) |

To add the credential click **Add** next to Credentials:

| Field     | Value                                         |
|-----------|-----------------------------------------------|
| Kind      | GitLab API token                              |
| API token | GitLab Personal Access Token with `api` scope |
| ID        | `gitlab-api-token`                            |

Click **Test Connection** — confirm it shows **Success**. Click **Save**.


---

### Step 4 — Configure Webhook Trigger on the Multibranch Job

Open `java-maven-multibranch` → **Configuration** → **Scan Multibranch Pipeline Triggers**

- Check: **Scan by webhook**
- Trigger token: `gitlabtoken`
- Click the **?** icon to reveal the full webhook URL:
  `http://<DROPLET_IP>:8080/multibranch-webhook-trigger/invoke?token=gitlabtoken`

Click **Save**.

---

### Step 5 — Register the Webhook in GitLab

GitLab → **twn-java-maven-app** → **Settings → Webhooks → Add new webhook**

| Field            | Value                                                                             |
|------------------|-----------------------------------------------------------------------------------|
| URL              | `http://<DROPLET_IP>:8080/multibranch-webhook-trigger/invoke?token=gitlabtoken`  |
| Trigger          | Push events                                                                       |
| SSL verification | Disabled (Jenkins runs on HTTP)                                                   |

Click **Add webhook**.

---

### Step 6 — Test the Webhook

Make a small commit in the app repo and push:

```bash
git commit --allow-empty -m "test webhook trigger"
git push origin main
```

Jenkins starts the `java-maven-multibranch` scan within seconds. Check the build history — the run should show **by remote host**, not **by user**.

---

### Step 7 — Verify Both Branches Trigger Independently

Push a commit to the `dev` branch:

```bash
git checkout dev
git commit --allow-empty -m "test webhook on dev"
git push origin dev
```

Confirm in Jenkins:
- `main` pipeline — all three stages including `deploy` ✓
- `dev` pipeline — `deploy` stage skipped ✓

---

## What I Learned

- **Webhook vs polling** — a webhook fires the moment a push happens (event-driven, instant, zero wasted resources); periodic scanning polls on a schedule and burns resources even when nothing changed
- **Two plugins, two URL formats** — the GitLab plugin handles single Pipeline jobs at `/project/<jobname>`; the Multibranch Scan Webhook Trigger plugin handles Multibranch jobs at `/multibranch-webhook-trigger/invoke?token=<token>`; using the wrong URL for the wrong job type silently does nothing
- **Token in the URL is not a secret** — it identifies which job to trigger, not who is allowed to call it; anyone with the URL can fire a scan, so treat it as semi-sensitive
- **Two separate GitLab credentials** — `gitlab-credential` is a username/password used by Jenkins to clone the repo over HTTPS; `gitlab-api-token` is a GitLab API token (different Kind in Jenkins) used by the GitLab plugin for the API connection — they serve different purposes and cannot be swapped
- **SSL verification disabled** because Jenkins runs on plain HTTP on the Droplet — acceptable for a bootcamp environment, never for production (production Jenkins should sit behind a reverse proxy with a valid TLS certificate)
- **One webhook, all branches** — the Multibranch Scan Webhook Trigger fires a repo scan on every push; Jenkins builds only the branch that changed, so a single webhook covers the entire repo automatically

---

## Cleanup

> **Keep the Jenkins Droplet running for the rest of Module 8.**

When Module 8 is fully done:

```bash
docker stop jenkins && docker rm jenkins
docker volume rm jenkins_home
```

Then destroy the Droplet from the DigitalOcean console.

---

