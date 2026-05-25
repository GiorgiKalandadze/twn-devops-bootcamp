# Module 6 — Artifact Repository Manager with Nexus

## Demo Project: Run Nexus on Droplet and Publish Artifact to Nexus

**Technologies:** Nexus · DigitalOcean · Linux · Java · Gradle · Maven

**Application sources:**
- Java Gradle App: [twn-devops-bootcamp/latest/06-nexus/java-app](https://gitlab.com/twn-devops-bootcamp/latest/06-nexus/java-app)
- Java Maven App: [twn-devops-bootcamp/latest/06-nexus/java-maven-app](https://gitlab.com/twn-devops-bootcamp/latest/06-nexus/java-maven-app)

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Install and configure Nexus from scratch on a cloud server
- Create a new user on Nexus with relevant permissions for publishing artifacts
- Build a Java Gradle project and upload the JAR to Nexus
- Build a Java Maven project and upload the JAR to Nexus

---

## Architecture

```
Local Machine                              DigitalOcean Droplet — FRA1
─────────────                              Ubuntu 24.04 LTS — 4 GB RAM
  │                                        module-6-demo-1-ubuntu-s-2vcpu-4gb-fra1
  │  Gradle / Maven build                          │
  │                                        ┌───────┴────────────┐
  │  publish (HTTP PUT)                    │ user: nexus         │
  ├────────────────────────────────────►   │ /opt/nexus          │
  │                                        │ /opt/sonatype-work  │
  │                                        └───────┬─────────────┘
  │                                                ▼
  │                                            :8081 Nexus Repository
  │                                                │
  │  Browser ◄───── http://<IP>:8081 ──────────────┘
  │
Firewall (demo-firewall)
┌─────────────────────────────────────────┐
│  TCP 22   — SSH        — your IP only   │
│  TCP 8081 — Nexus UI   — your IP only   │
└─────────────────────────────────────────┘
```

---

## Steps

### Step 1 — Create Droplet for Nexus

Nexus is JVM-based and memory-hungry. Create a fresh Droplet sized for it:

- **Image:** Ubuntu 24.04 (LTS) x64
- **Size:** s-2vcpu-4gb (4 GB RAM minimum)
- **Region:** Frankfurt (FRA1)
- **Hostname:** `module-6-demo-1-ubuntu-s-2vcpu-4gb-fra1`
- **Authentication:** SSH key

![Droplet created](./screenshots/01-droplet-created.png)

---

### Step 2 — Attach Firewall with SSH Rule

Attach the existing `demo-firewall` to the Droplet. Confirm port 22 inbound is restricted to your IP only.

![Firewall SSH rule](./screenshots/02-firewall-ssh-rule.png)

---

### Step 3 — SSH in and Install Java 17

Nexus 3.70+ requires Java 17.

```bash
ssh root@<DROPLET_IP>

apt update
apt install -y openjdk-17-jre-headless
java -version
```

![Install Java](./screenshots/03-install-java.png)

---

### Step 4 — Download and Extract Nexus

```bash
cd /opt
wget https://download.sonatype.com/nexus/3/nexus-unix-x86-64-3.78.0-14.tar.gz
tar -zxvf nexus-unix-x86-64-3.78.0-14.tar.gz
ls
```

You'll see two folders:
- `nexus-3.78.0-14/` — the Nexus binaries (read-only)
- `sonatype-work/` — runtime data, logs, repositories (writable)

Rename for cleanliness:

```bash
mv nexus-3.78.0-14 nexus
rm nexus-unix-x86-64-3.78.0-14.tar.gz
ls
```

![Nexus extracted](./screenshots/04-nexus-extracted.png)

> **Tip:** check [help.sonatype.com](https://help.sonatype.com/repomanager3/product-information/download) for the latest version before running `wget`.

---

### Step 5 — Create Dedicated `nexus` Linux User

Nexus must NOT run as root. Create a dedicated OS user and hand ownership over:

```bash
adduser nexus
chown -R nexus:nexus /opt/nexus
chown -R nexus:nexus /opt/sonatype-work
```

Tell Nexus to use this user:

```bash
vim /opt/nexus/bin/nexus.rc
```

Set:
```
run_as_user="nexus"
```

![Nexus user created](./screenshots/05-nexus-user-created.png)

---

### Step 6 — Open Port 8081 in Firewall

Add an inbound rule for Nexus UI access — restricted to your IP only (Nexus is admin-facing):

| Type | Protocol | Port | Source |
| --- | --- | --- | --- |
| SSH | TCP | 22 | Your IP only |
| Custom | TCP | 8081 | Your IP only |

![Firewall port 8081](./screenshots/06-firewall-add-port-8081.png)

---

### Step 7 — Start Nexus and Reach the UI

Switch to the `nexus` user and start the service:

```bash
su - nexus
/opt/nexus/bin/nexus start
```

Nexus takes 30–60 seconds to fully start. Once it's up, open in your browser:

```
http://<DROPLET_IP>:8081
```

![Nexus running](./screenshots/07-nexus-running.png)

---

### Step 8 — Initial Login & Setup Wizard

Click **Sign In** (top right). The initial admin password is in a file on the server:

```bash
# back on the droplet, as the nexus user
cat /opt/sonatype-work/nexus3/admin.password
```

Copy the password. In the browser:
1. Username: `admin`, paste the password
2. Set a new admin password
3. Choose **Disable Anonymous Access** (security best practice)

![Nexus initial login](./screenshots/08-nexus-initial-login.png)

---

### Step 9 — Create New Nexus Role for Publishing

**Settings (gear icon) → Security → Roles → Create role → Nexus role**

- **Role ID:** `nx-deployment`
- **Role name:** `nx-deployment`
- **Description:** Permissions to deploy artifacts to maven-snapshots

Add this privilege:
- `nx-repository-view-maven2-maven-snapshots-*`

Save.

![Create role](./screenshots/10-create-role.png)

---

### Step 10 — Create New Nexus User

**Settings → Security → Users → Create local user**

- **ID:** `developer`
- **First name:** Developer
- **Last name:** User
- **Email:** `developer@example.com`
- **Password:** (set a strong one — store it safely; you'll use it in build files)
- **Status:** Active
- **Roles:** assign `nx-deployment`

Save.

![Create user](./screenshots/11-create-user.png)

---

### Step 11 — Build Gradle Project & Upload to Nexus

On your **local machine**, clone the Gradle app:

```bash
git clone https://gitlab.com/twn-devops-bootcamp/latest/06-nexus/java-app.git
cd java-app
```

Open `build.gradle` and add the publishing configuration. The plugins block should include `maven-publish`:

```groovy
plugins {
    id 'java'
    id 'maven-publish'
}
```

Then at the bottom of the file:

```groovy
publishing {
    publications {
        maven(MavenPublication) {
            groupId = 'com.example'
            artifactId = 'my-app'
            version = '1.0-SNAPSHOT'
            from components.java
        }
    }
    repositories {
        maven {
            name = 'nexus'
            url = "http://<DROPLET_IP>:8081/repository/maven-snapshots/"
            allowInsecureProtocol = true
            credentials {
                username = project.findProperty('nexusUsername') ?: ''
                password = project.findProperty('nexusPassword') ?: ''
            }
        }
    }
}
```

To keep credentials out of the project, put them in `~/.gradle/gradle.properties` (your user home, not the project):

```properties
nexusUsername=developer
nexusPassword=<your-nexus-password>
```

Then build and publish:

```bash
./gradlew build
./gradlew publish
```

---

### Step 12 — Verify Gradle Artifact in Nexus

In the Nexus UI: **Browse → maven-snapshots → com → example → my-app → 1.0-SNAPSHOT/**

You should see the JAR uploaded.

![Nexus Gradle artifact](./screenshots/13-nexus-gradle-artifact.png)

---

### Step 13 — Clone Maven Project Locally

On your local machine:

```bash
git clone https://gitlab.com/twn-devops-bootcamp/latest/06-nexus/java-maven-app.git
cd java-maven-app
```

---

### Step 14 — Configure `pom.xml` for Nexus Deployment

Open `pom.xml` and add a `<distributionManagement>` block as a direct child of `<project>`:

```xml
<distributionManagement>
    <snapshotRepository>
        <id>nexus-snapshots</id>
        <url>http://<DROPLET_IP>:8081/repository/maven-snapshots/</url>
    </snapshotRepository>
</distributionManagement>
```

This tells Maven where to push the artifact when running `mvn deploy` on a SNAPSHOT version. The `<id>` is a label — it must match the `<id>` used in `~/.m2/settings.xml` for credentials.

![pom.xml distributionManagement](./screenshots/14-pom-distribution-management.png)

---

### Step 15 — Configure Maven Credentials in `~/.m2/settings.xml`

Maven's user-level config (`~/.m2/settings.xml`) holds credentials. It lives in your user home, **not** in the project, so it's never committed to Git.

```bash
mkdir -p ~/.m2
vim ~/.m2/settings.xml
```

Add:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0">
  <servers>
    <server>
      <id>nexus-snapshots</id>
      <username>developer</username>
      <password>your-nexus-password</password>
    </server>
  </servers>
</settings>
```

The `<id>` here must exactly match the `<id>` in `pom.xml`'s `<snapshotRepository>` — that's how Maven links the destination URL (from `pom.xml`) to the credentials for it (from `settings.xml`).

---

### Step 16 — Build and Deploy the Maven Artifact

```bash
mvn package
mvn deploy
```

- `mvn package` — compiles and produces the JAR in `target/`
- `mvn deploy` — runs `package`, then uploads the JAR to the Nexus URL from `distributionManagement`

Expected output ends with `BUILD SUCCESS` and an upload line like:
```
Uploading: http://<DROPLET_IP>:8081/repository/maven-snapshots/com/example/java-maven-app/1.1.0-SNAPSHOT/...
```

---

### Step 17 — Verify Maven Artifact in Nexus

In the Nexus UI: **Browse → maven-snapshots → com → example → java-maven-app → 1.1.0-SNAPSHOT/**

Both Gradle and Maven artifacts now live side by side in the same `maven-snapshots` repository.

![Nexus Maven artifact](./screenshots/17-nexus-maven-artifact.png)

---

## What I Learned

- How to install and configure Nexus Repository Manager from scratch on a cloud server
- Why Nexus must run as a dedicated non-root OS user (security + permission management)
- The difference between Nexus repository types: **proxy** (caches remote repos like Maven Central), **hosted** (your own artifacts), **group** (combines multiple repos behind a single URL)
- The difference between `maven-snapshots` (mutable, dev builds) and `maven-releases` (immutable, production builds)
- How to create Nexus roles with fine-grained privileges (`nx-repository-view-maven2-maven-snapshots-*`) and assign them to users — principle of least privilege
- How to configure a Gradle project with the `maven-publish` plugin to push artifacts to a remote repository
- How to keep Nexus credentials out of project source by storing them in `~/.gradle/gradle.properties`
- The role of `~/.m2/`: Maven's user-home directory. Contains `repository/` (a local cache of every downloaded JAR, reused across all your Maven projects) and `settings.xml` (your personal Maven config — credentials, mirrors, proxies)
- The difference between project-level config (`pom.xml`, committed to Git) and user-level config (`~/.m2/settings.xml`, never committed). `pom.xml` declares *where* to publish; `settings.xml` declares *how to authenticate*
- How the `<id>` field links `pom.xml`'s `distributionManagement` to `settings.xml`'s `servers` — by name match, not URL match

---

## Cleanup

Nexus runs continuously and consumes resources — destroy the Droplet when done:

```bash
# stop nexus first
su - nexus
/opt/nexus/bin/nexus stop
```

Then destroy the Droplet in the DigitalOcean dashboard.