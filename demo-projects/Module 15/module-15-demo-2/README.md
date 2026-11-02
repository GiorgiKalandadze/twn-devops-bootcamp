# Ansible: Automate Nexus Deployment

An Ansible playbook that installs and starts Nexus Repository Manager on a fresh Ubuntu droplet. It runs in five plays:

| Play | What it does |
|------|--------------|
| Install java and net-tools | Updates the apt cache and installs Java 17 (needed by Nexus) and `net-tools` (for the port check) |
| Download and unpack Nexus installer | Downloads the latest Nexus archive to `/opt`, unpacks it, and renames the folder to `/opt/nexus` |
| Create nexus user to own nexus folder | Creates the `nexus` group and user and makes it the owner of `/opt/nexus` and `/opt/sonatype-work` |
| Start nexus with nexus user | Sets `run_as_user="nexus"` in `nexus.rc` and starts Nexus as that user |
| Verify nexus running | Checks the process with `ps`, waits one minute, then lists the listening ports with `netstat` |

**Note:** The download URL always points to the latest Nexus version, so the version you get depends on when you run the playbook.

## Setup

1. Create a droplet on DigitalOcean (Ubuntu) and add your SSH key. Nexus needs a lot of memory, so use a droplet with at least 4 GB RAM. Note its public IP.

2. Put the droplet IP in the `hosts` file together with the connection details. The group name must be `nexus_server`, because the playbook uses it:

```text
[nexus_server]
<DROPLET_IP> ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa
```

3. Check that Ansible can reach the droplet:

```bash
ansible all -i hosts -m ping
```

## Running

```bash
ansible-playbook -i hosts deploy-nexus.yaml
```

The playbook runs once and exits. Nexus keeps running on the droplet.

Nexus listens on port 8081. Open `http://<DROPLET_IP>:8081` in the browser. Port 8081 must be open in the droplet's firewall. Nexus takes a few minutes to start, so the page may not load right away.

To sign in as `admin`, read the initial password on the droplet:

```bash
cat /opt/sonatype-work/nexus3/admin.password
```

## Configuration

Group of hosts the plays run on (`deploy-nexus.yaml` and `hosts`):

```yaml
hosts: nexus_server
```

Nexus archive and install folder:

```yaml
url: https://download.sonatype.com/nexus/3/latest-linux-x86_64.tar.gz
dest: /opt/
```

User that owns and runs Nexus:

```yaml
name: nexus
line: run_as_user="nexus"
```

The unpack and rename tasks only run when `/opt/nexus` does not exist yet (`when: not stat_result.stat.exists`), so the playbook can be run again without overwriting the install.


The first `debug` task prints the output of `ps aux | grep nexus`. A line owned by `nexus` that runs Java means Nexus is running.

The second `debug` task prints the listening ports. A `java` process listening on port `8081` means Nexus is ready.

## Cleanup

- Destroy the droplet in the DigitalOcean console
- Remove the IP from `hosts`