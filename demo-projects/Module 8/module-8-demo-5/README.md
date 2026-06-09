# Module 8 — CI/CD with Jenkins

## Demo Project: Automated Versioning in CI Pipeline

**Technologies:** Jenkins · GitLab · Docker · Linux · Git · Java · Maven · Groovy

**Application source:** [twn-java-maven-app](https://gitlab.com/giorgikalandadze24/twn-java-maven-app)

**Shared library:** [twn-jenkins-shared-library](https://gitlab.com/giorgikalandadze24/twn-jenkins-shared-library)

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Add an "increment version" stage that auto-bumps the patch version in `pom.xml` using `maven-versions-plugin` before every build
- Read the new version back from Maven and compose a unique image tag: `<version>-<BUILD_NUMBER>`
- Update `vars/buildJar.groovy` to run `mvn clean package` so only one JAR exists in `target/`, allowing the Dockerfile to use a wildcard `COPY`
- Update the Dockerfile to copy and run the JAR using a wildcard — version is no longer hardcoded anywhere
- Push the Docker image to DockerHub with the dynamic version tag
- Add a "commit version" stage that pushes the `pom.xml` version bump back to GitLab after a successful build
- Install the **Ignore Committer Strategy** plugin and configure it to ignore Jenkins' own version-bump commits, preventing an infinite build loop

---

## Architecture

```
  Developer
      │
      │  git push (real code change)
      ▼
  GitLab — twn-java-maven-app
      │
      │  webhook POST → Jenkins
      ▼
  java-maven-multibranch pipeline
      │
      ├─ increment version
      │     mvn build-helper:parse-version versions:set ...
      │     IMAGE_TAG = <version>-<BUILD_NUMBER>  e.g. 1.0.3-12
      │
      ├─ build jar
      │     mvn clean package  (single JAR in target/)
      │
      ├─ build image
      │     docker build -t kala24/java-maven-app:${IMAGE_TAG} .
      │     docker push
      │     → DockerHub  kala24/java-maven-app:1.0.3-12
      │
      ├─ commit version
      │     git commit -m "jenkins: version bump"
      │     git push origin HEAD:main
      │         │
      │         │  webhook fires again — but...
      │         ▼
      │     Ignore Committer Strategy
      │     (jenkins@example.com blocked → no build triggered)
      │
      └─ deploy  (main branch only)
            echo 'deploying to production...'
```

---

## Steps

### Step 1 — Configure Git Identity on the Jenkins Container

Jenkins needs a git identity to commit the version bump. Run this once on the Droplet:

```bash
docker exec -it jenkins bash
git config --global user.email "jenkins@example.com"
git config --global user.name "jenkins"
exit
```

---

### Step 2 — Update `vars/buildJar.groovy` in the Shared Library

Change `mvn package` to `mvn clean package`:

```groovy
def call() {
    sh 'mvn clean package'
}
```

`clean` empties `target/` before building. This ensures only one JAR exists, which lets the Dockerfile copy it with a wildcard without knowing the exact version string.

Commit and push to the shared library repo.

---

### Step 3 — Update the Dockerfile in the App Repo

The version is no longer hardcoded — update the Dockerfile to use a wildcard:

```dockerfile
FROM openjdk:8-jre-alpine
EXPOSE 8080
RUN mkdir -p /usr/app
WORKDIR /usr/app
COPY ./target/java-maven-app-*.jar /usr/app/
ENTRYPOINT ["sh", "-c", "java -jar /usr/app/java-maven-app-*.jar"]
```

`mvn clean package` guarantees a single match for the wildcard. Commit this change to the app repo.

---

### Step 4 — Install Ignore Committer Strategy Plugin

**Manage Jenkins → Plugins → Available plugins** → search `ignore committer` → select **Ignore Committer Strategy** → **Install without restart**.

This plugin is needed to break the build loop caused by Jenkins' own version-bump commit firing the webhook again.

---

### Step 5 — Configure Ignore Committer Strategy on the Multibranch Job

Open `java-maven-multibranch` → **Configuration** → **Branch Sources → Git → Build strategies → Add strategy → Ignore Committer Strategy**

- Ignored committer email: `jenkins@example.com`
- Check: **Allow builds when a changeset contains non-ignored author(s)**

Click **Save**.

---

### Step 6 — Update the Jenkinsfile

Replace the app's `Jenkinsfile` with the full versioned pipeline:

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
        stage('commit version') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'gitlab-credential', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                        sh "git remote set-url origin https://${USER}:${PASS}@gitlab.com/giorgikalandadze24/twn-java-maven-app.git"
                        sh 'git add .'
                        sh 'git commit -m "jenkins: version bump"'
                        sh 'git push origin HEAD:main'
                    }
                }
            }
        }
        stage('deploy') {
            when {
                expression { BRANCH_NAME == 'main' }
            }
            steps {
                echo 'deploying to production...'
            }
        }
    }
}
```

Key points:
- `IMAGE_TAG` set in `increment version` is available in all later stages — env vars persist across stages
- `git push origin HEAD:main` is required because Jenkins checks out a detached commit (not a branch), so `git push origin main` would fail
- The `commit version` stage runs after build + push, so the version bump is only committed if the build succeeded

Commit and push the updated Jenkinsfile to the app repo.

---

### Step 7 — Run the Pipeline and Verify

Trigger a build by pushing any change to the app repo. Confirm:

- `increment version` stage bumped the patch version in `pom.xml`
- DockerHub shows a new tag like `1.0.3-12` (version + build number)
- GitLab shows a new commit `jenkins: version bump` from the `jenkins` user
- No second build is triggered (Ignore Committer Strategy blocks the loop)

---

## What I Learned

- **`maven-versions-plugin` + `parsedVersion`** — `build-helper:parse-version` splits the current version into components (`majorVersion`, `minorVersion`, `nextIncrementalVersion`), and `versions:set` writes the new value back to `pom.xml`; `versions:commit` removes the backup file
- **`mvn help:evaluate -DforceStdout`** reads the version back cleanly from `pom.xml` — more reliable than regex-parsing the file directly; `-q` suppresses all Maven output so only the version string is returned
- **`IMAGE_TAG = version + BUILD_NUMBER`** produces a unique, traceable tag on every build (e.g. `1.0.3-12`); `BUILD_NUMBER` is a Jenkins built-in env var, always unique per pipeline run
- **`mvn clean package`** empties `target/` before building so only one JAR exists — this is what makes the Dockerfile wildcard `COPY ./target/java-maven-app-*.jar` unambiguous; without `clean`, old versioned JARs accumulate and the wildcard matches multiple files
- **`git push origin HEAD:main`** is required when Jenkins checks out in detached HEAD state (no branch reference); `HEAD:main` pushes the current commit to the `main` branch explicitly
- **Credentials injected into the remote URL** via `withCredentials` — the token is scoped to the block and never appears in logs or the Jenkinsfile
- **The commit loop problem** — the version-bump push fires the webhook, which would trigger another build; for Multibranch jobs the solution is the **Ignore Committer Strategy** plugin (ignores commits from `jenkins@example.com`); for single Pipeline jobs the equivalent is "Polling ignores commits from certain users" in Git Additional Behaviours
- **env vars set in one stage persist across all later stages** — `env.IMAGE_TAG` set in `increment version` is readable in `build image` and `commit version` without passing it explicitly

---

## Cleanup

> **Keep the Jenkins Droplet running for the rest of Module 8.**

When Module 8 is fully done:

```bash
docker stop jenkins && docker rm jenkins
docker volume rm jenkins_home
```

Then destroy the Droplet from the DigitalOcean console.
