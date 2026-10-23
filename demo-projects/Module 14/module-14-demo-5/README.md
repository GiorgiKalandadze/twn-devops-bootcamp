# Website Monitoring and Recovery

A Python script that checks a website running in a Docker container on a Linode server every 5 minutes. If the site is down, it sends an email and tries to recover it automatically.

| Situation | What the script does |
|-----------|----------------------|
| Site returns `200` | Prints a success message |
| Site returns another status code | Sends an email and restarts the container over SSH |
| Site is not reachable at all | Sends an email, reboots the Linode, waits until it is `running`, then restarts the container over SSH |

**Note:** The script reboots the server when the site is unreachable. Only point it at a server you are fine with restarting.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
```

The Linode server needs Docker installed and the app running as a container, for example:

```bash
docker run -d -p 8080:80 nginx
```

Set the environment variables:

```bash
export EMAIL_ADDRESS=<EMAIL_ADDRESS>
export EMAIL_PASSWORD=<GMAIL_APP_PASSWORD>
export LINODE_TOKEN=<LINODE_API_TOKEN>
export APP_HOSTNAME=<LINODE_IP>
export LINODE_ID=<LINODE_ID>
export CONTAINER_ID=<CONTAINER_ID>
export SSH_KEY_PATH=~/.ssh/id_rsa      # optional, this is the default
```

`EMAIL_PASSWORD` must be a Gmail App Password, not your normal account password.

## Running

```bash
python monitor-website.py
```

The script keeps running and checks the site every 5 minutes. Stop it with `Ctrl+C`.

To test the recovery, stop the container on the server and wait for the next check:

```bash
ssh root@<LINODE_IP> "docker stop <CONTAINER_ID>"
```

## Configuration

Check interval and URL (`monitor-website.py`):

```python
schedule.every(5).minutes.do(monitor_application)
response = requests.get(f'http://{APP_HOSTNAME}:8080/', timeout=10)
```

Email server (Gmail):

```python
smtplib.SMTP('smtp.gmail.com', 587)
```

SSH user used to restart the container:

```python
ssh.connect(hostname=APP_HOSTNAME, username='root', key_filename=SSH_KEY_PATH)
```

## Example Output

Site is healthy:

```text
Application is running successfully!
```

Site returns an error status:

```text
Application Down. Fix it!
Sending an email...
Restarting the application...
```

Site is not reachable at all:

```text
Connection error happened: HTTPConnectionPool(host='<LINODE_IP>', port=8080): ...
Sending an email...
Rebooting the server...
Restarting the application...
```

In both failure cases the email has the subject `SITE DOWN` and is sent to `EMAIL_ADDRESS`.

## Cleanup

- Delete the Linode server in Cloud Manager
- Revoke the Linode API token
- Revoke the Gmail App Password