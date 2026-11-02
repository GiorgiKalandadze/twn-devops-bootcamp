# Ansible Integration in Terraform

Terraform creates a VPC and two EC2 instances on AWS. As soon as the servers exist, Terraform runs an Ansible playbook against them, so they are configured automatically in a single `terraform apply`. The playbook installs Docker and Docker Compose and starts an nginx container from the image on Docker Hub.

| Part | What it does |
|------|--------------|
| `terraform/main.tf` | Creates the VPC, subnet, internet gateway, route table, security group, key pair and two EC2 instances (Amazon Linux 2023) |
| `null_resource` + `local-exec` | Runs `ansible-playbook` on your computer after both servers are created |
| Wait for SSH connection | Waits until port 22 on each server accepts connections |
| Install Docker | Installs Docker (and `acl`) with `yum` and starts the Docker daemon |
| Create new linux user | Creates the `devops` user in the `adm` and `docker` groups |
| Install Docker-compose | As `devops`: downloads the Docker Compose plugin that matches the server's architecture |
| Start docker containers | As `devops`: copies `docker-compose.yaml`, logs in to Docker Hub and starts the containers |

**Note:** Ansible runs on your computer, so Ansible and the `community.docker` collection must be installed locally. The playbook needs your Docker Hub password or access token in `ansible/project-vars`, which is excluded from git.

## Setup

1. The compose file uses the image `kala24/nginx-app:1.0` from the previous demo. It must already be pushed to Docker Hub.

2. Create `ansible/project-vars` from the example and add your Docker Hub password or access token:

```bash
cd ansible
cp project-vars.example project-vars
```

```text
docker_password: <DOCKERHUB_PASSWORD_OR_ACCESS_TOKEN>
```

3. Create `terraform/terraform.tfvars` from the example and fill in your values:

```bash
cd ../terraform
cp terraform.tfvars.example terraform.tfvars
```

`my_ip` is the address that may connect with SSH, written as `<YOUR_PUBLIC_IP>/32`. You can look up your public IP with `curl ifconfig.me`. `public_key_location` is your public key and `ssh_key_private` is the matching private key.

## Running

```bash
cd terraform
terraform init
terraform apply
```

Terraform creates the servers, waits until they exist, then starts the playbook. The Ansible output appears in the same terminal. The whole run takes a few minutes.

When it finishes, open both servers in the browser:

```text
http://<ec2-public_ip_1>:8080
http://<ec2-public_ip_2>:8080
```

The IPs are printed as outputs at the end of `terraform apply`. You can show them again with `terraform output`.

The playbook runs again only when the servers' public IPs change. To run it again by hand against the same servers:

```bash
cd ansible
ansible-playbook --inventory <IP_1>,<IP_2>, --private-key ~/.ssh/id_ed25519 --user ec2-user deploy-docker.yaml
```

## Configuration

The provisioner that connects Terraform to Ansible (`terraform/main.tf`):

```hcl
resource "null_resource" "configure_servers" {
  triggers = {
    trigger = "${aws_instance.myapp-server-one.public_ip},${aws_instance.myapp-server-two.public_ip}"
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/../ansible"
    command = "ansible-playbook --inventory ${aws_instance.myapp-server-one.public_ip},${aws_instance.myapp-server-two.public_ip}, --private-key ${var.ssh_key_private} --user ec2-user deploy-docker.yaml"
    environment = {
      ANSIBLE_HOST_KEY_CHECKING = "False"
    }
  }
}
```

- The inventory is passed on the command line as a comma-separated list of IPs, so no `hosts` file is needed.
- The `null_resource` depends on both instances through their IPs, so Ansible starts only after the servers exist.
- Host key checking is turned off for this run because the servers are brand new and their keys are not in `known_hosts`. This is only suitable for a demo.

The first play waits for SSH before the other plays start, because a new EC2 instance is "running" before its SSH service accepts connections:

```yaml
wait_for:
  port: 22
  delay: 10
  timeout: 100
  search_regex: OpenSSH
```

Image and port (`ansible/docker-compose.yaml`). The security group opens port 8080, so the container's port 80 is mapped to 8080:

```yaml
image: kala24/nginx-app:1.0
ports:
  - "8080:80"
```

SSH is allowed only from `my_ip`. If your public IP changes, update `my_ip` and apply again.

## Example Output

Terraform creates the resources and then starts Ansible:

```text
null_resource.configure_servers: Creating...
null_resource.configure_servers (local-exec): Executing: ["/bin/sh" "-c" "ansible-playbook --inventory ..."]
null_resource.configure_servers (local-exec): PLAY [Wait for SSH connection] *****************************
null_resource.configure_servers (local-exec): PLAY [Install Docker] **************************************
null_resource.configure_servers (local-exec): PLAY [Create new linux user] *******************************
null_resource.configure_servers (local-exec): PLAY [Install Docker-compose] ******************************
null_resource.configure_servers (local-exec): PLAY [Start docker containers] *****************************
null_resource.configure_servers: Creation complete
```

At the end Terraform prints the outputs:

```text
Apply complete! Resources: ... added, 0 changed, 0 destroyed.

Outputs:

aws-ami_id = "ami-..."
ec2-public_ip_1 = "<IP_1>"
ec2-public_ip_2 = "<IP_2>"
```

## Cleanup

```bash
cd terraform
terraform destroy
```

Run it from the same folder where you ran `apply`, because that is where the state file is. Afterwards, check in the EC2 console that both instances show `terminated`.

- Revoke the Docker Hub access token if you created one for this demo