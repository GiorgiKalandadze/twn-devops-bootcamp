# Module 9 — AWS Services

## Demo Project: Complete the CI/CD Pipeline — Dynamic Versioning + Docker Compose Deploy

**Technologies:** AWS (EC2, Security Groups) · Jenkins · Docker · Docker Compose · Linux · Git · Java · Maven · DockerHub

**Application source:** [twn-java-maven-app](https://gitlab.com/giorgikalandadze24/twn-java-maven-app)

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Combine dynamic versioning (Module 8 Demo 5) with Docker Compose deployment to EC2 (Module 9 Demo 3) into one complete CI/CD pipeline
- Auto-increment the app version on every build and tag the image with `<version>-<BUILD_NUMBER>`
- Build the JAR, build the image, and push it to DockerHub with the dynamic tag
- Deploy to EC2 via Docker Compose, injecting the dynamic image tag at deploy time
- Commit the version bump back to GitLab after a successful deploy
- Prevent the infinite build loop with the Ignore Committer Strategy plugin

---

## Architecture

```
  Developer
      │
      │  git push (master)
      ▼
  GitLab — twn-java-maven-app  ◄──────────────────────────────┐
      │                                                        │
      │  webhook POST                                          │
      ▼                                            commit version
  Jenkins — DigitalOcean Droplet (Docker container)    git push pom.xml
  java-maven-multibranch pipeline                              │
      │                                                        │
      ├─ increment version   mvn parse-version → IMAGE_TAG = <version>-<BUILD_NUMBER>
      ├─ build jar           mvn clean package
      ├─ build image         docker build + push  → DockerHub  kala24/java-maven-app:1.1.1-5
      │
      ├─ deploy  (master only)
      │     scp :22  docker-compose.yml + server-cmds.sh
      │     ssh :22  bash server-cmds.sh <IMAGE_TAG>
      │        │
      │        ▼
      │   ┌──────────────────────────────────────────────┐
      │   │  EC2 — eu-north-1 — Amazon Linux 2            │
      │   │   docker-compose pull / up --force-recreate   │
      │   │   ┌─────────────────────────────┐             │
      │   │   │ container :8080             │ ◄──── Browser  HTTP :8080
      │   │   └─────────────────────────────┘             │
      │   └──────────────────────────────────────────────┘
      │
      └─ commit version  (master only)
            git commit -m "jenkins: version bump"
            git push origin HEAD:master  ──────────────────────┘
                  │
                  │  webhook fires again — but...
                  ▼
            Ignore Committer Strategy
            (jenkins@example.com blocked → no rebuild)
```

---

## Steps

### Step 1 — Extend the Jenkinsfile to a Complete CI/CD Pipeline

Build out the full pipeline with five stages — versioning, build, image, deploy, and commit:

```groovy
@Library('jenkins-shared-library') _

pipeline {
    agent any
    tools {
        maven 'Maven'
    }
    stages {
        stage('increment version') {
            steps {
                script {
                    sh 'mvn build-helper:parse-version versions:set \
                        -DnewVersion=\${parsedVersion.majorVersion}.\${parsedVersion.minorVersion}.\${parsedVersion.nextIncrementalVersion} \
                        versions:commit'
                    def version = sh(
                        script: 'mvn help:evaluate -Dexpression=project.version -q -DforceStdout',
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "$version-$BUILD_NUMBER"
                }
            }
        }
        stage('build jar') {
            steps {
                script {
                    buildJar()
                }
            }
        }
        stage('build image') {
            steps {
                script {
                    buildImage("kala24/java-maven-app:${IMAGE_TAG}")
                }
            }
        }
        stage('deploy') {
            when {
                expression { BRANCH_NAME == 'master' }
            }
            steps {
                script {
                    def ec2Instance = "ec2-user@<EC2_PUBLIC_IP>"
                    sshagent(['ec2-server-key']) {
                        sh "scp -o StrictHostKeyChecking=no docker-compose.yml ${ec2Instance}:/home/ec2-user"
                        sh "scp -o StrictHostKeyChecking=no server-cmds.sh ${ec2Instance}:/home/ec2-user"
                        sh "ssh -o StrictHostKeyChecking=no ${ec2Instance} 'bash server-cmds.sh kala24/java-maven-app:${IMAGE_TAG}'"
                    }
                }
            }
        }
        stage('commit version') {
            when {
                expression { BRANCH_NAME == 'master' }
            }
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'gitlab-credential', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh "git remote set-url origin https://${USER}:${PASS}@gitlab.com/giorgikalandadze24/twn-java-maven-app.git"
                        sh 'git add .'
                        sh 'git commit -m "jenkins: version bump"'
                        sh 'git push origin HEAD:master'
                    }
                }
            }
        }
    }
}
```

Key points:
- `IMAGE_TAG` is set in `increment version` and persists across all later stages
- `deploy` and `commit version` are restricted to the `master` branch
- `commit version` runs **last** so the bump is only pushed after a successful deploy

---

### Step 2 — Make `docker-compose.yml` Use the Dynamic Tag

The Compose file reads the image from an `${IMAGE}` variable so the tag isn't hardcoded — it's injected at deploy time:

```yaml
services:
  java-maven-app:
    image: ${IMAGE}
    ports:
      - "8080:8080"
```

This lets the same Compose file deploy any build's image without editing it each time.

---

### Step 3 — Update `server-cmds.sh` to Pass the Tag Through

The script takes the image tag as `$1`, exports it as `IMAGE` for Compose, and frees port 8080 before redeploying:

```bash
#!/usr/bin/env bash
export IMAGE=$1

# stop any container currently bound to port 8080 to avoid a port conflict
docker ps -q --filter "publish=8080" | xargs -r docker stop

docker-compose -f docker-compose.yml pull
docker-compose -f docker-compose.yml up --detach --force-recreate
```

- `$1` is the dynamic image tag passed by Jenkins (e.g. `kala24/java-maven-app:1.1.1-5`)
- `export IMAGE` makes the tag available to `docker-compose.yml`'s `${IMAGE}`
- Stopping the container on port 8080 first prevents a bind conflict on redeploy

---

### Step 4 — Push to Master and Trigger the Pipeline

Commit and push all changes — `Jenkinsfile`, `docker-compose.yml`, and `server-cmds.sh` — to the `master` branch. The webhook fires and triggers the full `java-maven-multibranch` pipeline automatically.

---

### Step 5 — Watch the Full Pipeline Run

All five stages run green, end to end:

```
increment version → build jar → build image → deploy → commit version
```

![Pipeline all stages green](screenshots/01-pipeline-all-stages-green.png)

---

### Step 6 — Verify the Dynamic Tag on DockerHub

DockerHub shows a new image tag combining version and build number, e.g. `1.1.1-5`.

![DockerHub dynamic tag](screenshots/02-dockerhub-dynamic-tag.png)

---

### Step 7 — Verify the Version Bump on GitLab

GitLab shows a new `jenkins: version bump` commit from the `jenkins` user — and **no second pipeline is triggered**, because the Ignore Committer Strategy plugin blocks builds from `jenkins@example.com`, breaking the loop.

![GitLab version bump commit](screenshots/03-gitlab-version-bump-commit.png)

---

### Step 8 — Verify the App in the Browser

```
http://<EC2_PUBLIC_IP>:8080
```

The freshly versioned image, deployed via Docker Compose, is serving from EC2.

---

## What I Learned

- How to combine **CI** (auto-versioning, build, image push) and **CD** (Compose deploy to EC2) into a single end-to-end pipeline
- How an `${IMAGE}` variable in `docker-compose.yml` — fed by the tag passed into `server-cmds.sh` — enables **dynamic deployment** without editing the Compose file on every build
- Why the **commit version** stage must run last: the version bump is only pushed back to GitLab after the deploy succeeds, so a failed deploy never bumps the version
- Why the **Ignore Committer Strategy** plugin is essential: Jenkins' own `version bump` commit fires the webhook again, and ignoring `jenkins@example.com` prevents an infinite build loop
- How environment variables like `IMAGE_TAG` set in one stage **persist across all later stages** in a Jenkins pipeline

---

## Cleanup

Stop and remove the containers on EC2 when done:

```bash
docker-compose down
```
